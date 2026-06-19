import numpy as np


def get_competition_ranks(scores):
    """Return rank for each score; highest score gets rank 1."""
    indexed = list(enumerate(scores))
    sorted_indexed = sorted(indexed, key=lambda x: x[1], reverse=True)
    ranks = [0] * len(scores)
    for rank, (original_index, _) in enumerate(sorted_indexed):
        ranks[original_index] = rank + 1
    return ranks


def pl_theta_from_mix(p_win, exp_finish=None, *, mix=0.15, beta=1.0, tau=1.0, eps=1e-12):
    """
    Build Plackett-Luce logits from a mixture of win probability and expected finish position.
    """
    p = np.asarray(p_win, dtype=float)
    if not np.isfinite(p).any() or p.sum() <= 0:
        p = np.ones_like(p) / len(p)
    else:
        p = p / p.sum()

    if exp_finish is None:
        t = np.ones_like(p) / len(p)
    else:
        ef = np.asarray(exp_finish, dtype=float)
        inv = np.zeros_like(ef, dtype=float)
        mask = np.isfinite(ef) & (ef > 0)
        inv[mask] = (1.0 / ef[mask]) ** beta
        if inv.sum() <= 0:
            t = np.ones_like(p) / len(p)
        else:
            t = inv / inv.sum()

    w = (1.0 - mix) * p + mix * t
    w = np.clip(w, eps, None)
    w = w / w.sum()
    return np.log(w) / max(tau, 1e-6)


def monte_carlo(drivers, n=1000, scale=0.9, seed=None):
    """
    Simulate n F1 races using Plackett-Luce with Gumbel noise.
    Returns (theta_score_list, position_list).
    """
    rng = np.random.default_rng(seed)
    base_theta = np.asarray([d.theta for d in drivers], dtype=float)
    dnf_probs = np.asarray([d.dnf_prob for d in drivers], dtype=float)

    theta_scores = []
    positions = []
    for _ in range(n):
        dnf = rng.uniform(0.0, 1.0, size=dnf_probs.size) < dnf_probs
        noise = rng.gumbel(loc=0.0, scale=scale, size=base_theta.shape[0])
        theta_temp = np.where(dnf, -100.0, base_theta + noise)
        order = np.where(dnf, -100, get_competition_ranks(theta_temp))
        theta_scores.append(theta_temp.copy())
        positions.append(order.copy())

    return theta_scores, positions


def points_from_finishes(positions, point_values, dnf_value):
    """Convert an array of finish positions to fantasy points."""
    pv = np.asarray(point_values, dtype=float)
    pos = np.asarray(positions)
    points = np.zeros_like(pos, dtype=float)
    dnf_mask = (pos == -100)
    points[dnf_mask] = dnf_value
    valid = (~dnf_mask) & (pos >= 1) & (pos <= len(pv))
    if np.any(valid):
        points[valid] = pv[pos[valid].astype(int) - 1]
    return points


def price_from_stats(mean, std, risk_discount_factor=0.1, K=50):
    """Convert simulated mean and std of points into a driver price."""
    edge = float(np.maximum(mean - (risk_discount_factor * std), mean * 0.1))
    return K * edge
