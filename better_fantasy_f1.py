<<<<<<< HEAD
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import requests
import datetime
import time
from dataclasses import dataclass

@dataclass
class TeamPriors:
    dnf_prior: float               # per-race DNF prob
    win_prior: float               # per-race win prob
    expected_finish_prior: float   # lower = better (e.g., 2.4 means ~P2–P3 on avg)

CAR_PRIORS = {
    # season -> canonical team name -> priors
    2025: {
        "Red Bull Racing":  TeamPriors(dnf_prior=0.07, win_prior=0.01, expected_finish_prior=8.0),
        "McLaren":          TeamPriors(dnf_prior=0.06, win_prior=0.10, expected_finish_prior=4.0),
        "Ferrari":          TeamPriors(dnf_prior=0.08, win_prior=0.01, expected_finish_prior=7.0),
        "Mercedes":         TeamPriors(dnf_prior=0.08, win_prior=0.07, expected_finish_prior=7.0),
        "Aston Martin":     TeamPriors(dnf_prior=0.11, win_prior=0.02, expected_finish_prior=11.0),
        "Alpine":  TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Haas F1 Team":          TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Kick Sauber":          TeamPriors(dnf_prior=0.13, win_prior=0.00, expected_finish_prior=12.0),
        "Williams":         TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=10.0),
        "Racing Bulls":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=9.0),
        "default":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=8.5),
        # ... fill out the grid
    },
    # 2024: {...}  # you can keep per-season tables if you want
}

team_aliases = {
    "RB": "Racing Bulls",
    "AlphaTauri": "Racing Bulls"
    }


"""
Need to calculate the share price for each driver based on historical data.
Should be some sort of function that allows me to even out the points gained
by each driver.
"""

finish_points = [2.5, 2.3, 2.1, 1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0]
dnf = -10

# total points = (finish_points * num_shares) + dnf
class Driver:
    """
    A class to represent a race car driver.
    """

    def __init__(self, full_name, driver_number, team_name, win_prob=None, dnf_prob=None, expected_finish=None, theta=None, sim_results=None):
        """
        Initializes a new Driver instance with the given attributes.

        Args:
            name (str): The driver's full name.
            team_name (str): The name of the driver's racing team.
            win_prob (float): The fractional odds of the driver winning.
            dnf_odds (float): The fractional odds of the driver not finishing (DNF).
            expected_finish (int): The driver's average finishing position.
        """
        self.full_name = full_name
        self.driver_number = driver_number
        self.team_name = team_name
        self.win_prob = win_prob
        self.dnf_prob = dnf_prob
        self.expected_finish = expected_finish
        self.theta = theta
        self.sim_results = sim_results

    def __str__(self):
        """
        Provides a user-friendly string representation of the Driver object.
        """
        return f"Driver: {self.name} | Team: {self.team_name} | Avg Finish: {self.expected_finish}"

    def get_info(self):
        """
        Returns a dictionary of the driver's key statistics.
        """
        return {
            "full_name": self.full_name,
            "driver_number": self.driver_number,
            "team_name": self.team_name,
            "win_prob": self.win_prob,
            "dnf_prop": self.dnf_prob,
            "expected_finish": self.expected_finish,
            "theta": self.theta,
            "sim_results": self.sim_results
        }

# Convert driver win odds to win probability
def american_to_prob(odds):
    """
    Convert American odds (e.g. +150, -200) to implied probability.
    Input: int or string (like "+150" or "-200")
    Returns: probability in [0,1]
    """
    # ensure int
    if isinstance(odds, str):
        odds = int(odds)

    if odds > 0:   # positive odds, e.g. +150
        prob = 100 / (odds + 100)
    else:          # negative odds, e.g. -200
        prob = -odds / (-odds + 100)

    return prob


BASE_URL = "https://api.openf1.org/v1"

def fetch_openf1(endpoint: str, **params):
    """
    Fetch data from the OpenF1 API.
    
    Args:
        endpoint (str): e.g. "sessions", "drivers", "laps", "session_result"
        **params: query parameters (like year=2023)
    
    Returns:
        Parsed JSON (Python list/dict)
    """
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_n_last_sessions(years, n=40):
    sessions = []
    for year in years:
        sessions.extend(fetch_openf1('sessions', year=year, session_name="Race"))
    df = pd.DataFrame(sessions)
    sorted_df = df.sort_values(by='date_start', ascending=False)
    return sorted_df[:n]

