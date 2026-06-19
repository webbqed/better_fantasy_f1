import datetime
import numpy as np

from f1.config import CAR_PRIORS, team_aliases, point_values, dnf_value
from f1.data.openf1 import get_n_last_sessions, get_n_last_results, get_n_last_drivers
from f1.models.stats import driver_odds
from f1.models.simulation import pl_theta_from_mix, monte_carlo, points_from_finishes, price_from_stats



def run():
    """
    Fetch historical data, compute driver stats, run simulation, and return
    a list of Driver objects with all fields (price, sim_mean, sim_std, etc.) populated.
    """
    current_year = datetime.date.today().year
    prior_year = min(current_year, max(CAR_PRIORS.keys()))

    historical_sessions = get_n_last_sessions([current_year, current_year - 1, current_year - 2])
    historical_results = get_n_last_results(historical_sessions['session_key'])
    historical_drivers = get_n_last_drivers(historical_sessions['session_key'])

    historical_results = historical_results.merge(historical_drivers, on=['session_key', 'driver_number'])
    historical_results = historical_results.replace(team_aliases)

    # Determine current grid from the most recent session; each driver gets exactly
    # one entry using their current team (handles mid-season team changes cleanly).
    most_recent_session = historical_sessions.iloc[0]['session_key']
    recent = historical_results[historical_results['session_key'] == most_recent_session]
    current_team_by_driver = (
        recent.drop_duplicates('driver_number')
        .set_index('driver_number')['team_name']
        .to_dict()
    )

    current_drivers = []
    for driver_number, team_name in current_team_by_driver.items():
        priors = CAR_PRIORS[prior_year].get(team_name, CAR_PRIORS[prior_year]['default'])
        current_drivers.append(driver_odds(
            driver_number, team_name, historical_results,
            dnf_prior=priors.dnf_prior,
            win_prior=priors.win_prior,
            expected_finish_prior=priors.expected_finish_prior,
        ))

    thetas = pl_theta_from_mix(
        [d.win_prob for d in current_drivers],
        [d.expected_finish for d in current_drivers],
    )
    for i, driver in enumerate(current_drivers):
        driver.theta = thetas[i]

    _, positions = monte_carlo(current_drivers, n=1000)

    for i, driver in enumerate(current_drivers):
        driver.sim_results = np.array([p[i] for p in positions])
        driver.sim_points = points_from_finishes(driver.sim_results, point_values, dnf_value)
        driver.sim_mean = float(np.mean(driver.sim_points))
        driver.sim_std = float(np.std(driver.sim_points))
        driver.price = price_from_stats(driver.sim_mean, driver.sim_std)

    return current_drivers
