import numpy as np
import pytest

from f1.models.simulation import (
    get_competition_ranks, pl_theta_from_mix,
    monte_carlo, points_from_finishes, price_from_stats,
)
from f1.models.driver import Driver
from f1.config import point_values, dnf_value


def make_drivers(n=3):
    drivers = []
    for i in range(n):
        d = Driver(full_name=f"Driver {i}", driver_number=i, team_name="Team")
        d.theta = float(-i)   # driver 0 is strongest
        d.dnf_prob = 0.05
        drivers.append(d)
    return drivers


class TestGetCompetitionRanks:
    def test_basic(self):
        assert get_competition_ranks([10, 30, 20]) == [3, 1, 2]

    def test_single(self):
        assert get_competition_ranks([5]) == [1]

    def test_descending_input(self):
        assert get_competition_ranks([3, 2, 1]) == [1, 2, 3]


class TestPointsFromFinishes:
    def test_p1_earns_max(self):
        pts = points_from_finishes(np.array([1]), point_values, dnf_value)
        assert pts[0] == pytest.approx(2.5)

    def test_dnf_earns_penalty(self):
        pts = points_from_finishes(np.array([-100]), point_values, dnf_value)
        assert pts[0] == pytest.approx(-0.2)

    def test_p20_earns_zero(self):
        pts = points_from_finishes(np.array([20]), point_values, dnf_value)
        assert pts[0] == pytest.approx(0.0)

    def test_p5_earns_correct(self):
        pts = points_from_finishes(np.array([5]), point_values, dnf_value)
        assert pts[0] == pytest.approx(1.6)

    def test_mixed(self):
        pts = points_from_finishes(np.array([1, -100, 5]), point_values, dnf_value)
        assert pts[0] == pytest.approx(2.5)
        assert pts[1] == pytest.approx(-0.2)
        assert pts[2] == pytest.approx(1.6)


class TestPriceFromStats:
    def test_positive_mean(self):
        assert price_from_stats(mean=1.5, std=0.5) > 0

    def test_formula(self):
        # edge = max(1.5 - 0.1*0.5, 1.5*0.1) = max(1.45, 0.15) = 1.45
        # price = 50 * 1.45 = 72.5
        assert price_from_stats(mean=1.5, std=0.5, risk_discount_factor=0.1, K=50) == pytest.approx(72.5)

    def test_zero_mean_nonnegative(self):
        assert price_from_stats(mean=0.0, std=0.5) >= 0


class TestMonteCarlo:
    def test_output_shapes(self):
        drivers = make_drivers(3)
        theta_scores, positions = monte_carlo(drivers, n=100)
        assert len(theta_scores) == 100
        assert len(positions) == 100
        assert len(positions[0]) == 3

    def test_seeded_reproducible(self):
        drivers = make_drivers(3)
        _, pos1 = monte_carlo(drivers, n=20, seed=42)
        _, pos2 = monte_carlo(drivers, n=20, seed=42)
        assert np.array_equal(pos1, pos2)

    def test_dnf_encoded_minus_100(self):
        drivers = make_drivers(1)
        drivers[0].dnf_prob = 1.0
        _, positions = monte_carlo(drivers, n=50)
        assert all(p[0] == -100 for p in positions)


class TestPlThetaFromMix:
    def test_output_length(self):
        theta = pl_theta_from_mix([0.3, 0.1, 0.05, 0.05])
        assert len(theta) == 4

    def test_higher_win_prob_higher_theta(self):
        theta = pl_theta_from_mix([0.5, 0.1])
        assert theta[0] > theta[1]

    def test_uniform_win_probs_equal_theta(self):
        theta = pl_theta_from_mix([0.25, 0.25, 0.25, 0.25])
        assert theta[0] == pytest.approx(theta[1])