def get_n_last_results(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('session_result', session_key = session))
        time.sleep(.3)
    return pd.DataFrame(results)

def get_n_last_drivers(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('drivers', session_key = session))
        time.sleep(.3)
    return pd.DataFrame(results)

def get_unique_combinations(df, column1, column2):
    """
    Returns a list of unique combinations of values from two specified columns.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column1 (str): The name of the first column.
        column2 (str): The name of the second column.

    Returns:
        list: A list of tuples, where each tuple is a unique combination.
    """
    # Select the two columns and drop duplicate rows
    unique_pairs_df = df[[column1, column2]].drop_duplicates()

    # Convert the resulting DataFrame to a list of tuples for easy iteration
    # index=False prevents the DataFrame index from being included in the tuples
    return list(unique_pairs_df.itertuples(index=False))

def pct_calc(col, val, df, a=1, b=19):
    """
    Calculate Laplace-smoothed probability of col==val in df.
    Args:
        col (str): column name
        val: value to check (can be list)
        df (pd.DataFrame)
        a, b: Laplace smoothing hyperparameters
    """
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
    """
    Generate exponential decay weights for n observations.
    half_life: number of races after which weight halves
    """
    idx = np.arange(n)
    w = 0.5 ** (idx / max(half_life, 1))
    w /= w.sum() if w.sum() else 1.0
    return w


def make_recency_weights(n: int, half_life_races: int = 6):
    """Exponential decay by race index (0 = most recent)."""
    if n <= 0:
        return []
    idx = np.arange(n)  # 0..n-1
    w = 0.5 ** (idx / max(half_life_races, 1))
    s = w.sum()
    return (w / s) if s else w


