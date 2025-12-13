import logging
import sys
import argparse
from src.auth import get_yahoo_query
from src.data_fetcher import DataFetcher
from src.display import print_season_summary, print_threshold_report, print_data_status, print_fetch_summary
from src.database import init_db, save_season_data, get_weeks_stored
from src.analytics import calculate_all_thresholds, get_analysis_summary

# Configure logging
logging.basicConfig(level=logging.INFO)
# Disable verbose debug logging (re-enable if needed for troubleshooting)
# logging.getLogger('yahoo_oauth').setLevel(logging.DEBUG)
# logging.getLogger('urllib3').setLevel(logging.DEBUG)
# logging.getLogger('src.data_fetcher').setLevel(logging.DEBUG)

LEAGUE_ID = "16597"
SEASON_YEAR = 2025


def fetch_data():
    """Fetch latest data from Yahoo and persist to database."""
    print("=" * 60)
    print("Fetching Data from Yahoo Fantasy API")
    print("=" * 60)
    
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
        print("Fetching matchups for weeks 1-10...")
        season_data = fetcher.fetch_season_data(game_code, start_week=1, end_week=10)
        
        # 5. Initialize database
        init_db()
        
        # 6. Save to database
        save_season_data(season_data)
        
        # 7. Display summary
        print_fetch_summary(season_data)
        print(f"\n✓ Data persisted to fantasy_hockey.db")
        
        return True
        
    except Exception as e:
        print(f"CRITICAL ERROR: {e}")
        logging.exception("Detailed Traceback:")
        return False


def show_status():
    """Show database status - which weeks are stored and their completion status."""
    print("=" * 60)
    print("Checking Database Status")
    print("=" * 60)
    
    try:
        init_db()  # Ensure DB exists
        weeks = get_weeks_stored()
        print_data_status(weeks)
        return True
        
    except Exception as e:
        print(f"Error reading database: {e}")
        logging.exception("Detailed Traceback:")
        return False


def analyze_data():
    """Run threshold analysis on stored complete weeks."""
    print("=" * 60)
    print("Running Threshold Analysis")
    print("=" * 60)
    
    try:
        init_db()  # Ensure DB exists
        
        # Get analysis summary
        summary = get_analysis_summary()
        
        # Calculate thresholds for all categories
        thresholds = calculate_all_thresholds()
        
        # Display the report
        print_threshold_report(thresholds, summary)
        
        return True
        
    except Exception as e:
        print(f"Error during analysis: {e}")
        logging.exception("Detailed Traceback:")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fantasy Hockey Analytics - Phase 2: Persistence & Threshold Engine",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  fetch     Fetch latest data from Yahoo and persist to DB
  status    Show what weeks are stored and their completion status
  analyze   Run threshold analysis on stored data (complete weeks only)
  
Default behavior (no command): fetch + analyze
        """
    )
    
    parser.add_argument(
        'command',
        nargs='?',
        choices=['fetch', 'status', 'analyze'],
        help='Command to execute (default: fetch and analyze)'
    )
    
    args = parser.parse_args()
    
    # Welcome message
    print("\nWelcome to Fantasy Hockey Analytics - Phase 2")
    print("Persistence & Threshold Engine\n")
    
    # Execute based on command
    if args.command == 'fetch':
        success = fetch_data()
        sys.exit(0 if success else 1)
        
    elif args.command == 'status':
        success = show_status()
        sys.exit(0 if success else 1)
        
    elif args.command == 'analyze':
        success = analyze_data()
        sys.exit(0 if success else 1)
        
    else:
        # Default: fetch + analyze
        print("Running default mode: fetch + analyze\n")
        
        # 1. Fetch data
        fetch_success = fetch_data()
        if not fetch_success:
            print("\n⚠ Fetch failed, skipping analysis")
            sys.exit(1)
        
        print("\n")  # Spacing
        
        # 2. Analyze data
        analyze_success = analyze_data()
        
        sys.exit(0 if analyze_success else 1)


if __name__ == "__main__":
    main()
