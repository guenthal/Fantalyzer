"""SQLite persistence layer for Fantasy Hockey Analytics - Schema v2 with Team IDs."""

import sqlite3
import sys
from typing import List, Dict, Optional
from datetime import datetime
from .models import SeasonData, Matchup
from .constants import ALL_CATEGORIES, LOWER_IS_BETTER

SCHEMA_VERSION = 2


def get_schema_version(db_path: str = "fantasy_hockey.db") -> int:
    """Check current schema version. Returns 1 if old schema, 2 if new, 0 if no database."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if teams table exists (v2 schema)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='teams'
        """)
        
        if cursor.fetchone():
            conn.close()
            return 2
        
        # Check if weekly_snapshots exists (v1 schema)
        cursor.execute("""
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name='weekly_snapshots'
        """)
        
        if cursor.fetchone():
            conn.close()
            return 1
        
        conn.close()
        return 0  # No database
        
    except sqlite3.OperationalError:
        return 0  # Database doesn't exist


def drop_all_tables(db_path: str = "fantasy_hockey.db"):
    """Drop all existing tables for migration."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()
    
    for table in tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table[0]}")
    
    conn.commit()
    conn.close()


def init_db(db_path: str = "fantasy_hockey.db"):
    """Create tables if they don't exist. Check for schema migration needs."""
    
    # Check if migration is needed
    current_version = get_schema_version(db_path)
    
    if current_version > 0 and current_version < SCHEMA_VERSION:
        print("\n" + "="*60)
        print("DATABASE SCHEMA MIGRATION REQUIRED")
        print("="*60)
        print(f"Current schema version: {current_version}")
        print(f"Required schema version: {SCHEMA_VERSION}")
        print("\nThis will delete existing data (can be re-fetched from Yahoo).")
        print("Run 'python main.py migrate' to proceed.")
        print("="*60)
        sys.exit(1)
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create teams table (NEW in v2)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS teams (
            team_id INTEGER PRIMARY KEY,
            current_name TEXT NOT NULL,
            manager_name TEXT,
            first_seen_week INTEGER,
            last_seen_week INTEGER
        )
    """)
    
    # Create weekly_snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_complete BOOLEAN NOT NULL,
            UNIQUE(week_number)
        )
    """)
    
    # Create matchup_results table (MODIFIED in v2 - uses team_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchup_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER REFERENCES weekly_snapshots(id),
            week_number INTEGER NOT NULL,
            team1_id INTEGER NOT NULL REFERENCES teams(team_id),
            team2_id INTEGER NOT NULL REFERENCES teams(team_id),
            team1_category_wins INTEGER,
            team2_category_wins INTEGER,
            ties INTEGER,
            is_complete BOOLEAN NOT NULL
        )
    """)
    
    # Create category_outcomes table (MODIFIED in v2 - uses team_id)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matchup_id INTEGER REFERENCES matchup_results(id),
            week_number INTEGER NOT NULL,
            category TEXT NOT NULL,
            team1_id INTEGER NOT NULL,
            team2_id INTEGER NOT NULL,
            team1_value REAL NOT NULL,
            team2_value REAL NOT NULL,
            winner_team_id INTEGER,
            winning_value REAL,
            losing_value REAL,
            is_complete BOOLEAN NOT NULL
        )
    """)
    
    # Create indexes for common queries
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_outcomes_team1 
        ON category_outcomes(team1_id, category, is_complete)
    """)
    
    cursor.execute("""
        CREATE INDEX IF NOT EXISTS idx_category_outcomes_team2 
        ON category_outcomes(team2_id, category, is_complete)
    """)
    
    conn.commit()
    conn.close()


def save_season_data(data: SeasonData, db_path: str = "fantasy_hockey.db"):
    """Persist a SeasonData object. Updates existing weeks if re-fetched."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Group matchups by week
    weeks_data = {}
    for matchup in data.matchups:
        if matchup.week not in weeks_data:
            weeks_data[matchup.week] = []
        weeks_data[matchup.week].append(matchup)
    
    # Process each week
    for week_num, matchups in weeks_data.items():
        # Determine if week is complete (all matchups in week must be complete)
        is_complete = all(m.is_complete for m in matchups)
        
        # Insert or update weekly snapshot
        cursor.execute("""
            INSERT INTO weekly_snapshots (week_number, is_complete, fetched_at)
            VALUES (?, ?, ?)
            ON CONFLICT(week_number) DO UPDATE SET
                is_complete = excluded.is_complete,
                fetched_at = excluded.fetched_at
        """, (week_num, is_complete, datetime.now()))
        
        # Get the snapshot ID
        cursor.execute("SELECT id FROM weekly_snapshots WHERE week_number = ?", (week_num,))
        snapshot_id = cursor.fetchone()[0]
        
        # Delete existing matchup data for this week (to handle re-fetches)
        cursor.execute("DELETE FROM matchup_results WHERE week_number = ?", (week_num,))
        
        # Insert matchups for this week
        for matchup in matchups:
            # Upsert teams
            for team in [matchup.team1, matchup.team2]:
                cursor.execute("""
                    INSERT INTO teams (team_id, current_name, manager_name, first_seen_week, last_seen_week)
                    VALUES (?, ?, ?, ?, ?)
                    ON CONFLICT(team_id) DO UPDATE SET
                        current_name = excluded.current_name,
                        last_seen_week = excluded.last_seen_week
                """, (team.team_id, team.team_name, team.manager_name, week_num, week_num))
            
            # Calculate category wins
            t1_wins = sum(1 for winner in matchup.category_winners.values() 
                         if winner == matchup.team1.team_name)
            t2_wins = sum(1 for winner in matchup.category_winners.values() 
                         if winner == matchup.team2.team_name)
            ties = sum(1 for winner in matchup.category_winners.values() 
                      if winner == "Tie")
            
            # Insert matchup result
            cursor.execute("""
                INSERT INTO matchup_results 
                (snapshot_id, week_number, team1_id, team2_id,
                 team1_category_wins, team2_category_wins, ties, is_complete)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, week_num, matchup.team1.team_id, matchup.team2.team_id,
                  t1_wins, t2_wins, ties, matchup.is_complete))
            
            matchup_id = cursor.lastrowid
            
            # Insert category outcomes
            for category in ALL_CATEGORIES:
                team1_value = getattr(matchup.team1, category)
                team2_value = getattr(matchup.team2, category)
                winner_name = matchup.category_winners.get(category, "Tie")
                
                # Determine winner_team_id and winning/losing values
                if winner_name == "Tie":
                    winner_team_id = None
                    winning_value = None
                    losing_value = None
                elif winner_name == matchup.team1.team_name:
                    winner_team_id = matchup.team1.team_id
                    winning_value = team1_value
                    losing_value = team2_value
                else:
                    winner_team_id = matchup.team2.team_id
                    winning_value = team2_value
                    losing_value = team1_value
                
                cursor.execute("""
                    INSERT INTO category_outcomes
                    (matchup_id, week_number, category, team1_id, team2_id,
                     team1_value, team2_value, winner_team_id, winning_value, losing_value, is_complete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (matchup_id, week_num, category, matchup.team1.team_id, matchup.team2.team_id,
                      team1_value, team2_value, winner_team_id, winning_value, losing_value, matchup.is_complete))
    
    conn.commit()
    conn.close()


def get_all_category_outcomes(category: str, complete_only: bool = True, 
                               db_path: str = "fantasy_hockey.db") -> List[dict]:
    """Fetch all outcomes for a specific category. Defaults to complete weeks only."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    query = """
        SELECT * FROM category_outcomes
        WHERE category = ?
    """
    params = [category]
    
    if complete_only:
        query += " AND is_complete = 1"
    
    cursor.execute(query, params)
    results = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return results


def get_weeks_stored(db_path: str = "fantasy_hockey.db") -> List[dict]:
    """Return list of weeks with completion status: [{'week': 1, 'is_complete': True}, ...]"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT week_number as week, is_complete, fetched_at
        FROM weekly_snapshots
        ORDER BY week_number
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_incomplete_weeks(db_path: str = "fantasy_hockey.db") -> List[int]:
    """Return list of week numbers that are still in progress."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT week_number
        FROM weekly_snapshots
        WHERE is_complete = 0
        ORDER BY week_number
    """)
    
    results = [row[0] for row in cursor.fetchall()]
    conn.close()
    return results


