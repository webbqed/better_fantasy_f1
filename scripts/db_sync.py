"""Push pipeline output into the database through the FastAPI endpoints.

These functions talk to the running API over HTTP (not the DB directly), so the
API server must be up when they run. Each is safe to re-run: races and drivers
are only created if missing, while prices are always appended to preserve
historical price data.
"""
import os

import requests

from f1.data.openf1 import get_season_calendar
from f1.models.simulation import summarize_price_stats

API_BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def seed_races(year, api_base=API_BASE_URL):
    """Create any races from the season calendar that aren't in the DB yet."""
    calendar = get_season_calendar(year)
    existing = requests.get(f"{api_base}/races", timeout=30).json()
    existing_rounds = {(r["season_year"], r["round_number"]) for r in existing}

    created = 0
    for _, row in calendar.iterrows():
        round_number = int(row["round_number"])
        if (year, round_number) in existing_rounds:
            continue
        payload = {
            "season_year": year,
            "round_number": round_number,
            "race_name": f"{row['country_name']} Grand Prix",
            "race_date": row["date_start"].isoformat(),
            "is_completed": bool(row["is_completed"]),
        }
        requests.post(f"{api_base}/races", json=payload, timeout=30).raise_for_status()
        created += 1
    return created


def seed_drivers(drivers, api_base=API_BASE_URL):
    """Create any current-grid drivers that aren't in the DB yet (by number)."""
    existing = requests.get(f"{api_base}/drivers", timeout=30).json()
    existing_numbers = {d["driver_number"] for d in existing}

    created = 0
    for driver in drivers:
        if driver.driver_number in existing_numbers or not driver.full_name:
            continue
        payload = {
            "driver_number": int(driver.driver_number),
            "full_name": driver.full_name,
            "team_name": driver.team_name,
            "is_active": True,
        }
        requests.post(f"{api_base}/drivers", json=payload, timeout=30).raise_for_status()
        created += 1
    return created


def reconcile_active_drivers(drivers, api_base=API_BASE_URL):
    """Sync each driver's is_active flag to the current grid.

    Drivers in the current grid are marked active; everyone else inactive. This
    ONLY flips the flag — it never touches portfolio holdings, so a user's
    investment in a driver who drops off the grid stays intact (they can choose
    to sell). Returns (reactivated, deactivated) counts.
    """
    active_numbers = {int(d.driver_number) for d in drivers}
    db_drivers = requests.get(f"{api_base}/drivers", timeout=30).json()

    reactivated = deactivated = 0
    for d in db_drivers:
        desired = d["driver_number"] in active_numbers
        if d["is_active"] == desired:
            continue
        requests.patch(
            f"{api_base}/drivers/{d['id']}", json={"is_active": desired}, timeout=30
        ).raise_for_status()
        if desired:
            reactivated += 1
        else:
            deactivated += 1
    return reactivated, deactivated


def write_prices(drivers, year, api_base=API_BASE_URL):
    """Append a price row per driver for the next upcoming race.

    Returns (rows_written, race) so the caller can report which race the prices
    were attached to.
    """
    races = requests.get(f"{api_base}/races", timeout=30).json()
    upcoming = [r for r in races if r["season_year"] == year and not r["is_completed"]]
    if not upcoming:
        raise RuntimeError(
            f"No upcoming race found for {year}. Run seed_races first, or the "
            "season may be over."
        )
    race = min(upcoming, key=lambda r: r["round_number"])

    db_drivers = requests.get(f"{api_base}/drivers", timeout=30).json()
    id_by_number = {d["driver_number"]: d["id"] for d in db_drivers}

    written = 0
    for driver in drivers:
        driver_id = id_by_number.get(driver.driver_number)
        if driver_id is None:
            print(f"  skipped {driver.full_name}: not found in drivers table")
            continue
        payload = {
            "driver_id": driver_id,
            "race_id": race["id"],
            **summarize_price_stats(driver),
        }
        requests.post(f"{api_base}/driver-prices", json=payload, timeout=30).raise_for_status()
        written += 1
    return written, race