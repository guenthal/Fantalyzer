import logging
import sys
from src.auth import get_yahoo_query
from src.data_fetcher import DataFetcher
from src.display import print_season_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
# Disable verbose debug logging (re-enable if needed for troubleshooting)
# logging.getLogger('yahoo_oauth').setLevel(logging.DEBUG)
# logging.getLogger('urllib3').setLevel(logging.DEBUG)
# logging.getLogger('src.data_fetcher').setLevel(logging.DEBUG)

LEAGUE_ID = "16597"
SEASON_YEAR = 2025

def main():
    print("Welcome to Fantasy Hockey Analytics Phase 1")
    
    try:
        # 1. Auth
        print("Initializing Yahoo API connection...")
        query = get_yahoo_query(LEAGUE_ID)
        
        # 2. Setup Fetcher
        fetcher = DataFetcher(query, LEAGUE_ID)
        
        # 3. Resolve Game ID
        game_code = fetcher.get_game_id(SEASON_YEAR)
        print(f"Resolved Game ID for {SEASON_YEAR}: {game_code}")
        
        # 4. Fetch Data
        print("Fetching matchups for weeks 1-9...")
        season_data = fetcher.fetch_season_data(game_code, start_week=1, end_week=9)
        
        # 5. Display
        print_season_summary(season_data)
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        logging.exception("Detailed Traceback:")

if __name__ == "__main__":
    main()
