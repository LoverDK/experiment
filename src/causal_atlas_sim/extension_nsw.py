"""Disjoint-unit randomized references and known-truth NSW-covariate checks."""
from __future__ import annotations

from dataclasses import replace
import numpy as np
from .nsw_experiment import (NSW_COVARIATES, NSW_SOURCE_SHA256, NswLocalContrast,
                            NswExperimentConfig, fit_nsw_method)
from .extension_baselines import archive_baselines, unit_t_learner


def read_data(path):
    import hashlib
    import pandas as pd
    if hashlib.sha256(path.read_bytes()).hexdigest() != NSW_SOURCE_SHA256:
        raise ValueError("NSW hash mismatch")
    frame = pd.read_stata(path)
    x = frame[list(NSW_COVARIATES)].to_numpy(float)
    scale = x.std(0)
    x = (x - x.mean(0)) / np.where(scale > 1e-8, scale, 1)
    return x, frame.treat.to_numpy(int), frame.re78.to_numpy(float) / 1000


def fixed_design(x, treatment):
    rng = np.random.default_rng(2026090601)
    source, reference = [], []
    for arm in (0, 1):
        indices = rng.permutation(np.flatnonzero(treatment == arm))
        cut = 2 * len(indices) // 3
        source.extend(indices[:cut]); reference.extend(indices[cut:])
    # Anchors use baseline covariates only. Skip the outermost 5% to reduce tiny arms.
    norm = np.linalg.norm(x, axis=1)
    eligible = np.flatnonzero(norm <= np.quantile(norm, .95))
    chosen = [int(eligible[np.argmin(norm[eligible])])]
    while len(chosen) < 30:
        distances = ((x[eligible, None] - x[chosen][None, :]) ** 2).sum(2).min(1)
        chosen.append(int(eligible[np.argmax(distances)]))
    return np.sort(source), np.sort(reference), np.array(chosen[:24]), np.array(chosen[24:])


def make_objects(x, treatment, y, pool, anchors):
    objects = []
    for j, anchor in enumerate(anchors):
        distance = ((x[pool] - x[anchor]) ** 2).sum(1)
        ids = np.asarray(pool)[np.argsort(distance, kind="stable")[:50]]
        a = treatment[ids]
        if min(a.sum(), len(a) - a.sum()) < 8:
            raise ValueError("arm_minimum")
        yy = y[ids]; context = x[ids].mean(0)
        effect = yy[a == 1].mean() - yy[a == 0].mean()
        se = np.sqrt(yy[a == 1].var(ddof=1)/a.sum() + yy[a == 0].var(ddof=1)/(len(a)-a.sum()))
        overlap = 4 * a.mean() * (1 - a.mean())
        radius = np.sqrt(((x[ids] - context) ** 2).sum(1).mean())
        objects.append(NswLocalContrast(str(j), int(anchor), tuple(map(int, ids)), context,
            context[:6], np.r_[context, overlap, radius], float(effect), float(se),
            float(overlap), float(radius), int(a.sum()), int(len(a)-a.sum())))
    return objects


def scale_objects(source, targets):
    for name in ("semantic_representation", "causal_representation"):
        matrix = np.vstack([getattr(s, name) for s in source])
        mean, scale = matrix.mean(0), matrix.std(0)
        scale = np.where(scale > 1e-8, scale, 1)
        source = [replace(s, **{name: (getattr(s, name)-mean)/scale}) for s in source]
        targets = [replace(s, **{name: (getattr(s, name)-mean)/scale}) for s in targets]
    return source, targets