def weighted_rate_bool(series_bool, weights, prior_mean=None, prior_strength=0.0):
    """Weighted mean for a boolean array with optional Bayesian shrinkage.
    - weights can be any positive weights (need not sum to 1)
    - if prior_strength>0 and prior_mean is provided, we shrink toward prior_mean
      using Kish effective sample size for the weights.
    """
    series = np.asarray(series_bool, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = min(series.size, w.size)
    series = series[:m]
    w = w[:m]
    if m == 0 or w.sum() == 0:
        return float(prior_mean) if prior_mean is not None else 0.0
    # raw weighted mean
    p_hat = float((series * w).sum() / w.sum())
    if prior_strength and prior_mean is not None and prior_strength > 0:
        # Kish effective sample size
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
    Assumes df is for a single driver.
    Returns None if fewer than 10 finished races.
    """
    f = df[~df['dnf'].astype(bool)].copy()
    if 'start_date' in f.columns:
        f = f.sort_values('start_date', ascending=False)

    if len(f) <= 9:
        return None

    w = make_recency_weights(len(f), half_life_races=half_life)
    # Guard against 'position' sometimes being strings
    pos = pd.to_numeric(f['position'], errors='coerce')
    return weighted_avg(pos.values, w)


def dynamic_prior_strength_from_weights(weights, target_neff: float = 10.0,
                                        min_strength: float = 0.0, max_strength: float = 20.0) -> float:
    """Compute a prior strength that tops up the Kish effective sample size to target_neff.
    If weights are very concentrated (small n_eff), prior gets stronger; otherwise it fades out.
    """
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
    If sample size < 10 rows for this driver/team, use priors as specified:
      - dnf_prior: used as-is (then clamped to [0.03, 0.15])
      - expected_finish_prior: used as-is
      - win_prior: combined with data via Bayesian shrinkage with dynamic prior strength
        (prior_strength tops up Kish effective sample size to `target_neff`).
    """
    filtered_df = df[(df['driver_number'] == driver_number) & (df['team_name'] == team_name)].copy()
    if len(filtered_df) == 0:
        # fall back to global priors if no history
        return Driver(full_name=None, driver_number=driver_number, team_name=team_name,
                      dnf_prob=0.07, win_prob=0.01)

    # Ensure most-recent-first order for weighting
    if 'start_date' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('start_date', ascending=False)

    driver = Driver(full_name=filtered_df['full_name'].iloc[0], driver_number=driver_number, team_name=team_name)

    if len(filtered_df) > 9:
        # DNF: Laplace-smoothed fraction + clamp
        driver.dnf_prob = clamp_prob(pct_calc('dnf', True, filtered_df))

        # Win: exponential recency weighting over all available races
        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        # For >=10 we normally avoid shrinkage; pass prior_strength=0.
        driver.win_prob = weighted_rate_bool(win_bool, w, prior_mean=win_prior, prior_strength=0.0) if win_prior is not None else weighted_rate_bool(win_bool, w)

        # Expected finish position (exclude DNFs). Only if >=10 finished races
        driver.expected_finish = expected_finish_position(filtered_df, half_life=pos_half_life)
    else:
        # --- Use priors for small samples (<10) ---
        # DNF: use prior as-is (then clamp to the invariant bounds)
        if dnf_prior is not None:
            driver.dnf_prob = clamp_prob(float(dnf_prior))
        else:
            # Fallback: smoothed in-sample estimate, still clamped
            driver.dnf_prob = clamp_prob(pct_calc('dnf', True, filtered_df))

        # Win: Bayesian smoothing of limited data toward prior
        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        if win_prior is not None:
            s0 = dynamic_prior_strength_from_weights(w, target_neff=target_neff)
            driver.win_prob = weighted_rate_bool(win_bool, w, prior_mean=float(win_prior), prior_strength=s0)
        else:
            # If no prior provided, just use the small-sample weighted mean
            driver.win_prob = weighted_rate_bool(win_bool, w)

        # Expected finish: use prior as-is when provided
        driver.expected_finish = float(expected_finish_prior) if expected_finish_prior is not None else expected_finish_position(filtered_df, half_life=pos_half_life)

    return driver


def pl_theta_from_mix(p_win, exp_finish=None, *, mix=0.15, beta=1.0, tau=1.0, eps=1e-12):
    """
    Build PL logits theta from a mixture of win priors and position priors.
    p_win: array-like (can include zeros); we'll normalize
    exp_finish: array-like expected finish among finishers (lower=better); can be None/NaN
    mix: fraction of mass from position prior (0..1)
    beta: shape for position prior, t_i ∝ (1/E[pos])**beta
    tau: temperature for PL (1 baseline; >1 more random)
    """
    p = np.asarray(p_win, dtype=float)
    # normalize win priors (fallback to uniform if all zero)
    if not np.isfinite(p).any() or p.sum() <= 0:
        p = np.ones_like(p) / len(p)
    else:
        p = p / p.sum()

    # position-based tail
    if exp_finish is None:
        t = np.ones_like(p) / len(p)
    else:
        ef = np.asarray(exp_finish, dtype=float)
        inv = np.zeros_like(ef, dtype=float)
        mask = np.isfinite(ef) & (ef > 0)
        # mask is a boolean array. It is used here to basically filter out any bad values from the inv array
        inv[mask] = (1.0 / ef[mask]) ** beta
        if inv.sum() <= 0:
            t = np.ones_like(p) / len(p)
        else:
            t = inv / inv.sum()

    # mix
    w = (1.0 - mix) * p + mix * t
    w = np.clip(w, eps, None)
    w = w / w.sum()

    return np.log(w) / max(tau, 1e-6)

def get_competition_ranks(scores):
    """
    Returns an array of ranks for each score, with the highest score ranked first (rank 0).

    Args:
        scores (list): A list of integer scores.

    Returns:
        list: A list of ranks corresponding to the original scores.
    """
    # 1. Enumerate the scores to keep track of original indices
    indexed_scores = list(enumerate(scores))
    
    # 2. Sort the list of tuples by score in descending order
    #    The key=lambda x: x[1] specifies that the sorting should be based on the score (the second item in the tuple).
    #    The reverse=True flag ensures a descending sort.
    sorted_indexed_scores = sorted(indexed_scores, key=lambda x: x[1], reverse=True)
    
    # 3. Create a result array to store the ranks
    result_ranks = [0] * len(scores)
    
    # 4. Assign ranks based on the sorted order and place them in the correct position
    for rank, (original_index, _) in enumerate(sorted_indexed_scores):
        result_ranks[original_index] = rank + 1
        
    return result_ranks

def monte_carlo(drivers, n=1000, scale=0.9, seed=None):
    """
    Simulate n F1 races.
    - drivers: iterable of objects with .theta (float) and .dnf_prob (0..1)
    - rng: optional numpy.random.Generator. If None, a new one is created.
    - seed: optional int to seed the RNG (ignored if rng is provided)
    - scale: Gumbel noise scale
    Returns (theta_score_list, position_list)
    """
    rng = np.random.default_rng(seed)

    theta_score = []
    position = []

    base_theta = np.asarray([d.theta for d in drivers], dtype=float)
    dnf_probs = np.asarray([d.dnf_prob for d in drivers], dtype=float)

    for _ in range(n):
        # Per-race DNF draw (True means the driver did not finish)
        dnf = rng.uniform(0.0, 1.0, size=dnf_probs.size) < dnf_probs

        # Fresh Gumbel noise EACH race
        noise = rng.gumbel(loc=0.0, scale=scale, size=base_theta.shape[0])
        theta_temp = base_theta + noise

        # Push DNFs to a very low score so they rank last
        theta_temp = np.where(dnf, -100.0, theta_temp)

        order = get_competition_ranks(theta_temp)
        order = np.where(dnf, -100, order)

        # Append COPIES to avoid any accidental aliasing/view issues
        theta_score.append(theta_temp.copy())
        position.append(order.copy())

    return theta_score, position
        
        



if __name__ == "__main__":
    
    current_date = datetime.date.today()
    current_year = current_date.year
    
    historical_sessions = get_n_last_sessions([current_year, current_year-1, current_year-2])   
    historical_results = get_n_last_results(historical_sessions['session_key'])
    historical_drivers = get_n_last_drivers(historical_sessions['session_key'])

    historical_results = historical_results.merge( historical_drivers, on=['session_key', 'driver_number'])
    historical_results = historical_results.replace(team_aliases)
    
    driver_list = []
    for driver_number, team_name in get_unique_combinations(historical_results, 'driver_number', 'team_name'):        
        try:
            driver_list.append(driver_odds(driver_number, team_name, historical_results,
                                           dnf_prior = CAR_PRIORS[2025][team_name].dnf_prior,
                                           win_prior = CAR_PRIORS[2025][team_name].win_prior,
                                           expected_finish_prior = CAR_PRIORS[2025][team_name].expected_finish_prior))
        except KeyError:
            driver_list.append(driver_odds(driver_number, team_name, historical_results,
                                           dnf_prior = CAR_PRIORS[2025]['default'].dnf_prior,
                                           win_prior = CAR_PRIORS[2025]['default'].win_prior,
                                           expected_finish_prior = CAR_PRIORS[2025]['default'].expected_finish_prior))
    
    # Get the list of current drivers (current logic just grabs the 20 who raced last. Need to fix)
    current_drivers = driver_list[:20]
    
    # Grab win probabilities and expected finish numbers to calculate theta for each driver
    # theta will be used for Plackett-Luce model for ranking drivers
    p_win = [d.win_prob for d in current_drivers]
    exp_finish = [d.expected_finish for d in current_drivers]
    theta = pl_theta_from_mix(p_win, exp_finish)
    for i, driver in enumerate(current_drivers):
        driver.theta = theta[i]
        
    race_matrix, win_matrix = monte_carlo(current_drivers, 1000)
    
    for i, driver in enumerate(current_drivers):
        driver.sim_results = np.array([w[i] for w in win_matrix])
        
    

=======
# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import numpy as np
import requests
import datetime
import time
from dataclasses import dataclass

@dataclass
class TeamPriors:
    dnf_prior: float               # per-race DNF prob
    win_prior: float               # per-race win prob
    expected_finish_prior: float   # lower = better (e.g., 2.4 means ~P2–P3 on avg)

CAR_PRIORS = {
    # season -> canonical team name -> priors
    2025: {
        "Red Bull Racing":  TeamPriors(dnf_prior=0.07, win_prior=0.01, expected_finish_prior=8.0),
        "McLaren":          TeamPriors(dnf_prior=0.06, win_prior=0.10, expected_finish_prior=4.0),
        "Ferrari":          TeamPriors(dnf_prior=0.08, win_prior=0.01, expected_finish_prior=7.0),
        "Mercedes":         TeamPriors(dnf_prior=0.08, win_prior=0.07, expected_finish_prior=7.0),
        "Aston Martin":     TeamPriors(dnf_prior=0.11, win_prior=0.02, expected_finish_prior=11.0),
        "Alpine":  TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Haas F1 Team":          TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Kick Sauber":          TeamPriors(dnf_prior=0.13, win_prior=0.00, expected_finish_prior=12.0),
        "Williams":         TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=10.0),
        "Racing Bulls":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=9.0),
        "default":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=8.5),
        # ... fill out the grid
    },
    # 2024: {...}  # you can keep per-season tables if you want
}

