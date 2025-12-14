"""Quick debug script to discover team_id field in yfpy objects."""
import logging
import sys

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

from src.auth import get_yahoo_query
from src.data_fetcher import DataFetcher

LEAGUE_ID = "16597"
SEASON_YEAR = 2025

try:
    print("Connecting to Yahoo API...")
    query = get_yahoo_query(LEAGUE_ID)
    
    fetcher = DataFetcher(query, LEAGUE_ID)
    game_code = fetcher.get_game_id(SEASON_YEAR)
    
    print(f"\nFetching week 1 to inspect team objects...")
    yfpy_matchups = query.get_league_matchups_by_week(chosen_week=1)
    
    if yfpy_matchups:
        team_obj = yfpy_matchups[0].teams[0]
        print(f"\n=== Team Object Inspection ===")
        print(f"Team name: {team_obj.name}")
        print(f"Has team_id attr: {hasattr(team_obj, 'team_id')}")
        print(f"Has team_key attr: {hasattr(team_obj, 'team_key')}")
        
        if hasattr(team_obj, 'team_id'):
            print(f"team_id value: {team_obj.team_id}")
        if hasattr(team_obj, 'team_key'):
            print(f"team_key value: {team_obj.team_key}")
            
        print("\nAll attributes:")
        for attr in dir(team_obj):
            if not attr.startswith('_'):
                try:
                    val = getattr(team_obj, attr)
                    if not callable(val):
                        print(f"  {attr}: {val}")
                except:
                    pass
    
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