# NEW FUNCTIONS FOR PHASE 3

def get_all_teams(db_path: str = "fantasy_hockey.db") -> List[dict]:
    """Return all teams: [{team_id, current_name, manager_name}, ...]"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT team_id, current_name, manager_name
        FROM teams
        ORDER BY team_id
    """)
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return results


def get_team_by_id(team_id: int, db_path: str = "fantasy_hockey.db") -> Optional[dict]:
    """Return team info or None."""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT team_id, current_name, manager_name, first_seen_week, last_seen_week
        FROM teams
        WHERE team_id = ?
    """, (team_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None


def team_exists(team_id: int, db_path: str = "fantasy_hockey.db") -> bool:
    """Check if team ID exists in database."""
    team = get_team_by_id(team_id, db_path)
    return team is not None


def get_team_category_values(team_id: int, category: str,
                              complete_only: bool = True,
                              db_path: str = "fantasy_hockey.db") -> List[dict]:
    """
    Query category_outcomes for a specific team.
    
    Returns list of {week, team_value, opponent_value, won} dicts.
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Build query conditions
    complete_filter = "AND is_complete = 1" if complete_only else ""
    
    # Query when team is team1
    query1 = f"""
        SELECT 
            week_number as week,
            team1_value as team_value,
            team2_value as opponent_value,
            CASE 
                WHEN winner_team_id = ? THEN 1
                WHEN winner_team_id IS NULL THEN NULL
                ELSE 0
            END as won
        FROM category_outcomes
        WHERE team1_id = ? AND category = ? {complete_filter}
    """
    
    cursor.execute(query1, (team_id, team_id, category))
    results = [dict(row) for row in cursor.fetchall()]
    
    # Query when team is team2
    query2 = f"""
        SELECT 
            week_number as week,
            team2_value as team_value,
            team1_value as opponent_value,
            CASE 
                WHEN winner_team_id = ? THEN 1
                WHEN winner_team_id IS NULL THEN NULL
                ELSE 0
            END as won
        FROM category_outcomes
        WHERE team2_id = ? AND category = ? {complete_filter}
    """
    
    cursor.execute(query2, (team_id, team_id, category))
    results.extend([dict(row) for row in cursor.fetchall()])
    
    # Sort by week
    results.sort(key=lambda x: x['week'])
    
    conn.close()
    return results