team_aliases = {
    "RB": "Racing Bulls",
    "AlphaTauri": "Racing Bulls"
    }


"""
Need to calculate the share price for each driver based on historical data.
Should be some sort of function that allows me to even out the points gained
by each driver.
"""

finish_points = [2.5, 2.3, 2.1, 1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0]
dnf = -10

# total points = (finish_points * num_shares) + dnf
class Driver:
    """
    A class to represent a race car driver.
    """

    def __init__(self, full_name, driver_number, team_name, win_prob=None, dnf_prob=None, expected_finish=None, theta=None, sim_results=None):
        """
        Initializes a new Driver instance with the given attributes.

        Args:
            name (str): The driver's full name.
            team_name (str): The name of the driver's racing team.
            win_prob (float): The fractional odds of the driver winning.
            dnf_odds (float): The fractional odds of the driver not finishing (DNF).
            expected_finish (int): The driver's average finishing position.
        """
        self.full_name = full_name
        self.driver_number = driver_number
        self.team_name = team_name
        self.win_prob = win_prob
        self.dnf_prob = dnf_prob
        self.expected_finish = expected_finish
        self.theta = theta
        self.sim_results = sim_results

    def __str__(self):
        """
        Provides a user-friendly string representation of the Driver object.
        """
        return f"Driver: {self.name} | Team: {self.team_name} | Avg Finish: {self.expected_finish}"

    def get_info(self):
        """
        Returns a dictionary of the driver's key statistics.
        """
        return {
            "full_name": self.full_name,
            "driver_number": self.driver_number,
            "team_name": self.team_name,
            "win_prob": self.win_prob,
            "dnf_prop": self.dnf_prob,
            "expected_finish": self.expected_finish,
            "theta": self.theta,
            "sim_results": self.sim_results
        }

