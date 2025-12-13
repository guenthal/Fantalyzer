from typing import Dict, List
from .models import SeasonData, Matchup
from .constants import CATEGORY_DISPLAY_NAMES, ALL_CATEGORIES, LOWER_IS_BETTER

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


def print_threshold_report(thresholds: Dict[str, 'CategoryThresholds'], summary: dict):
    """Display a table showing winning thresholds per category with analysis metadata."""
    
    # Check if we have any data
    if summary['weeks_analyzed'] == 0:
        print("\n" + "=" * 80)
        print("Insufficient Data")
        print("=" * 80)
        print("No completed weeks available for analysis.")
        if summary['weeks_excluded'] > 0:
            print(f"Week(s) {', '.join(map(str, summary['incomplete_week_numbers']))} in progress - excluded from analysis")
        print("=" * 80)
        return
    
    # Build header
    print("\n" + "=" * 80)
    print("League Winning Thresholds")
    print("=" * 80)
    
    # Analysis period info
    week_nums = summary['complete_week_numbers']
    if week_nums:
        week_range = f"Weeks {min(week_nums)}-{max(week_nums)}" if len(week_nums) > 1 else f"Week {week_nums[0]}"
        print(f"Analysis Period: {week_range} ({summary['weeks_analyzed']} complete weeks, ~{summary['total_matchups']} matchups)")
    
    if summary['weeks_excluded'] > 0:
        incomplete_str = ', '.join(map(str, summary['incomplete_week_numbers']))
        print(f"Week(s) {incomplete_str} in progress - excluded from analysis")
    
    print("-" * 80)
    
    # Table header
    print(f"{'Category':<12} {'Dir':<6} {'Min Win':<10} {'Median':<10} {'75th %':<10} {'Max Lose':<10} {'Overlap Zone':<15}")
    print("-" * 80)
    
    # Print each category
    for category in ALL_CATEGORIES:
        threshold = thresholds.get(category)
        if not threshold or threshold.sample_size == 0:
            continue
        
        display_name = CATEGORY_DISPLAY_NAMES.get(category, category)
        direction = "Lower" if category in LOWER_IS_BETTER else "Higher"
        
        # Format values based on category type
        if category in ['save_pct', 'gaa']:
            min_win = f"{threshold.min_winning:.3f}"
            median = f"{threshold.median_winning:.3f}"
            p75 = f"{threshold.p75_winning:.3f}"
            max_lose = f"{threshold.max_losing:.3f}"
            
            if threshold.overlap_exists:
                overlap = f"{threshold.overlap_low:.3f}-{threshold.overlap_high:.3f}"
            else:
                overlap = "None"
        else:
            min_win = f"{int(threshold.min_winning)}"
            median = f"{int(threshold.median_winning)}"
            p75 = f"{int(threshold.p75_winning)}"
            max_lose = f"{int(threshold.max_losing)}"
            
            if threshold.overlap_exists:
                overlap = f"{int(threshold.overlap_low)}-{int(threshold.overlap_high)}"
            else:
                overlap = "None"
        
        print(f"{display_name:<12} {direction:<6} {min_win:<10} {median:<10} {p75:<10} {max_lose:<10} {overlap:<15}")
    
    print("-" * 80)
    print("\nNote: 'Overlap Zone' = range where both wins and losses occurred.")
    print("      Above the zone (or below for GAA) = likely win.")
    print("      Below the zone (or above for GAA) = likely loss.")
    print("=" * 80)


def print_data_status(weeks: List[dict]):
    """Show which weeks are stored and their completion status."""
    
    if not weeks:
        print("\nNo data stored in database.")
        return
    
    print("\n" + "=" * 60)
    print("Database Status")
    print("=" * 60)
    
    complete_weeks = [w for w in weeks if w['is_complete']]
    incomplete_weeks = [w for w in weeks if not w['is_complete']]
    
    print(f"Total weeks stored: {len(weeks)}")
    print(f"Complete weeks: {len(complete_weeks)}")
    print(f"Incomplete weeks: {len(incomplete_weeks)}")
    print("-" * 60)
    
    # Show week details
    for week in weeks:
        status = "✓ Complete" if week['is_complete'] else "⏳ In Progress"
        print(f"Week {week['week']}: {status}")
    
    print("=" * 60)


def print_fetch_summary(season_data: SeasonData):
    """Display summary of fetched data showing complete vs incomplete weeks."""
    
    # Group by week
    weeks_info = {}
    for matchup in season_data.matchups:
        week_num = matchup.week
        if week_num not in weeks_info:
            weeks_info[week_num] = {'count': 0, 'complete': True}
        weeks_info[week_num]['count'] += 1
        if not matchup.is_complete:
            weeks_info[week_num]['complete'] = False
    
    print("\n" + "=" * 60)
    print("Fetch Summary")
    print("=" * 60)
    
    for week_num in sorted(weeks_info.keys()):
        info = weeks_info[week_num]
        status = "complete" if info['complete'] else "in progress"
        print(f"Week {week_num}: {info['count']} matchups ({status})")
    
    complete_count = sum(1 for info in weeks_info.values() if info['complete'])
    incomplete_count = len(weeks_info) - complete_count
    
    print("-" * 60)
    print(f"Summary: {len(weeks_info)} weeks stored ({complete_count} complete, {incomplete_count} in progress)")
    print("=" * 60)
