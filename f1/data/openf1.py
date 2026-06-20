import time
import requests
import pandas as pd
from f1.config import BASE_URL


def fetch_openf1(endpoint: str, **params):
    """Fetch data from the OpenF1 API with exponential-backoff retry on 429."""
    url = f"{BASE_URL}/{endpoint}"
    for attempt in range(5):
        resp = requests.get(url, params=params, timeout=10)
        if resp.status_code == 429:
            wait = 2 ** attempt
            print(f"Rate limited, retrying in {wait}s...")
            time.sleep(wait)
            continue
        resp.raise_for_status()
        return resp.json()
    resp.raise_for_status()


def get_n_last_sessions(years, n=40):
    sessions = []
    for year in years:
        sessions.extend(fetch_openf1('sessions', year=year, session_name="Race"))
    df = pd.DataFrame(sessions)
    df['date_start'] = pd.to_datetime(df['date_start'], utc=True)
    now = pd.Timestamp.now(tz='UTC')
    df = df[(df['date_start'] < now) & (~df['is_cancelled'].astype(bool))]
    return df.sort_values(by='date_start', ascending=False).head(n)


def get_season_calendar(year):
    """Return all (non-cancelled) race sessions for a season, past and upcoming.

    Unlike get_n_last_sessions, this keeps future races so we can seed the full
    calendar. round_number is derived from date order (OpenF1 doesn't provide it),
    and is_completed marks races whose start time is already in the past.
    """
    sessions = fetch_openf1('sessions', year=year, session_name="Race")
    df = pd.DataFrame(sessions)
    df['date_start'] = pd.to_datetime(df['date_start'], utc=True)
    df = df[~df['is_cancelled'].astype(bool)]
    df = df.sort_values('date_start').reset_index(drop=True)
    df['round_number'] = df.index + 1
    now = pd.Timestamp.now(tz='UTC')
    df['is_completed'] = df['date_start'] < now
    return df


def get_n_last_results(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('session_result', session_key=session))
        time.sleep(2.0)
    return pd.DataFrame(results)


def get_n_last_drivers(sessions):
    results = []
    for session in sessions:
        results.extend(fetch_openf1('drivers', session_key=session))
        time.sleep(2.0)
    return pd.DataFrame(results)
