"""Enumerated finite-law diagnostics for the bridge coefficient expression."""
from __future__ import annotations

from dataclasses import replace
import numpy as np
from .dgp import SimulationConfig, generate_minimal_archive
from .methods import AtlasConfig, compute_certificate, fit_causal_atlas
from .algorithm1 import _candidate_experiment
from .partial_identification import _weight_family
from .bridge_experiment import _build_bridge_library, BridgeExperimentConfig


def audit_set_function(values, estimate, budget):
    """All subset extensions, not just greedy-path samples. Undefined => no bound."""
    n = int(np.log2(len(values)))
    if not np.isfinite(values).all() or not np.isfinite(estimate).all():
        return dict(valid=False, reason='empty_intersection', gamma=None, monotone=False,
                    epsilon=None, optimum=None, selected_value=None, lower_bound=None,
                    bound_holds=None, vacuous=None, monotonicity_violations=None)
    violations, ratios, epsilon = 0, [], 0.0
    for s in range(1 << n):
        for j in range(n):
            if not s & (1 << j):
                u = s | (1 << j)
                delta = values[u]-values[s]
                violations += int(delta < -1e-9)
                epsilon = max(epsilon, abs((estimate[u]-estimate[s])-delta))
        remainder = ((1 << n)-1) ^ s
        u = remainder
        while u:
            gain = values[s | u] - values[s]
            if gain > 1e-9:
                marginal_sum = sum(values[s | (1 << j)] - values[s] for j in range(n) if u & (1 << j))
                ratios.append(marginal_sum / gain)
            u = (u-1) & remainder
    gamma = min(1.0, min(ratios)) if ratios else None
    selected = 0
    for _ in range(budget):
        j = max((j for j in range(n) if not selected & (1 << j)),
                key=lambda j: estimate[selected | (1 << j)]-estimate[selected])
        selected |= 1 << j
    optimum = max(values[s] for s in range(1 << n) if s.bit_count() <= budget)
    eligible = violations == 0 and gamma is not None and gamma > 0
    lower = (1-np.exp(-gamma))*optimum - 2*budget*epsilon/gamma if eligible else None
    return dict(valid=True, reason='eligible' if eligible else 'assumption_failed',
        gamma=gamma, monotone=violations == 0, monotonicity_violations=violations,
        epsilon=float(epsilon), optimum=float(optimum), selected_value=float(values[selected]),
        lower_bound=float(lower) if lower is not None else None,
        bound_holds=bool(values[selected]+1e-9 >= lower) if lower is not None else None,
        vacuous=bool(lower <= 0) if lower is not None else None)


def bridge_checks(repetitions=12, reference_draws=2048, planning_draws=128):
    records, sets, failures = [], [], []
    for scenario, shift, seed in (('moderate',.25,2026090621),('severe',.8,2026090622)):
        for rep, ss in enumerate(np.random.SeedSequence(seed).spawn(repetitions)):
            streams = ss.spawn(3)
            g = generate_minimal_archive(SimulationConfig(target_shift_fraction=shift), seed=int(streams[0].generate_state(1)[0]))
            library = _build_bridge_library(g.target, BridgeExperimentConfig(), np.random.default_rng(streams[1]))
            candidates = tuple(library[i] for i in (0,1,4,5,8,9))
            config = AtlasConfig()
            encoded = tuple(_candidate_experiment(c,g.target,0) for c in candidates)
            means = np.array([fit_causal_atlas(g.archive,c,config).raw_point_estimate for c in encoded])
            se = np.array([c.standard_error for c in candidates])
            # Independent planning/reference draws; common vectors across subsets.
            draws = np.random.default_rng(streams[2]).normal(means,se,(reference_draws+planning_draws,6))
            old_y = np.array([a.estimated_effect for a in g.archive])
            initial_labels, initial_weights = _weight_family(g.archive,g.target,config,max_singletons=4)
            fixed_allocation = len(initial_weights)+len(candidates)
            initial_radii = np.array([compute_certificate(g.archive,g.target,w,
                replace(config,zeta=config.zeta/fixed_allocation)).radius for w in initial_weights])
            initial_centers = np.array(initial_weights) @ old_y
            base_lo, base_hi = max(initial_centers-initial_radii), min(initial_centers+initial_radii)
            singleton_radii=[]
            all_archive = (*g.archive,*encoded)
            for j in range(6):
                w=np.zeros(len(all_archive)); w[len(g.archive)+j]=1
                singleton_radii.append(compute_certificate(all_archive,g.target,w,
                    replace(config,zeta=config.zeta/fixed_allocation)).radius)
            widths = {k:np.empty((64,len(draws))) for k in ('operational','retained_certificates')}
            for mask in range(64):
                chosen=[j for j in range(6) if mask & (1<<j)]
                augmented=(*g.archive,*(encoded[j] for j in chosen))
                _, weights=_weight_family(augmented,g.target,config,max_singletons=4)
                radii=np.array([compute_certificate(augmented,g.target,w,
                    replace(config,zeta=config.zeta/len(weights))).radius for w in weights])
                outcomes=np.column_stack((np.tile(old_y,(len(draws),1)),draws[:,chosen]))
                centers=outcomes @ np.array(weights).T
                widths['operational'][mask]=(centers+radii).min(1)-(centers-radii).max(1)
                lo,hi=np.full(len(draws),base_lo),np.full(len(draws),base_hi)
                for j in chosen:
                    lo=np.maximum(lo,draws[:,j]-singleton_radii[j]); hi=np.minimum(hi,draws[:,j]+singleton_radii[j])
                widths['retained_certificates'][mask]=hi-lo
            for family,width in widths.items():
                invalid=width<0
                failures.append(dict(scenario=scenario,replicate=rep,family=family,
                    empty_intersections=int(invalid.sum()),evaluations=int(width.size)))
                values=width[0,planning_draws:].mean()-width[:,planning_draws:].mean(1)
                est=width[0,:planning_draws].mean()-width[:,:planning_draws].mean(1)
                if invalid.any(): values[:]=np.nan; est[:]=np.nan
                for mask in range(64):
                    sets.append(dict(scenario=scenario,replicate=rep,family=family,mask=mask,
                        cardinality=mask.bit_count(),reference_value=float(values[mask]),planning_value=float(est[mask])))
                for budget in (1,2,3):
                    result=audit_set_function(values,est,budget)
                    records.append(dict(scenario=scenario,replicate=rep,family=family,budget=budget,
                        reference_draws=reference_draws,planning_draws=planning_draws,**result))
            print(f"Bridge {scenario} {rep+1}/{repetitions}",flush=True)
    return records,sets,failures
