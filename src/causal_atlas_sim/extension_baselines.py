"""Archive-only comparators with source-only tuning and explicit data access."""
from __future__ import annotations

import numpy as np

RIDGES = (0.01, 0.1, 1.0, 10.0, 100.0)
BANDWIDTHS = (0.5, 1.0, 2.0)


def regression_predictions(x, y, target, *, kernel=False):
    """Select a smoother by source LOO error, without target outcomes."""
    x, y, target = np.asarray(x), np.asarray(y), np.atleast_2d(target)
    mean, scale = x.mean(0), x.std(0)
    scale = np.where(scale > 1e-8, scale, 1.0)
    x, target = (x - mean) / scale, (target - mean) / scale
    best = None
    for bandwidth in BANDWIDTHS if kernel else (1.0,):
        if kernel:
            dist = ((x[:, None] - x[None, :]) ** 2).sum(2)
            positive = dist[dist > 1e-10]
            base = np.median(positive) if len(positive) else 1.0
            matrix = np.exp(-dist / (2 * bandwidth ** 2 * base))
            cross = np.exp(-((target[:, None] - x[None, :]) ** 2).sum(2) / (2 * bandwidth ** 2 * base))
        else:
            matrix, cross = x @ x.T, target @ x.T
        # An unpenalized intercept. Centering the kernel includes it in H.
        n = len(y)
        center = np.eye(n) - np.ones((n, n)) / n
        centered = center @ matrix @ center
        eig, vec = np.linalg.eigh(centered)
        eig = np.maximum(eig, 0)
        cross_centered = (cross - matrix.mean(0)[None, :]) @ center
        for ridge in RIDGES:
            inverse = (vec / (eig + ridge)) @ vec.T
            smoother = centered @ inverse + np.ones((n, n)) / n
            residual = (y - smoother @ y) / np.maximum(1 - np.diag(smoother), 1e-8)
            score = float(np.mean(residual ** 2))
            if best is None or score < best[0]:
                prediction = y.mean() + cross_centered @ inverse @ (y - y.mean())
                best = (score, prediction, ridge, bandwidth)
    return best[1], {"ridge": best[2], "bandwidth_multiplier": best[3], "loo_mse": best[0]}


def archive_baselines(x, effects, ses, target):
    """Every method receives the same enriched source/target representation."""
    x, target = np.asarray(x), np.atleast_2d(target)
    y, variance = np.asarray(effects), np.maximum(np.asarray(ses) ** 2, 1e-10)
    weight = 1 / variance
    fixed = weight @ y / weight.sum()
    q = np.sum(weight * (y - fixed) ** 2)
    c = weight.sum() - np.sum(weight ** 2) / weight.sum()
    tau2 = max(0.0, (q - len(y) + 1) / c)
    random_weight = 1 / (variance + tau2)
    random_effect = random_weight @ y / random_weight.sum()
    nearest = np.argmin(((target[:, None] - x[None, :]) ** 2).sum(2), axis=1)
    ridge, ridge_meta = regression_predictions(x, y, target)
    kernel, kernel_meta = regression_predictions(x, y, target, kernel=True)
    return {
        "ivw_meta": np.full(len(target), fixed),
        "random_effects_meta": np.full(len(target), random_effect),
        "full_nearest": y[nearest],
        "ridge_meta_regression": ridge,
        "rbf_kernel_ridge": kernel,
    }, {"ridge": ridge_meta, "kernel": kernel_meta, "DL_tau2": tau2}


def unit_t_learner(x, treatment, y, target_x):
    """Ridge outcome regression in each arm; target outcomes are not arguments."""
    mu = []
    for arm in (0, 1):
        select = treatment == arm
        mu.append(regression_predictions(x[select], y[select], target_x)[0])
    return mu[1] - mu[0]
