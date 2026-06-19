import pandas as pd
import numpy as np
import pytest

from f1.models.stats import (
    pct_calc, clamp_prob, make_recency_weights,
    weighted_rate_bool, weighted_avg, driver_odds,
)
from f1.models.driver import Driver


def make_race_df(n_races=12, driver_number=44, team_name="Mercedes", n_wins=2, n_dnf=0):
    """Build a minimal race-history DataFrame for testing."""
    rows = []
    for i in range(n_races):
        rows.append({
            "driver_number": driver_number,
            "full_name": "Test DRIVER",
            "team_name": team_name,
            "session_key": 9000 + i,
            "position": 1 if i < n_wins else 3,
            "dnf": i >= (n_races - n_dnf),
        })
    return pd.DataFrame(rows)


class TestPctCalc:
    def test_basic(self):
        df = pd.DataFrame({"dnf": [True, False, False, True]})
        assert pct_calc("dnf", True, df) == pytest.approx((2 + 1) / (4 + 1 + 19))

    def test_empty_df(self):
        df = pd.DataFrame({"dnf": pd.Series([], dtype=bool)})
        assert pct_calc("dnf", True, df) == pytest.approx(1 / 20)

    def test_list_val(self):
        df = pd.DataFrame({"pos": [1, 2, 3, 4]})
        assert pct_calc("pos", [1, 2], df) == pytest.approx((2 + 1) / (4 + 1 + 19))


class TestClampProb:
    def test_in_range(self):
        assert clamp_prob(0.08) == pytest.approx(0.08)

    def test_below_min(self):
        assert clamp_prob(0.01) == pytest.approx(0.03)

    def test_above_max(self):
        assert clamp_prob(0.99) == pytest.approx(0.15)


class TestMakeRecencyWeights:
    def test_sums_to_one(self):
        assert np.sum(make_recency_weights(10)) == pytest.approx(1.0)

    def test_most_recent_highest(self):
        w = make_recency_weights(5)
        assert w[0] > w[1] > w[2]

    def test_empty(self):
        assert make_recency_weights(0) == []

    def test_single(self):
        assert make_recency_weights(1)[0] == pytest.approx(1.0)


class TestDriverOdds:
    def test_sufficient_data_returns_driver(self):
        df = make_race_df(n_races=12)
        d = driver_odds(44, "Mercedes", df)
        assert isinstance(d, Driver)
        assert d.win_prob is not None
        assert d.dnf_prob is not None

    def test_sufficient_data_dnf_clamped(self):
        df = make_race_df(n_races=12, n_dnf=0)
        d = driver_odds(44, "Mercedes", df)
        assert 0.03 <= d.dnf_prob <= 0.15

    def test_insufficient_data_uses_prior(self):
        df = make_race_df(n_races=3, n_wins=0)
        d = driver_odds(44, "Mercedes", df, win_prior=0.25, dnf_prior=0.08)
        # With Bayesian shrinkage toward 0.25 from 0 observed wins, result is between 0 and 0.25
        assert 0.0 < d.win_prob < 0.5

    def test_no_history_returns_fallback(self):
        df = make_race_df(n_races=12)
        d = driver_odds(99, "Unknown Team", df)
        assert d.dnf_prob == pytest.approx(0.07)
        assert d.win_prob == pytest.approx(0.01)
