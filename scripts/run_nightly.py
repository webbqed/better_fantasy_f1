import sys
import os
import datetime
import numpy as np
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from f1.pipeline import run
from f1.models.simulation import summarize_price_stats
from scripts.db_sync import seed_races, seed_drivers, write_prices

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
        stats = summarize_price_stats(d)

        # Best5%/Best25% are display-only (not stored on DriverPrice).
        results = d.sim_results
        finishes = results[results != -100]
        p5  = float(np.percentile(finishes,  5)) if len(finishes) else float("nan")
        p25 = float(np.percentile(finishes, 25)) if len(finishes) else float("nan")

        print(col.format(
            d.full_name[:24],
            f"{stats['price']:.1f}",
            f"{stats['win_prob'] * 100:.1f}%",
            f"{stats['top3_prob'] * 100:.1f}%",
            f"{stats['dnf_prob'] * 100:.1f}%",
            f"{stats['avg_pts']:.2f}",
            f"{stats['std_per_100']:.2f}",
            f"{stats['median_position']:.0f}",
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

    # Push results to the database through the API. Requires the API server to
    # be running (see API_BASE_URL in scripts/db_sync.py).
    year = datetime.date.today().year
    print("\nSyncing to database...")
    try:
        new_races = seed_races(year)
        new_drivers = seed_drivers(drivers)
        written, race = write_prices(drivers, year)
        print(f"  races seeded: {new_races} new")
        print(f"  drivers seeded: {new_drivers} new")
        print(f"  prices written: {written} for round {race['round_number']} ({race['race_name']})")
    except requests.exceptions.ConnectionError:
        print("  ERROR: could not reach the API. Is the uvicorn server running?")