# Convert driver win odds to win probability
def american_to_prob(odds):
    """
    Convert American odds (e.g. +150, -200) to implied probability.
    Input: int or string (like "+150" or "-200")
    Returns: probability in [0,1]
    """
    # ensure int
    if isinstance(odds, str):
        odds = int(odds)

    if odds > 0:   # positive odds, e.g. +150
        prob = 100 / (odds + 100)
    else:          # negative odds, e.g. -200
        prob = -odds / (-odds + 100)

    return prob


BASE_URL = "https://api.openf1.org/v1"

def fetch_openf1(endpoint: str, **params):
    """
    Fetch data from the OpenF1 API.
    
    Args:
        endpoint (str): e.g. "sessions", "drivers", "laps", "session_result"
        **params: query parameters (like year=2023)
    
    Returns:
        Parsed JSON (Python list/dict)
    """
    url = f"{BASE_URL}/{endpoint}"
    resp = requests.get(url, params=params, timeout=10)
    resp.raise_for_status()
    return resp.json()

def get_n_last_sessions(years, n=40):
    sessions = []
    for year in years:
        sessions.extend(fetch_openf1('sessions', year=year, session_name="Race"))
    df = pd.DataFrame(sessions)
    sorted_df = df.sort_values(by='date_start', ascending=False)
    return sorted_df[:n]

