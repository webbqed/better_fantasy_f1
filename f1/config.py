from dataclasses import dataclass

BASE_URL = "https://api.openf1.org/v1"

@dataclass
class TeamPriors:
    dnf_prior: float               # per-race DNF prob
    win_prior: float               # per-race win prob
    expected_finish_prior: float   # lower = better (e.g., 2.4 means ~P2-P3 on avg)

CAR_PRIORS = {
    2025: {
        "Red Bull Racing":  TeamPriors(dnf_prior=0.07, win_prior=0.01, expected_finish_prior=8.0),
        "McLaren":          TeamPriors(dnf_prior=0.06, win_prior=0.10, expected_finish_prior=4.0),
        "Ferrari":          TeamPriors(dnf_prior=0.08, win_prior=0.01, expected_finish_prior=7.0),
        "Mercedes":         TeamPriors(dnf_prior=0.08, win_prior=0.07, expected_finish_prior=7.0),
        "Aston Martin":     TeamPriors(dnf_prior=0.11, win_prior=0.02, expected_finish_prior=11.0),
        "Alpine":           TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Haas F1 Team":     TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Kick Sauber":      TeamPriors(dnf_prior=0.13, win_prior=0.00, expected_finish_prior=12.0),
        "Williams":         TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=10.0),
        "Racing Bulls":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=9.0),
        "default":          TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=8.5),
    },
    2026: {
        "Red Bull Racing":  TeamPriors(dnf_prior=0.07, win_prior=0.01, expected_finish_prior=8.0),
        "McLaren":          TeamPriors(dnf_prior=0.06, win_prior=0.10, expected_finish_prior=4.0),
        "Ferrari":          TeamPriors(dnf_prior=0.08, win_prior=0.01, expected_finish_prior=7.0),
        "Mercedes":         TeamPriors(dnf_prior=0.08, win_prior=0.07, expected_finish_prior=7.0),
        "Aston Martin":     TeamPriors(dnf_prior=0.11, win_prior=0.02, expected_finish_prior=11.0),
        "Alpine":           TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=13.0),
        "Haas F1 Team":     TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=12.0),
        "Audi":             TeamPriors(dnf_prior=0.12, win_prior=0.00, expected_finish_prior=13.0),
        "Williams":         TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=10.0),
        "Racing Bulls":     TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=10.0),
        "Cadillac":         TeamPriors(dnf_prior=0.15, win_prior=0.00, expected_finish_prior=16.0),
        "default":          TeamPriors(dnf_prior=0.10, win_prior=0.00, expected_finish_prior=8.5),
    },
}

team_aliases = {
    "RB": "Racing Bulls",
    "AlphaTauri": "Racing Bulls",
    "Kick Sauber": "Audi",
}

point_values = [2.5, 2.3, 2.1, 1.8, 1.6, 1.4, 1.2, 1.0, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.2, 0.1, 0.1, 0.0]
dnf_value = -0.2
