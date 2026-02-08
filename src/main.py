import os

import uvicorn
from fastapi import FastAPI

from .routes import auth, gear, health

app = FastAPI(title="Strava Stats Service", debug=True)

# Register routers
app.include_router(auth.router)
app.include_router(gear.router)
app.include_router(health.router)

host = os.getenv("HOST", "127.0.0.1")
port = int(os.getenv("PORT", 8000))


def main():
    """Entry point for running the FastAPI application with uvicorn."""
    uvicorn.run(app, host=host, port=port, log_level="info", access_log=False)


if __name__ == "__main__":
    main()
