import numpy as np
import pandas as pd
from f1.models.driver import Driver


def american_to_prob(odds):
    """Convert American odds (e.g. +150, -200) to implied probability."""
    if isinstance(odds, str):
        odds = int(odds)
    if odds > 0:
        return 100 / (odds + 100)
    else:
        return -odds / (-odds + 100)


def pct_calc(col, val, df, a=1, b=19):
    """Calculate Laplace-smoothed probability of col==val in df."""
    n = len(df)
    if n == 0:
        return (0 + a) / (0 + a + b)
    if isinstance(val, list):
        k = df[col].isin(val).sum()
    else:
        k = (df[col] == val).sum()
    return (k + a) / (n + a + b)


def clamp_prob(p, low=0.03, high=0.15):
    return max(low, min(high, p))


def exp_decay_weights(n, half_life=6):
    """Generate exponential decay weights for n observations."""
    idx = np.arange(n)
    w = 0.5 ** (idx / max(half_life, 1))
    w /= w.sum() if w.sum() else 1.0
    return w


def make_recency_weights(n: int, half_life_races: int = 6):
    """Exponential decay by race index (0 = most recent)."""
    if n <= 0:
        return []
    idx = np.arange(n)
    w = 0.5 ** (idx / max(half_life_races, 1))
    s = w.sum()
    return (w / s) if s else w


def weighted_rate_bool(series_bool, weights, prior_mean=None, prior_strength=0.0):
    """Weighted mean for a boolean array with optional Bayesian shrinkage."""
    series = np.asarray(series_bool, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = min(series.size, w.size)
    series = series[:m]
    w = w[:m]
    if m == 0 or w.sum() == 0:
        return float(prior_mean) if prior_mean is not None else 0.0
    p_hat = float((series * w).sum() / w.sum())
    if prior_strength and prior_mean is not None and prior_strength > 0:
        n_eff = float((w.sum() ** 2) / (w ** 2).sum())
        return float((prior_strength * prior_mean + n_eff * p_hat) / (prior_strength + n_eff))
    return p_hat


def weighted_avg(values, weights):
    v = np.asarray(values, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = min(v.size, w.size)
    if m == 0:
        return None
    v = v[:m]
    w = w[:m]
    mask = ~np.isnan(v)
    v = v[mask]
    w = w[mask]
    s = w.sum()
    return float((v * w).sum() / s) if s else None


def expected_finish_position(df, half_life=6):
    """
    Exponentially decaying weighted average of 'position' for FINISHED races only.
    Returns None if fewer than 10 finished races.
    """
    f = df[~df['dnf'].astype(bool)].copy()
    if 'start_date' in f.columns:
        f = f.sort_values('start_date', ascending=False)
    if len(f) <= 9:
        return None
    w = make_recency_weights(len(f), half_life_races=half_life)
    pos = pd.to_numeric(f['position'], errors='coerce')
    return weighted_avg(pos.values, w)


def dynamic_prior_strength_from_weights(weights, target_neff: float = 10.0,
                                        min_strength: float = 0.0, max_strength: float = 20.0) -> float:
    """Compute a prior strength that tops up the Kish effective sample size to target_neff."""
    w = np.asarray(weights, dtype=float)
    if w.size == 0 or w.sum() == 0:
        return float(target_neff)
    n_eff = float((w.sum() ** 2) / (w ** 2).sum())
    s0 = max(min_strength, target_neff - n_eff)
    return float(min(s0, max_strength))


def driver_odds(driver_number, team_name, df, *,
                win_half_life=6, pos_half_life=6,
                dnf_prior: float | None = None,
                win_prior: float | None = None,
                expected_finish_prior: float | None = None,
                target_neff: float = 10.0):
    """
    Compute driver odds with recency weighting.
    Falls back to priors when fewer than 10 races of history exist.
    """
    filtered_df = df[(df['driver_number'] == driver_number) & (df['team_name'] == team_name)].copy()
    if len(filtered_df) == 0:
        return Driver(full_name=None, driver_number=driver_number, team_name=team_name,
                      dnf_prob=0.07, win_prob=0.01)

    if 'start_date' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('start_date', ascending=False)

    driver = Driver(full_name=filtered_df['full_name'].iloc[0],
                    driver_number=driver_number, team_name=team_name)

    if len(filtered_df) > 9:
        driver.dnf_prob = clamp_prob(pct_calc('dnf', True, filtered_df))

        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        driver.win_prob = (weighted_rate_bool(win_bool, w, prior_mean=win_prior, prior_strength=0.0)
                          if win_prior is not None else weighted_rate_bool(win_bool, w))

        driver.expected_finish = expected_finish_position(filtered_df, half_life=pos_half_life)
    else:
        driver.dnf_prob = clamp_prob(float(dnf_prior)) if dnf_prior is not None else clamp_prob(pct_calc('dnf', True, filtered_df))

        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        if win_prior is not None:
            s0 = dynamic_prior_strength_from_weights(w, target_neff=target_neff)
            driver.win_prob = weighted_rate_bool(win_bool, w, prior_mean=float(win_prior), prior_strength=s0)
        else:
            driver.win_prob = weighted_rate_bool(win_bool, w)

        driver.expected_finish = float(expected_finish_prior) if expected_finish_prior is not None else expected_finish_position(filtered_df, half_life=pos_half_life)

    return driver
