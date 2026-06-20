from fastapi import FastAPI

from api.routers import (
    drivers,
    users,
    leagues,
    league_members,
    races,
    driver_prices,
    portfolio_holdings,
    transactions,
    race_results,
    matchups,
)

app = FastAPI(title="Better Fantasy F1")

app.include_router(users.router)
app.include_router(leagues.router)
app.include_router(league_members.router)
app.include_router(drivers.router)
app.include_router(races.router)
app.include_router(driver_prices.router)
app.include_router(portfolio_holdings.router)
app.include_router(transactions.router)
app.include_router(race_results.router)
app.include_router(matchups.router)


@app.get("/health")
def health():
    return {"status": "ok"}