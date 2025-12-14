"""User configuration for Fantasy Hockey Analytics."""

import os

# Database path
DB_PATH = os.getenv("FANTASY_DB_PATH", "fantasy_hockey.db")

# User's team ID (set this in .env or override with --id flag)
MY_TEAM_ID = int(os.getenv("MY_TEAM_ID", "0"))


def get_my_team_id() -> int:
    """Get the configured team ID."""
    return MY_TEAM_ID


def is_my_team_configured() -> bool:
    """Check if user has configured their team ID."""
    return MY_TEAM_ID > 0
