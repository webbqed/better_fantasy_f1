# Fantasy F1 Monte Carlo Simulator

This project is a small Monte Carlo engine for modeling **Formula 1 driver performance** using recent race data from the public **OpenF1 API**. It estimates per-driver probabilities for:

- **DNF (Did Not Finish)**  
- **Race win probability**  
- **Expected finishing position**

Using those estimates, it builds a **Plackett–Luce ranking model** and simulates many races to generate a distribution of finishing positions for each driver (useful for fantasy games, “share prices”, or general performance analysis).

---

## Features

- Pulls race, driver and result data from **OpenF1** for the last few seasons.
- Uses **team-level priors** (per-team DNF rate, win rate, and expected finish) to stabilize estimates when data is sparse.
- Applies **recency weighting** (exponential decay by race) so recent performance matters more.
- Performs **Bayesian shrinkage** of win probabilities toward team priors for drivers with few races.
- Converts win probabilities + expected finish into **Plackett–Luce logits** (`theta`) for ranking.
- Runs a **Monte Carlo simulation** of many synthetic races, including DNFs, to estimate each driver’s finishing-position distribution.

---

## Project Structure

All logic currently lives in a single file:

- `better_fantasy_f1.py`  
  - Data structures:
    - `TeamPriors` – dataclass holding team-level priors.
    - `CAR_PRIORS` – dictionary of per-team priors for the 2025 season (with a `default` fallback).
    - `Driver` – encapsulates a driver’s identity plus probabilities, PL parameter `theta`, and simulation results.
  - OpenF1 helpers:
    - `fetch_openf1()`, `get_n_last_sessions()`, `get_n_last_results()`, `get_n_last_drivers()`
  - Statistics / modeling:
    - `pct_calc()`, `clamp_prob()`, `make_recency_weights()`
    - `weighted_rate_bool()`, `weighted_avg()`
    - `expected_finish_position()`
    - `dynamic_prior_strength_from_weights()`
    - `driver_odds()` – main function that estimates DNF, win probability, and expected finish for a given driver.
    - `pl_theta_from_mix()` – builds PL logits from win probabilities and expected finishes.
    - `monte_carlo()` – runs the race simulations.
  - Script entry point (`if __name__ == "__main__":`)
    - Pulls recent race history (current year and previous 2).
    - Builds `Driver` objects for each driver/team combo.
    - Chooses 20 “current” drivers.
    - Computes PL logits and runs Monte Carlo.
    - Stores each driver’s simulated finishing positions in `driver.sim_results`.

---

## Requirements

- **Python** 3.10+ (recommended)
- Python packages:
  - `pandas`
  - `numpy`
  - `requests`

### Install dependencies

```bash
pip install pandas numpy requests
```

---

## How it Works (High Level)

1. **Fetch historical races**

   ```python
   historical_sessions = get_n_last_sessions(
       [current_year, current_year - 1, current_year - 2]
   )
   historical_results = get_n_last_results(historical_sessions["session_key"])
   historical_drivers = get_n_last_drivers(historical_sessions["session_key"])
   ```

   The script pulls recent **race** sessions (not practice/qualifying) and joins driver metadata onto session results.

2. **Normalize team names**

   Some teams are aliased (`RB`, `AlphaTauri` → `Racing Bulls`) so that team priors line up correctly.

3. **Estimate per-driver probabilities**

   For each unique `(driver_number, team_name)`:

   ```python
   driver = driver_odds(
       driver_number,
       team_name,
       historical_results,
       dnf_prior=CAR_PRIORS[2025][team_name].dnf_prior,
       win_prior=CAR_PRIORS[2025][team_name].win_prior,
       expected_finish_prior=CAR_PRIORS[2025][team_name].expected_finish_prior,
   )
   ```

   - If a driver has **10+ races** in the data:
     - DNF probability is a Laplace-smoothed empirical rate, clamped to `[0.03, 0.15]`.
     - Win probability is a recency-weighted frequency of P1 finishes.
     - Expected finish is a recency-weighted average position over **finished** races.
   - If a driver has **<10 races**:
     - DNF and expected finish lean heavily on **team priors**.
     - Win probability is shrunk toward the prior using a dynamic prior strength based on effective sample size.