def get_n_last_results(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('session_result', session_key = session))
        time.sleep(.3)
    return pd.DataFrame(results)

def get_n_last_drivers(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('drivers', session_key = session))
        time.sleep(.3)
    return pd.DataFrame(results)

def get_unique_combinations(df, column1, column2):
    """
    Returns a list of unique combinations of values from two specified columns.

    Args:
        df (pd.DataFrame): The input DataFrame.
        column1 (str): The name of the first column.
        column2 (str): The name of the second column.

    Returns:
        list: A list of tuples, where each tuple is a unique combination.
    """
    # Select the two columns and drop duplicate rows
    unique_pairs_df = df[[column1, column2]].drop_duplicates()

    # Convert the resulting DataFrame to a list of tuples for easy iteration
    # index=False prevents the DataFrame index from being included in the tuples
    return list(unique_pairs_df.itertuples(index=False))

def pct_calc(col, val, df, a=1, b=19):
    """
    Calculate Laplace-smoothed probability of col==val in df.
    Args:
        col (str): column name
        val: value to check (can be list)
        df (pd.DataFrame)
        a, b: Laplace smoothing hyperparameters
    """
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
    """
    Generate exponential decay weights for n observations.
    half_life: number of races after which weight halves
    """
    idx = np.arange(n)
    w = 0.5 ** (idx / max(half_life, 1))
    w /= w.sum() if w.sum() else 1.0
    return w


def make_recency_weights(n: int, half_life_races: int = 6):
    """Exponential decay by race index (0 = most recent)."""
    if n <= 0:
        return []
    idx = np.arange(n)  # 0..n-1
    w = 0.5 ** (idx / max(half_life_races, 1))
    s = w.sum()
    return (w / s) if s else w


