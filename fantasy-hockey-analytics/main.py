import logging
import sys
import argparse
from src.auth import get_yahoo_query
from src.data_fetcher import DataFetcher
from src.display import (
    print_season_summary, 
    print_threshold_report, 
    print_data_status, 
    print_fetch_summary,
    print_team_list,
    print_team_analysis
)
from src.database import (
    init_db, 
    save_season_data, 
    get_weeks_stored,
    get_all_teams,
    team_exists,
    drop_all_tables
)
from src.analytics import calculate_all_thresholds, get_analysis_summary
from src.team_analysis import analyze_team
from src.config import get_my_team_id, is_my_team_configured

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


def team_command(args):
    """Handle team analysis commands."""
    try:
        init_db()
        
        # Handle --list flag
        if args.list:
            teams = get_all_teams()
            if not teams:
                print("\nNo teams in database. Run 'python main.py fetch' first.")
                return False
            print_team_list(teams)
            return True
        
        # Determine team_id
        if args.id:
            team_id = args.id
        else:
            team_id = get_my_team_id()
            if team_id == 0:
                print("\n" + "=" * 60)
                print("No team specified")
                print("=" * 60)
                print("Please either:")
                print("  1. Set MY_TEAM_ID in your .env file, or")
                print("  2. Use --id <team_id> flag")
                print("\nRun 'python main.py team --list' to see available teams.")
                print("=" * 60)
                return False
        
        # Validate team exists
        if not team_exists(team_id):
            print(f"\nTeam ID {team_id} not found.")
            print("Run 'python main.py team --list' to see available teams.")
            return False
        
        # Check we have data to analyze
        summary = get_analysis_summary()
        if summary['weeks_analyzed'] == 0:
            print("\n" + "=" * 60)
            print("Insufficient Data")
            print("=" * 60)
            print("No complete weeks available for analysis.")
            if summary['weeks_excluded'] > 0:
                incomplete_str = ', '.join(map(str, summary['incomplete_week_numbers']))
                print(f"Week(s) {incomplete_str} still in progress.")
            print("\nAnalysis requires at least one completed week.")
            print("Run 'python main.py fetch' to get more data.")
            print("=" * 60)
            return False
        
        # Run analysis
        result = analyze_team(team_id)
        print_team_analysis(result)
        return True
        
    except Exception as e:
        print(f"\nError during team analysis: {e}")
        logging.exception("Detailed Traceback:")
        return False


def migrate_command(args):
    """Migrate database schema."""
    print("\n" + "=" * 60)
    print("DATABASE MIGRATION")
    print("=" * 60)
    print("This will delete all existing data in the database.")
    print("Data can be re-fetched from Yahoo after migration.")
    print("=" * 60)
    
    confirm = input("\nProceed with migration? (yes/no): ")
    
    if confirm.lower() != 'yes':
        print("\nMigration cancelled.")
        return False
    
    try:
        print("\nDropping old tables...")
        drop_all_tables()
        
        print("Creating new schema...")
        init_db()
        
        print("\n" + "=" * 60)
        print("✓ Migration complete!")
        print("=" * 60)
        print("\nRun 'python main.py fetch' to reload data with new schema.")
        return True
        
    except Exception as e:
        print(f"\nError during migration: {e}")
        logging.exception("Detailed Traceback:")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Fantasy Hockey Analytics - Phase 3: Team Performance Analysis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Commands:
  fetch           Fetch latest data from Yahoo and persist to DB
  status          Show what weeks are stored and their completion status
  analyze         Run threshold analysis on stored data (complete weeks only)
  team            Analyze your team (requires MY_TEAM_ID in .env)
  team --list     Show all available teams
  team --id <ID>  Analyze a specific team by ID
  migrate         Migrate database schema (drops existing data)
  
Default behavior (no command): fetch + analyze
        """
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command to execute')
    
    # fetch command
    parser_fetch = subparsers.add_parser('fetch', help='Fetch data from Yahoo')
    
    # status command
    parser_status = subparsers.add_parser('status', help='Show database status')
    
    # analyze command
    parser_analyze = subparsers.add_parser('analyze', help='Run threshold analysis')
    
    # team command
    parser_team = subparsers.add_parser('team', help='Analyze team performance')
    parser_team.add_argument('--list', action='store_true', help='List all teams')
    parser_team.add_argument('--id', type=int, help='Team ID to analyze')
    
    # migrate command
    parser_migrate = subparsers.add_parser('migrate', help='Migrate database schema')
    
    args = parser.parse_args()
    
    # Welcome message
    print("\nWelcome to Fantasy Hockey Analytics - Phase 3")
    print("Team Performance Analysis\n")
    
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
        
    elif args.command == 'team':
        success = team_command(args)
        sys.exit(0 if success else 1)
        
    elif args.command == 'migrate':
        success = migrate_command(args)
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
