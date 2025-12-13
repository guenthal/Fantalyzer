from src.auth import get_yahoo_query
import logging
import json

# Setup logging
logging.basicConfig(level=logging.DEBUG)

def debug_stat_structure():
    LEAGUE_ID = "16597"
    query = get_yahoo_query(LEAGUE_ID)
    
    # Fetch week 1
    print("Fetching raw data for Week 1...")
    # chosen_week=1
    matchups = query.get_league_matchups_by_week(chosen_week=1)
    
    if not matchups:
        print("No matchups found!")
        return

    # Inspect the first team of the first matchup
    first_matchup = matchups[0]
    team1 = first_matchup.teams[0]
    
    print(f"\nTeam Name: {team1.name}")
    print(f"Team ID: {team1.team_id}")
    
    print("\n--- Team Object Dictionary Dump ---")
    # Helper to serialize bytes
    def json_default(o):
        if isinstance(o, bytes):
            return o.decode('utf-8')
        return str(o)
        
    print(json.dumps(team1.__dict__, default=json_default, indent=2))
    
    # Check explicitly for team_points just in case
    if hasattr(team1, 'team_points'):
        print(f"\nTeam Points: {team1.team_points}")

if __name__ == "__main__":
    debug_stat_structure()