def weighted_rate_bool(series_bool, weights, prior_mean=None, prior_strength=0.0):
    """Weighted mean for a boolean array with optional Bayesian shrinkage.
    - weights can be any positive weights (need not sum to 1)
    - if prior_strength>0 and prior_mean is provided, we shrink toward prior_mean
      using Kish effective sample size for the weights.
    """
    series = np.asarray(series_bool, dtype=float)
    w = np.asarray(weights, dtype=float)
    m = min(series.size, w.size)
    series = series[:m]
    w = w[:m]
    if m == 0 or w.sum() == 0:
        return float(prior_mean) if prior_mean is not None else 0.0
    # raw weighted mean
    p_hat = float((series * w).sum() / w.sum())
    if prior_strength and prior_mean is not None and prior_strength > 0:
        # Kish effective sample size
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
    Assumes df is for a single driver.
    Returns None if fewer than 10 finished races.
    """
    f = df[~df['dnf'].astype(bool)].copy()
    if 'start_date' in f.columns:
        f = f.sort_values('start_date', ascending=False)

    if len(f) <= 9:
        return None

    w = make_recency_weights(len(f), half_life_races=half_life)
    # Guard against 'position' sometimes being strings
    pos = pd.to_numeric(f['position'], errors='coerce')
    return weighted_avg(pos.values, w)


def dynamic_prior_strength_from_weights(weights, target_neff: float = 10.0,
                                        min_strength: float = 0.0, max_strength: float = 20.0) -> float:
    """Compute a prior strength that tops up the Kish effective sample size to target_neff.
    If weights are very concentrated (small n_eff), prior gets stronger; otherwise it fades out.
    """
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
    If sample size < 10 rows for this driver/team, use priors as specified:
      - dnf_prior: used as-is (then clamped to [0.03, 0.15])
      - expected_finish_prior: used as-is
      - win_prior: combined with data via Bayesian shrinkage with dynamic prior strength
        (prior_strength tops up Kish effective sample size to `target_neff`).
    """
    filtered_df = df[(df['driver_number'] == driver_number) & (df['team_name'] == team_name)].copy()
    if len(filtered_df) == 0:
        # fall back to global priors if no history
        return Driver(full_name=None, driver_number=driver_number, team_name=team_name,
                      dnf_prob=0.07, win_prob=0.01)

    # Ensure most-recent-first order for weighting
    if 'start_date' in filtered_df.columns:
        filtered_df = filtered_df.sort_values('start_date', ascending=False)

    driver = Driver(full_name=filtered_df['full_name'].iloc[0], driver_number=driver_number, team_name=team_name)

    if len(filtered_df) > 9:
        # DNF: Laplace-smoothed fraction + clamp
        driver.dnf_prob = clamp_prob(pct_calc('dnf', True, filtered_df))

        # Win: exponential recency weighting over all available races
        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        # For >=10 we normally avoid shrinkage; pass prior_strength=0.
        driver.win_prob = weighted_rate_bool(win_bool, w, prior_mean=win_prior, prior_strength=0.0) if win_prior is not None else weighted_rate_bool(win_bool, w)

        # Expected finish position (exclude DNFs). Only if >=10 finished races
        driver.expected_finish = expected_finish_position(filtered_df, half_life=pos_half_life)
    else:
        # --- Use priors for small samples (<10) ---
        # DNF: use prior as-is (then clamp to the invariant bounds)
        if dnf_prior is not None:
            driver.dnf_prob = clamp_prob(float(dnf_prior))
        else:
            # Fallback: smoothed in-sample estimate, still clamped
            driver.dnf_prob = clamp_prob(pct_calc('dnf', True, filtered_df))

        # Win: Bayesian smoothing of limited data toward prior
        w = make_recency_weights(len(filtered_df), half_life_races=win_half_life)
        win_bool = (filtered_df['position'] == 1).values
        if win_prior is not None:
            s0 = dynamic_prior_strength_from_weights(w, target_neff=target_neff)
            driver.win_prob = weighted_rate_bool(win_bool, w, prior_mean=float(win_prior), prior_strength=s0)
        else:
            # If no prior provided, just use the small-sample weighted mean
            driver.win_prob = weighted_rate_bool(win_bool, w)

        # Expected finish: use prior as-is when provided
        driver.expected_finish = float(expected_finish_prior) if expected_finish_prior is not None else expected_finish_position(filtered_df, half_life=pos_half_life)

    return driver


def pl_theta_from_mix(p_win, exp_finish=None, *, mix=0.15, beta=1.0, tau=1.0, eps=1e-12):
    """
    Build PL logits theta from a mixture of win priors and position priors.
    p_win: array-like (can include zeros); we'll normalize
    exp_finish: array-like expected finish among finishers (lower=better); can be None/NaN
    mix: fraction of mass from position prior (0..1)
    beta: shape for position prior, t_i ∝ (1/E[pos])**beta
    tau: temperature for PL (1 baseline; >1 more random)
    """
    p = np.asarray(p_win, dtype=float)
    # normalize win priors (fallback to uniform if all zero)
    if not np.isfinite(p).any() or p.sum() <= 0:
        p = np.ones_like(p) / len(p)
    else:
        p = p / p.sum()

    # position-based tail
    if exp_finish is None:
        t = np.ones_like(p) / len(p)
    else:
        ef = np.asarray(exp_finish, dtype=float)
        inv = np.zeros_like(ef, dtype=float)
        mask = np.isfinite(ef) & (ef > 0)
        # mask is a boolean array. It is used here to basically filter out any bad values from the inv array
        inv[mask] = (1.0 / ef[mask]) ** beta
        if inv.sum() <= 0:
            t = np.ones_like(p) / len(p)
        else:
            t = inv / inv.sum()

    # mix
    w = (1.0 - mix) * p + mix * t
    w = np.clip(w, eps, None)
    w = w / w.sum()

    return np.log(w) / max(tau, 1e-6)

