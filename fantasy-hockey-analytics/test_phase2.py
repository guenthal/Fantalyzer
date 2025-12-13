"""
Quick test script to verify Phase 2 implementation without requiring Yahoo API access.
This creates mock data and tests the database and analytics pipeline.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.models import TeamStats, Matchup, SeasonData
from src.database import init_db, save_season_data, get_weeks_stored, get_all_category_outcomes
from src.analytics import calculate_thresholds, calculate_all_thresholds, get_analysis_summary
from src.display import print_threshold_report, print_data_status


def create_mock_data():
    """Create mock season data for testing."""
    matchups = []
    
    # Create 5 weeks of data (3 complete, 2 incomplete)
    for week in range(1, 6):
        is_complete = week <= 3  # Weeks 1-3 complete, 4-5 incomplete
        
        # Create 5 matchups per week (10 team league)
        for matchup_num in range(5):
            team1 = TeamStats(
                team_name=f"Team {matchup_num*2 + 1}",
                manager_name=f"Manager {matchup_num*2 + 1}",
                goals=20 + week + matchup_num,
                assists=25 + week * 2,
                points=45 + week * 3,
                plus_minus=week - 2,
                pim=20 + matchup_num,
                ppp=10 + week,
                hits=100 + week * 10,
                shots=200 + week * 15,
                goalie_wins=3 if week % 2 == 0 else 2,
                save_pct=0.900 + (week * 0.01),
                gaa=2.50 - (week * 0.1)
            )
            
            team2 = TeamStats(
                team_name=f"Team {matchup_num*2 + 2}",
                manager_name=f"Manager {matchup_num*2 + 2}",
                goals=18 + week * 2,
                assists=22 + week,
                points=40 + week * 4,
                plus_minus=week - 3,
                pim=18 + matchup_num * 2,
                ppp=9 + week,
                hits=95 + week * 8,
                shots=190 + week * 12,
                goalie_wins=2 if week % 2 == 0 else 3,
                save_pct=0.895 + (week * 0.01),
                gaa=2.60 - (week * 0.08)
            )
            
            # Determine winners for each category
            category_winners = {
                'goals': team1.team_name if team1.goals > team2.goals else team2.team_name,
                'assists': team1.team_name if team1.assists > team2.assists else team2.team_name,
                'points': team1.team_name if team1.points > team2.points else team2.team_name,
                'plus_minus': team1.team_name if team1.plus_minus > team2.plus_minus else team2.team_name,
                'pim': team1.team_name if team1.pim > team2.pim else team2.team_name,
                'ppp': team1.team_name if team1.ppp > team2.ppp else team2.team_name,
                'hits': team1.team_name if team1.hits > team2.hits else team2.team_name,
                'shots': team1.team_name if team1.shots > team2.shots else team2.team_name,
                'goalie_wins': team1.team_name if team1.goalie_wins > team2.goalie_wins else team2.team_name,
                'save_pct': team1.team_name if team1.save_pct > team2.save_pct else team2.team_name,
                'gaa': team1.team_name if team1.gaa < team2.gaa else team2.team_name,  # Lower is better
            }
            
            matchup = Matchup(
                week=week,
                team1=team1,
                team2=team2,
                category_winners=category_winners,
                is_complete=is_complete
            )
            
            matchups.append(matchup)
    
    return SeasonData(
        league_id=99999,
        season="2025-2026 (Test)",
        matchups=matchups
    )


def test_database():
    """Test database operations."""
    print("\n" + "=" * 60)
    print("TEST 1: Database Persistence")
    print("=" * 60)
    
    # Clean start
    if os.path.exists("test_fantasy_hockey.db"):
        os.remove("test_fantasy_hockey.db")
    
    # Initialize DB
    init_db("test_fantasy_hockey.db")
    print("✓ Database initialized")
    
    # Create and save mock data
    season_data = create_mock_data()
    save_season_data(season_data, "test_fantasy_hockey.db")
    print(f"✓ Saved {len(season_data.matchups)} matchups")
    
    # Verify weeks stored
    weeks = get_weeks_stored("test_fantasy_hockey.db")
    print(f"✓ Retrieved {len(weeks)} weeks from database")
    
    complete_count = sum(1 for w in weeks if w['is_complete'])
    incomplete_count = len(weeks) - complete_count
    print(f"  - Complete weeks: {complete_count}")
    print(f"  - Incomplete weeks: {incomplete_count}")
    
    return True


def test_analytics():
    """Test analytics engine."""
    print("\n" + "=" * 60)
    print("TEST 2: Analytics Engine")
    print("=" * 60)
    
    # Calculate thresholds for goals category
    thresholds = calculate_thresholds('goals', "test_fantasy_hockey.db")
    print(f"✓ Calculated thresholds for Goals category")
    print(f"  - Sample size: {thresholds.sample_size}")
    print(f"  - Min winning: {thresholds.min_winning}")
    print(f"  - Median winning: {thresholds.median_winning}")
    print(f"  - Max losing: {thresholds.max_losing}")
    print(f"  - Overlap exists: {thresholds.overlap_exists}")
    
    # Calculate all thresholds
    all_thresholds = calculate_all_thresholds("test_fantasy_hockey.db")
    print(f"✓ Calculated thresholds for all {len(all_thresholds)} categories")
    
    # Get summary
    summary = get_analysis_summary("test_fantasy_hockey.db")
    print(f"✓ Analysis summary:")
    print(f"  - Weeks analyzed: {summary['weeks_analyzed']}")
    print(f"  - Weeks excluded: {summary['weeks_excluded']}")
    
    return True


def test_display():
    """Test display functions."""
    print("\n" + "=" * 60)
    print("TEST 3: Display Functions")
    print("=" * 60)
    
    # Test data status display
    weeks = get_weeks_stored("test_fantasy_hockey.db")
    print_data_status(weeks)
    
    # Test threshold report display
    thresholds = calculate_all_thresholds("test_fantasy_hockey.db")
    summary = get_analysis_summary("test_fantasy_hockey.db")
    print_threshold_report(thresholds, summary)
    
    return True


def test_gaa_direction():
    """Test that GAA is correctly handled as lower-is-better."""
    print("\n" + "=" * 60)
    print("TEST 4: GAA Direction-Aware Logic")
    print("=" * 60)
    
    thresholds = calculate_thresholds('gaa', "test_fantasy_hockey.db")
    
    print(f"✓ GAA thresholds calculated")
    print(f"  - Direction: {thresholds.direction}")
    assert thresholds.direction == 'lower_wins', "GAA should be 'lower_wins'"
    print(f"  ✓ Direction is correctly set to '{thresholds.direction}'")
    
    # In GAA, min_winning should be the LOWEST (best) GAA that won
    # and max_losing should be the HIGHEST (worst) GAA that lost
    print(f"  - Min winning GAA (best performance): {thresholds.min_winning:.3f}")
    print(f"  - Max losing GAA (worst performance): {thresholds.max_losing:.3f}")
    
    return True


def run_all_tests():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("PHASE 2 IMPLEMENTATION TEST SUITE")
    print("=" * 60)
    print("\nTesting without Yahoo API access using mock data...")
    
    try:
        # Run tests
        test_database()
        test_analytics()
        test_gaa_direction()
        test_display()
        
        # Success
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED")
        print("=" * 60)
        print("\nPhase 2 implementation is working correctly!")
        print("You can now run:")
        print("  - python main.py fetch     (requires Yahoo OAuth)")
        print("  - python main.py status")
        print("  - python main.py analyze")
        
        # Cleanup
        if os.path.exists("test_fantasy_hockey.db"):
            os.remove("test_fantasy_hockey.db")
            print("\n✓ Test database cleaned up")
        
        return 0
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ TEST FAILED")
        print("=" * 60)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(run_all_tests())