def predictions(x, treatment, y, source_pool, sources, targets):
    sources, targets = scale_objects(sources, targets)
    target_matrix = np.vstack([s.causal_representation for s in targets])
    baselines, tuning = archive_baselines(np.vstack([s.causal_representation for s in sources]),
        [s.estimated_effect for s in sources], [s.standard_error for s in sources], target_matrix)
    target_units = np.concatenate([np.array(s.neighborhood_rows) for s in targets])
    unit_effect = unit_t_learner(x[source_pool], treatment[source_pool], y[source_pool], x[target_units])
    rows = []
    for j, target in enumerate(targets):
        # Prediction never receives reference outcome or standard error.
        blind = replace(target, estimated_effect=float("nan"), standard_error=float("nan"))
        for method in ("atlas", "atlas_no_rejection", "semantic_forced"):
            p = fit_nsw_method(method, sources, blind, NswExperimentConfig())
            rows.append(dict(method=method, target=j, estimate=p.predicted_effect,
                released=p.accepted, lower=p.interval_lower, upper=p.interval_upper,
                data_access="archive_summaries"))
        for method, pred in baselines.items():
            rows.append(dict(method=method, target=j, estimate=float(pred[j]), released=True,
                lower=None, upper=None, data_access="archive_summaries"))
        rows.append(dict(method="unit_ridge_t_learner", target=j,
            estimate=float(unit_effect[j*50:(j+1)*50].mean()), released=True,
            lower=None, upper=None, data_access="source_individuals"))
    return rows, tuning


def real_reference(x, t, y, design, bootstrap=200):
    source_pool, ref_pool, source_anchors, ref_anchors = design
    assert not set(source_pool) & set(ref_pool)
    rng = np.random.default_rng(2026090602)
    records, failures = [], []
    for b in range(bootstrap + 1):
        pools = []
        for pool in (source_pool, ref_pool):
            pools.append(np.concatenate([rng.choice(pool[t[pool] == arm], size=sum(t[pool] == arm), replace=True)
                for arm in (0, 1)]) if b else pool)
        try:
            sources = make_objects(x, t, y, pools[0], source_anchors)
            targets = make_objects(x, t, y, pools[1], ref_anchors)
            preds, _ = predictions(x, t, y, pools[0], sources, targets)
            for row in preds:
                ref = targets[row['target']]
                records.append(dict(bootstrap=b, **row, reference=ref.estimated_effect,
                    reference_se=ref.standard_error, gap=row['estimate']-ref.estimated_effect))
        except ValueError as error:
            if str(error) != 'arm_minimum': raise
            failures.append(dict(bootstrap=b, reason=str(error)))
        if b % 25 == 0: print(f"NSW real bootstrap {b}/{bootstrap}", flush=True)
    if any(r['bootstrap'] == 0 for r in failures): raise ValueError("Original design arm minima failed")
    return records, failures


def response_surface(x, key):
    if key == 'constant': tau = np.ones(len(x)) * 2
    elif key == 'smooth': tau = 2 + .8*np.tanh(x[:,0]) + 1.2*np.tanh(x[:,7])
    elif key == 'interaction': tau = 1 + 2*np.tanh(x[:,0]*x[:,7]) + .8*(x[:,5] > 0)
    else: raise ValueError(key)
    mu = 3 + .7*x[:,0] + 1.5*np.tanh(x[:,6]) + .5*x[:,1]**2
    return mu, tau


def semisynthetic(x, design, repetitions=100):
    source_pool, ref_pool, source_anchors, ref_anchors = design
    records, failures = [], []
    for surface, seed in zip(('constant','smooth','interaction'), (2026090611,2026090612,2026090613)):
        mu, tau = response_surface(x, surface)
        for rep, ss in enumerate(np.random.SeedSequence(seed).spawn(repetitions)):
            rng = np.random.default_rng(ss)
            t = rng.binomial(1, .5, len(x))
            y = mu + t*tau + rng.normal(0, 3, len(x))
            try:
                sources = make_objects(x,t,y,source_pool,source_anchors)
                targets = make_objects(x,t,y,ref_pool,ref_anchors)
                preds, _ = predictions(x,t,y,source_pool,sources,targets)
                for row in preds:
                    truth = float(tau[list(targets[row['target']].neighborhood_rows)].mean())
                    covered = row['lower'] <= truth <= row['upper'] if row['lower'] is not None else None
                    records.append(dict(surface=surface, replicate=rep, seed=int(ss.generate_state(1)[0]),
                        **row, truth=truth, absolute_error=abs(row['estimate']-truth), covered=covered))
            except ValueError as error:
                if str(error) != 'arm_minimum': raise
                failures.append(dict(surface=surface, replicate=rep, reason=str(error)))
            if rep % 25 == 0: print(f"NSW {surface} {rep}/{repetitions}", flush=True)
    return records, failures