def get_competition_ranks(scores):
    """
    Returns an array of ranks for each score, with the highest score ranked first (rank 0).

    Args:
        scores (list): A list of integer scores.

    Returns:
        list: A list of ranks corresponding to the original scores.
    """
    # 1. Enumerate the scores to keep track of original indices
    indexed_scores = list(enumerate(scores))
    
    # 2. Sort the list of tuples by score in descending order
    #    The key=lambda x: x[1] specifies that the sorting should be based on the score (the second item in the tuple).
    #    The reverse=True flag ensures a descending sort.
    sorted_indexed_scores = sorted(indexed_scores, key=lambda x: x[1], reverse=True)
    
    # 3. Create a result array to store the ranks
    result_ranks = [0] * len(scores)
    
    # 4. Assign ranks based on the sorted order and place them in the correct position
    for rank, (original_index, _) in enumerate(sorted_indexed_scores):
        result_ranks[original_index] = rank + 1
        
    return result_ranks

def monte_carlo(drivers, n=1000, scale=0.9, seed=None):
    """
    Simulate n F1 races.
    - drivers: iterable of objects with .theta (float) and .dnf_prob (0..1)
    - rng: optional numpy.random.Generator. If None, a new one is created.
    - seed: optional int to seed the RNG (ignored if rng is provided)
    - scale: Gumbel noise scale
    Returns (theta_score_list, position_list)
    """
    rng = np.random.default_rng(seed)

    theta_score = []
    position = []

    base_theta = np.asarray([d.theta for d in drivers], dtype=float)
    dnf_probs = np.asarray([d.dnf_prob for d in drivers], dtype=float)

    for _ in range(n):
        # Per-race DNF draw (True means the driver did not finish)
        dnf = rng.uniform(0.0, 1.0, size=dnf_probs.size) < dnf_probs

        # Fresh Gumbel noise EACH race
        noise = rng.gumbel(loc=0.0, scale=scale, size=base_theta.shape[0])
        theta_temp = base_theta + noise

        # Push DNFs to a very low score so they rank last
        theta_temp = np.where(dnf, -100.0, theta_temp)

        order = get_competition_ranks(theta_temp)
        order = np.where(dnf, -100, order)

        # Append COPIES to avoid any accidental aliasing/view issues
        theta_score.append(theta_temp.copy())
        position.append(order.copy())

    return theta_score, position
        
        



if __name__ == "__main__":
    
    current_date = datetime.date.today()
    current_year = current_date.year
    
    historical_sessions = get_n_last_sessions([current_year, current_year-1, current_year-2])   
    historical_results = get_n_last_results(historical_sessions['session_key'])
    historical_drivers = get_n_last_drivers(historical_sessions['session_key'])

    historical_results = historical_results.merge( historical_drivers, on=['session_key', 'driver_number'])
    historical_results = historical_results.replace(team_aliases)
    
    driver_list = []
    for driver_number, team_name in get_unique_combinations(historical_results, 'driver_number', 'team_name'):        
        try:
            driver_list.append(driver_odds(driver_number, team_name, historical_results,
                                           dnf_prior = CAR_PRIORS[2025][team_name].dnf_prior,
                                           win_prior = CAR_PRIORS[2025][team_name].win_prior,
                                           expected_finish_prior = CAR_PRIORS[2025][team_name].expected_finish_prior))
        except KeyError:
            driver_list.append(driver_odds(driver_number, team_name, historical_results,
                                           dnf_prior = CAR_PRIORS[2025]['default'].dnf_prior,
                                           win_prior = CAR_PRIORS[2025]['default'].win_prior,
                                           expected_finish_prior = CAR_PRIORS[2025]['default'].expected_finish_prior))
    
    # Get the list of current drivers (current logic just grabs the 20 who raced last. Need to fix)
    current_drivers = driver_list[:20]
    
    # Grab win probabilities and expected finish numbers to calculate theta for each driver
    # theta will be used for Plackett-Luce model for ranking drivers
    p_win = [d.win_prob for d in current_drivers]
    exp_finish = [d.expected_finish for d in current_drivers]
    theta = pl_theta_from_mix(p_win, exp_finish)
    for i, driver in enumerate(current_drivers):
        driver.theta = theta[i]
        
    race_matrix, win_matrix = monte_carlo(current_drivers, 1000)
    
    for i, driver in enumerate(current_drivers):
        driver.sim_results = np.array([w[i] for w in win_matrix])
        
    

>>>>>>> e85e0ea (Updated Readme)
