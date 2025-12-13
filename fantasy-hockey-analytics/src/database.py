"""SQLite persistence layer for Fantasy Hockey Analytics."""

import sqlite3
from typing import List, Dict
from datetime import datetime
from .models import SeasonData, Matchup
from .constants import ALL_CATEGORIES, LOWER_IS_BETTER


def init_db(db_path: str = "fantasy_hockey.db"):
    """Create tables if they don't exist."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Track when we fetched data
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weekly_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            week_number INTEGER NOT NULL,
            fetched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_complete BOOLEAN NOT NULL,
            UNIQUE(week_number)
        )
    """)
    
    # One row per matchup
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS matchup_results (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            snapshot_id INTEGER REFERENCES weekly_snapshots(id),
            week_number INTEGER NOT NULL,
            team1_name TEXT NOT NULL,
            team2_name TEXT NOT NULL,
            team1_manager TEXT,
            team2_manager TEXT,
            team1_category_wins INTEGER,
            team2_category_wins INTEGER,
            ties INTEGER,
            is_complete BOOLEAN NOT NULL
        )
    """)
    
    # One row per category per matchup - key table for analytics
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS category_outcomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matchup_id INTEGER REFERENCES matchup_results(id),
            week_number INTEGER NOT NULL,
            category TEXT NOT NULL,
            team1_value REAL NOT NULL,
            team2_value REAL NOT NULL,
            winner TEXT NOT NULL,
            winning_value REAL,
            losing_value REAL,
            is_complete BOOLEAN NOT NULL
        )
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
                (snapshot_id, week_number, team1_name, team2_name, team1_manager, team2_manager,
                 team1_category_wins, team2_category_wins, ties, is_complete)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (snapshot_id, week_num, matchup.team1.team_name, matchup.team2.team_name,
                  matchup.team1.manager_name, matchup.team2.manager_name,
                  t1_wins, t2_wins, ties, matchup.is_complete))
            
            matchup_id = cursor.lastrowid
            
            # Insert category outcomes
            for category in ALL_CATEGORIES:
                team1_value = getattr(matchup.team1, category)
                team2_value = getattr(matchup.team2, category)
                winner_name = matchup.category_winners.get(category, "Tie")
                
                # Determine winning and losing values
                if winner_name == "Tie":
                    winning_value = None
                    losing_value = None
                elif winner_name == matchup.team1.team_name:
                    winning_value = team1_value
                    losing_value = team2_value
                else:
                    winning_value = team2_value
                    losing_value = team1_value
                
                cursor.execute("""
                    INSERT INTO category_outcomes
                    (matchup_id, week_number, category, team1_value, team2_value,
                     winner, winning_value, losing_value, is_complete)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (matchup_id, week_num, category, team1_value, team2_value,
                      winner_name, winning_value, losing_value, matchup.is_complete))
    
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
