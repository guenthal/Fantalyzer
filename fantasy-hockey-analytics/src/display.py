from .models import SeasonData, Matchup

def print_season_summary(data: SeasonData):
    current_week = 0
    print(f"\nSeason Summary: {data.season}")
    
    # Sort matchups by week
    sorted_matchups = sorted(data.matchups, key=lambda x: x.week)
    
    for m in sorted_matchups:
        if m.week != current_week:
            current_week = m.week
            print(f"\n=== Week {current_week} ===")
            
        print_matchup_detail(m)

def print_matchup_detail(m: Matchup):
    print(f"Matchup: {m.team1.team_name} vs {m.team2.team_name}")
    
    # Headers
    print(f"{'Category':<15} | {m.team1.team_name:<20} | {m.team2.team_name:<20} | Winner")
    print("-" * 75)
    
    # Categories
    # We'll use the STAT_MAPPING values implicitly or iteration
    # Since we don't have the mapping imported here, we can iterate our dataclass fields or hardcode
    categories = [
        ('Goals', 'goals'), ('Assists', 'assists'), ('Points', 'points'), 
        ('Plus/Minus', 'plus_minus'), ('PIM', 'pim'), ('PPP', 'ppp'), 
        ('Hits', 'hits'), ('Shots', 'shots'), ('Wins', 'goalie_wins'), 
        ('SV%', 'save_pct'), ('GAA', 'gaa')
    ]
    
    t1_wins = 0
    t2_wins = 0
    ties = 0
    
    for label, field in categories:
        v1 = getattr(m.team1, field)
        v2 = getattr(m.team2, field)
        winner = m.category_winners.get(field, "N/A") # look up using field name
        
        # Shorten winner for display
        if winner == m.team1.team_name:
            win_display = m.team1.team_name
            t1_wins += 1
        elif winner == m.team2.team_name:
            win_display = m.team2.team_name
            t2_wins += 1
        else:
            win_display = "Tie"
            ties += 1
            
        print(f"{label:<15} | {v1:<20} | {v2:<20} | {win_display}")
    
    print("-" * 75)
    result_str = f"Result: {m.team1.team_name} wins {t1_wins}-{t2_wins}-{ties}" if t1_wins > t2_wins else f"Result: {m.team2.team_name} wins {t2_wins}-{t1_wins}-{ties}"
    if t1_wins == t2_wins: result_str = f"Result: Tie {t1_wins}-{t2_wins}-{ties}"
    print(result_str)
    print("")
