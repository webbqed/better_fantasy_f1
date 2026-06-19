import pandas as pd
import numpy as np
import pytest

from f1.models.driver import Driver
from f1.models.stats import driver_odds
from f1.models.simulation import pl_theta_from_mix, monte_carlo, points_from_finishes, price_from_stats
from f1.config import point_values, dnf_value


def make_driver(number, team, win_prob=0.05, dnf_prob=0.08, expected_finish=10.0):
    d = Driver(full_name=f"Driver {number}", driver_number=number, team_name=team)
    d.win_prob = win_prob
    d.dnf_prob = dnf_prob
    d.expected_finish = expected_finish
    return d


def simulate_grid(drivers):
    """Run the full simulation pipeline on a list of drivers and return them priced."""
    thetas = pl_theta_from_mix([d.win_prob for d in drivers], [d.expected_finish for d in drivers])
    for i, d in enumerate(drivers):
        d.theta = thetas[i]
    _, positions = monte_carlo(drivers, n=1000, seed=0)
    for i, d in enumerate(drivers):
        d.sim_results = np.array([p[i] for p in positions])
        d.sim_points = points_from_finishes(d.sim_results, point_values, dnf_value)
        d.sim_mean = float(np.mean(d.sim_points))
        d.sim_std = float(np.std(d.sim_points))
        d.price = price_from_stats(d.sim_mean, d.sim_std)
    return drivers


class TestGridSize:
    def test_standard_20_driver_grid(self):
        drivers = simulate_grid([make_driver(i, "Team") for i in range(20)])
        assert len(drivers) == 20
        assert all(d.price is not None for d in drivers)

    def test_22_driver_grid(self):
        drivers = simulate_grid([make_driver(i, "Team") for i in range(22)])
        assert len(drivers) == 22
        assert all(d.price is not None for d in drivers)

    def test_18_driver_grid(self):
        drivers = simulate_grid([make_driver(i, "Team") for i in range(18)])
        assert len(drivers) == 18
        assert all(d.price is not None for d in drivers)

    def test_dnf_always_scores_penalty_regardless_of_grid_size(self):
        for grid_size in [18, 20, 22]:
            drivers = [make_driver(i, "Team") for i in range(grid_size)]
            drivers[0].dnf_prob = 1.0  # first driver always DNFs
            drivers = simulate_grid(drivers)
            assert np.all(drivers[0].sim_points == dnf_value), (
                f"DNF driver should always score {dnf_value} on a {grid_size}-driver grid"
            )
