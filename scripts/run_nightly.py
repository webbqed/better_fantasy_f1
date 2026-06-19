import sys
import os
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from f1.pipeline import run

if __name__ == "__main__":
    drivers = run()
    drivers = sorted(drivers, key=lambda d: d.sim_mean, reverse=True)

    col = "{:<24} {:>6} {:>6} {:>6} {:>6} {:>8} {:>7} {:>7} {:>7} {:>7}"
    print(col.format(
        "Driver", "Price", "Win%", "Top3%", "DNF%",
        "AvgPts", "Std/$100", "MedPos", "Best5%", "Best25%",
    ))
    print("-" * 90)

    for d in drivers:
        results = d.sim_results
        dnf_mask = results == -100
        finishes = results[~dnf_mask]

        win_pct      = np.mean(results == 1) * 100
        top3_pct     = np.mean((results <= 3) & ~dnf_mask) * 100
        dnf_pct      = np.mean(dnf_mask) * 100
        med_pos      = float(np.median(finishes))        if len(finishes) else float("nan")
        p5           = float(np.percentile(finishes,  5)) if len(finishes) else float("nan")
        p25          = float(np.percentile(finishes, 25)) if len(finishes) else float("nan")
        std_per_100  = d.sim_std * (100 / d.price)

        print(col.format(
            d.full_name[:24],
            f"{d.price:.1f}",
            f"{win_pct:.1f}%",
            f"{top3_pct:.1f}%",
            f"{dnf_pct:.1f}%",
            f"{d.sim_mean:.2f}",
            f"{std_per_100:.2f}",
            f"{med_pos:.0f}",
            f"{p5:.0f}",
            f"{p25:.0f}",
        ))

    print(f"\n{len(drivers)} drivers | 1,000 simulations each")
    print(
        "\nColumn guide:"
        "\n  Price    — model price (higher = model thinks driver is more valuable)"
        "\n  Win%     — % of simulations where driver wins"
        "\n  Top3%    — % of simulations where driver finishes on the podium (P1-P3)"
        "\n  DNF%     — % of simulations where driver does not finish"
        "\n  AvgPts   — mean fantasy points across all simulations"
        "\n  StdPts   — standard deviation of fantasy points per $100 invested (higher = more volatile per dollar)"
        "\n  MedPos   — median finishing position, excluding DNFs (lower = better)"
        "\n  Best5%   — finishing position in the best 5% of non-DNF simulations"
        "\n  Best25%  — finishing position in the best 25% of non-DNF simulations"
    )