4. **Build PL logits**

   The script mixes two signals:

   - Win probabilities (`p_win`)
   - Expected finishes (`exp_finish`)

   to create a **mixed prior** and converts it to log-probabilities `theta` used by the Plackett–Luce model.

5. **Monte Carlo race simulation**

   `monte_carlo(current_drivers, n=1000)`:

   - For each simulated race:
     - Draws DNFs from each driver’s `dnf_prob`.
     - Draws Gumbel noise and adds it to `theta`.
     - Ranks drivers; DNFs are forced to the bottom.
   - Returns arrays of simulated **scores** and **positions**.
   - Each `Driver` gets a `sim_results` array of their finishing positions across all runs.

---

## Running the Script

From the command line:

```bash
python better_fantasy_f1.py
```

This will:

- Fetch data from OpenF1.
- Build priors and probability estimates.
- Run a Monte Carlo simulation with 1000 races.
- Attach results to the `current_drivers` list in memory.

> **Note:** In its current form, the script doesn’t print or save a final table yet—it just builds the objects. You can extend the main block to write a CSV, pretty-print a table, or expose a CLI.

Example extension:

```python
if __name__ == "__main__":
    # ... existing logic ...

    # Simple summary: mean finishing position across simulations
    summary_rows = []
    for d in current_drivers:
        avg_finish = np.mean(d.sim_results)
        win_rate = np.mean(np.array(d.sim_results) == 1)
        summary_rows.append(
            {
                "driver": d.full_name,
                "team": d.team_name,
                "dnf_prob": d.dnf_prob,
                "win_prob": d.win_prob,
                "avg_finish": avg_finish,
                "sim_win_rate": win_rate,
            }
        )

    summary_df = pd.DataFrame(summary_rows).sort_values("avg_finish")
    print(summary_df.to_string(index=False))
```

---

## Using as a Module

You can also import this file in another script or notebook and reuse its functions:

```python
from better_fantasy_f1 import (
    get_n_last_sessions,
    get_n_last_results,
    get_n_last_drivers,
    driver_odds,
    pl_theta_from_mix,
    monte_carlo,
    CAR_PRIORS,
)

# Example: compute odds for a single driver/team from your own dataframe
driver = driver_odds(
    driver_number=4,
    team_name="McLaren",
    df=historical_results,
    dnf_prior=CAR_PRIORS[2025]["McLaren"].dnf_prior,
    win_prior=CAR_PRIORS[2025]["McLaren"].win_prior,
    expected_finish_prior=CAR_PRIORS[2025]["McLaren"].expected_finish_prior,
)
print(driver.get_info())
```

---

## Configuration / Customisation

You can tweak the behavior without changing the overall structure:

- **Number of simulations**  
  Change `n` in `monte_carlo(current_drivers, n=1000)`.

- **Recency half-life**  
  - `win_half_life`, `pos_half_life` in `driver_odds()` control how quickly old races “decay” in importance.
  - The default (6 races) means a race 6 races ago has ~half the weight of the most recent race.

- **Team priors**  
  Edit the `CAR_PRIORS[2025]` table to match your beliefs or updated performance expectations.

- **Mix between win odds and expected finish**  
  Change `mix` and `beta` in `pl_theta_from_mix()`.

---

## Potential Next Steps

Some ideas for future improvements:

- Output a CSV/JSON summary of each driver’s simulated stats.
- Build a small CLI (e.g., using `argparse`) to:
  - Choose seasons / number of races.
  - Change number of simulations or priors from the command line.
- Add a function to convert simulated stats into a **“share price”** metric for fantasy F1 games.
- Add simple unit tests for critical pieces like `driver_odds()` and `monte_carlo()`.
