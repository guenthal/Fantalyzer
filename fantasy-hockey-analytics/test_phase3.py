"""
Test suite for Phase 3: Team Performance Analysis
Tests edge cases with mock data - no Yahoo API required.
"""

import sys
import os
import statistics

# Add src to path
sys.path.insert(0, os.path.dirname(__file__))

from src.models import TeamStats, Matchup, SeasonData
from src.database import (
    init_db, 
    save_season_data, 
    get_all_teams,
    get_team_by_id,
    team_exists,
    get_team_category_values,
    drop_all_tables
)
from src.team_analysis import (
    analyze_team, 
    has_goalie_data,
    calculate_trend,
    calculate_assessment,
    calculate_gap
)
from src.analytics import calculate_thresholds


def setup_test_database():
    """Create test database with mock data for edge cases."""
    db_path = "test_phase3.db"
    
    # Clean start
    if os.path.exists(db_path):
        os.remove(db_path)
    
    init_db(db_path)
    
    # Create mock season data with edge cases
    matchups = []
    
    # Create 9 complete weeks + 1 incomplete
    for week in range(1, 11):
        is_complete = week <= 9  # Weeks 1-9 complete, week 10 incomplete
        
        # 5 matchups per week (10 teams)
        for matchup_num in range(5):
            team1_id = matchup_num * 2 + 1
            team2_id = matchup_num * 2 + 2
            
            # Team 3 renamed in week 5
            team1_name = f"Team {team1_id}"
            team2_name = f"Team {team2_id}"
            if team1_id == 3 and week >= 5:
                team1_name = "New Name FC"  # Renamed!
            if team2_id == 3 and week >= 5:
                team2_name = "New Name FC"  # Renamed!
            
            # Team 1: Strong in goals, weak in GAA
            # Team 2: Weak overall
            # Team 3: Renamed mid-season, competitive
            # Team 4: Zero goalie data (Dana never starts goalies)
            # Team 5: Only in weeks 8-9 (new team, insufficient trend data)
            # Team 6: All categories tied in week 5
            
            if team1_id == 5 or team2_id == 5:
                if week < 8:
                    continue  # Team 5 doesn't exist yet
            
            # Build team stats
            team1 = TeamStats(
                team_id= team1_id,
                team_name=team1_name,
                manager_name=f"Manager {team1_id}",
                goals=25 + week + (team1_id * 2) if team1_id != 2 else 15 + week,  # Team 2 weak
                assists=30 + week if team1_id != 2 else 20 + week,
                points=55 + week * 2 if team1_id != 2 else 35 + week,
                plus_minus=week - 2 if team1_id != 2 else week - 5,
                pim=22 + matchup_num if (team1_id, week) != (1, 5) else 20,  # Team 1 ties in week 5
                ppp=12 + week if team1_id != 2 else 8 + week,
                hits=120 + week * 8 if team1_id != 2 else 80 + week * 5,
                shots=220 + week * 10 if team1_id != 2 else 150 + week * 8,
                goalie_wins=3 if week % 2 == 0 and team1_id != 4 else (2 if team1_id != 4 else 0),
                save_pct=0.910 + (week * 0.005) if team1_id != 4 else 0.0,  # Team 4: no goalie
                gaa=2.80 - (week * 0.05) if team1_id != 1 and team1_id != 4 else (3.20 - week * 0.02 if team1_id == 1 else 0.0)  # Team 1 weak in GAA
            )
            
            team2 = TeamStats(
                team_id=team2_id,
                team_name=team2_name,
                manager_name=f"Manager {team2_id}",
                goals=22 + week + matchup_num,
                assists=28 + week,
                points=50 + week * 2,
                plus_minus=week - 3,
                pim=20 + matchup_num * 2 if (team2_id, week) != (2, 5) else 20,  # Team 2 ties in week 5
                ppp=10 + week,
                hits=110 + week * 7,
                shots=210 + week * 9,
                goalie_wins=2 if week % 2 == 0 and team2_id != 4 else (3 if team2_id != 4 else 0),
                save_pct=0.905 + (week * 0.005) if team2_id != 4 else 0.0,  # Team 4: no goalie
                gaa=2.70 - (week * 0.05) if team2_id != 4 else 0.0  # Team 4: no goalie
            )
            
            # Determine winners
            category_winners = {
                'goals': team1.team_name if team1.goals > team2.goals else team2.team_name,
                'assists': team1.team_name if team1.assists > team2.assists else team2.team_name,
               'points': team1.team_name if team1.points > team2.points else team2.team_name,
                'plus_minus': team1.team_name if team1.plus_minus > team2.plus_minus else team2.team_name,
                'pim': "Tie" if team1.pim == team2.pim else (team1.team_name if team1.pim > team2.pim else team2.team_name),
                'ppp': team1.team_name if team1.ppp > team2.ppp else team2.team_name,
                'hits': team1.team_name if team1.hits > team2.hits else team2.team_name,
                'shots': team1.team_name if team1.shots > team2.shots else team2.team_name,
                'goalie_wins': team1.team_name if team1.goalie_wins > team2.goalie_wins else team2.team_name,
                'save_pct': team1.team_name if team1.save_pct > team2.save_pct else team2.team_name,
                'gaa': team1.team_name if team1.gaa < team2.gaa and team1.gaa > 0 else (team2.team_name if team2.gaa > 0 else "Tie"),
            }
            
            matchup = Matchup(
                week=week,
                team1=team1,
                team2=team2,
                category_winners=category_winners,
                is_complete=is_complete
            )
            
            matchups.append(matchup)
    
    season_data = SeasonData(
        league_id=99999,
        season="2025-2026 (Phase 3 Test)",
        matchups=matchups
    )
    
    save_season_data(season_data, db_path)
    return db_path


def cleanup_test_database():
    """Clean up test database."""
    db_path = "test_phase3.db"
    if os.path.exists(db_path):
        os.remove(db_path)


def test_team_rename():
    """Verify analysis works for team that renamed mid-season."""
    print("\n=== Test: Team Rename Handling ===")
    
    db_path = "test_phase3.db"
    
    # Team 3 renamed in week 5
    team = get_team_by_id(3, db_path)
    assert team is not None, "Team 3 should exist"
    assert team['current_name'] == "New Name FC", f"Expected 'New Name FC', got '{team['current_name']}'"
    
    # Analysis should include all weeks
    result = analyze_team(3, db_path)
    assert result.weeks_analyzed == 9, f"Expected 9 weeks, got {result.weeks_analyzed}"
    assert result.team_name == "New Name FC", "Should show current name"
    
    print("  ✓ Team rename handled correctly")
    print(f"    - Current name: {result.team_name}")
    print(f"    - Weeks analyzed: {result.weeks_analyzed}")


def test_zero_goalie_data():
    """Verify GAA/SV% show 'No Data' when all zeros."""
    print("\n=== Test: Zero Goalie Data Detection ===")
    
    db_path = "test_phase3.db"
    result = analyze_team(4, db_path)
    
    assert result.assessments['gaa'].assessment == 'no_data', \
        f"GAA should be 'no_data', got '{result.assessments['gaa'].assessment}'"
    assert result.assessments['save_pct'].assessment == 'no_data', \
        f"SV% should be 'no_data', got '{result.assessments['save_pct'].assessment}'"
    
    # Should not appear in improvement priorities
    priority_categories = [p[0] for p in result.improvement_priorities]
    assert 'gaa' not in priority_categories, "GAA should not be in improvement priorities"
    assert 'save_pct' not in priority_categories, "SV% should not be in improvement priorities"
    
    print("  ✓ Zero goalie data detected")
    print(f"    - GAA assessment: {result.assessments['gaa'].assessment}")
    print(f"    - SV% assessment: {result.assessments['save_pct'].assessment}")


def test_insufficient_trend_data():
    """Verify trend shows 'insufficient_data' with < 4 weeks."""
    print("\n=== Test: Insufficient Trend Data ===")
    
    db_path = "test_phase3.db"
    
    # Team 5 only in weeks 8-9 (2 weeks)
    result = analyze_team(5, db_path)
    
    for category, assessment in result.assessments.items():
        if assessment.weeks_played > 0 and assessment.assessment != 'no_data':
            assert assessment.trend == 'insufficient_data', \
                f"{category} trend should be 'insufficient_data', got '{assessment.trend}'"
    
    print("  ✓ Insufficient trend data handling")
    print(f"    - Weeks played: {result.weeks_analyzed}")
    print(f"    - All trends: insufficient_data")


def test_gaa_direction():
    """Verify GAA assessment is inverted (low = good)."""
    print("\n=== Test: GAA Direction-Aware Logic ===")
    
    db_path = "test_phase3.db"
    
    # Team 1 has high GAA (weak performance)
    result = analyze_team(1, db_path)
    
    gaa = result.assessments['gaa']
    assert gaa.direction == 'lower_wins', f"GAA direction should be 'lower_wins', got '{gaa.direction}'"
    
    # For GAA, if team average is ABOVE median, gap should be NEGATIVE
    if gaa.team_average > gaa.threshold_median:
        assert gaa.gap < 0, f"GAA gap should be negative when above median, got {gaa.gap}"
        assert gaa.assessment in ['weak', 'critical'], \
            f"High GAA should be weak/critical, got '{gaa.assessment}'"
    
    print("  ✓ GAA direction-aware logic working")
    print(f"    - Direction: {gaa.direction}")
    print(f"    - Team avg: {gaa.team_average:.3f}")
    print(f"    - Median: {gaa.threshold_median:.3f}")
    print(f"    - Gap: {gaa.gap:.3f}")
    print(f"    - Assessment: {gaa.assessment}")


def test_gap_sign_convention():
    """Verify gap is positive when performance is good."""
    print("\n=== Test: Gap Sign Convention ===")
    
    db_path = "test_phase3.db"
    result = analyze_team(1, db_path)
    
    # For 'higher wins' categories
    goals = result.assessments['goals']
    if goals.team_average > goals.threshold_median:
        assert goals.gap > 0, "Gap should be positive when above median (higher wins)"
        print(f"  ✓ Goals (higher wins): avg={goals.team_average:.1f}, median={goals.threshold_median:.1f}, gap={goals.gap:+.1f}")
    
    # For GAA (lower wins)
    gaa = result.assessments['gaa']
    if gaa.team_average < gaa.threshold_median:
        assert gaa.gap > 0, "Gap should be positive when below median (lower wins)"
        print(f"  ✓ GAA (lower wins): avg={gaa.team_average:.3f}, median={gaa.threshold_median:.3f}, gap={gaa.gap:+.3f}")


def test_improvement_priorities_sorted():
    """Verify priorities are sorted by gap (most negative first)."""
    print("\n=== Test: Improvement Priorities Sorting ===")
    
    db_path = "test_phase3.db"
    result = analyze_team(2, db_path)  # Team 2 is weak overall
    
    priorities = result.improvement_priorities
    if len(priorities) > 1:
        gaps = [p[1] for p in priorities]
        assert gaps == sorted(gaps), "Priorities should be sorted by gap (ascending)"
        print(f"  ✓ Priorities sorted correctly")
        print(f"    - Most urgent: {priorities[0][0]} (gap: {priorities[0][1]:.2f})")
        print(f"    - Total priorities: {len(priorities)}")


def test_assessment_buckets():
    """Verify assessment thresholds work correctly."""
    print("\n=== Test: Assessment Bucket Thresholds ===")
    
    from src.analytics import calculate_all_thresholds
    
    db_path = "test_phase3.db"
    thresholds = calculate_all_thresholds(db_path)
    
    # Test calculate_assessment function
    from src.team_analysis import calculate_assessment
    
    threshold = thresholds['goals']
    
    # Test dominant (above p75)
    assessment = calculate_assessment(threshold.p75_winning + 5, threshold, 'higher_wins')
    assert assessment == 'dominant', f"Expected 'dominant', got '{assessment}'"
    
    # Test strong (above median, below p75)
    mid_value = (threshold.median_winning + threshold.p75_winning) / 2
    assessment = calculate_assessment(mid_value, threshold, 'higher_wins')
    assert assessment == 'strong', f"Expected 'strong', got '{assessment}'"
    
    # Test critical (well below min)
    assessment = calculate_assessment(threshold.min_winning * 0.5, threshold, 'higher_wins')
    assert assessment == 'critical', f"Expected 'critical', got '{assessment}'"
    
    print("  ✓ Assessment buckets working correctly")


def test_empty_database():
    """Verify graceful handling of empty database."""
    print("\n=== Test: Empty Database Handling ===")
    
    db_path = "test_empty.db"
    if os.path.exists(db_path):
        os.remove(db_path)
    
    init_db(db_path)
    
    teams = get_all_teams(db_path)
    assert teams == [], "Empty DB should have no teams"
    
    exists = team_exists(1, db_path)
    assert not exists, "Team should not exist in empty DB"
    
    os.remove(db_path)
    print("  ✓ Empty database handled gracefully")


def test_team_not_found():
    """Verify error handling for invalid team ID."""
    print("\n=== Test: Team Not Found Handling ===")
    
    db_path = "test_phase3.db"
    
    exists = team_exists(999, db_path)
    assert not exists, "Team 999 should not exist"
    
    try:
        result = analyze_team(999, db_path)
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "not found" in str(e).lower(), "Error message should mention 'not found'"
        print("  ✓ Team not found error handled correctly")


def test_has_goalie_data_function():
    """Test the has_goalie_data helper function."""
    print("\n=== Test: has_goalie_data Function ===")
    
    # Non-goalie stats always have data
    assert has_goalie_data([10, 20, 30], 'goals') == True
    
    # All zeros for goalie stats = no data
    assert has_goalie_data([0.0, 0.0, 0.0], 'gaa') == False
    assert has_goalie_data([0.0, 0.0, 0.0], 'save_pct') == False
    
    # Some non-zero values = has data
    assert has_goalie_data([2.5, 2.3, 0.0], 'gaa') == True
    assert has_goalie_data([0.910, 0.0, 0.915], 'save_pct') == True
    
    print("  ✓ has_goalie_data function working")


def test_trend_calculation():
    """Test trend calculation logic."""
    print("\n=== Test: Trend Calculation ===")
    
    # Improving (for higher wins)
    trend = calculate_trend([20, 22, 24, 28, 30, 32], 'higher_wins')
    assert trend == 'improving', f"Expected 'improving', got '{trend}'"
    
    # Declining (for higher wins)
    trend = calculate_trend([30, 28, 26, 24, 22, 20], 'higher_wins')
    assert trend == 'declining', f"Expected 'declining', got '{trend}'"
    
    # Stable
    trend = calculate_trend([25, 26, 24, 25, 26, 24], 'higher_wins')
    assert trend == 'stable', f"Expected 'stable', got '{trend}'"
    
    # Insufficient data
    trend = calculate_trend([25, 26], 'higher_wins')
    assert trend == 'insufficient_data', f"Expected 'insufficient_data', got '{trend}'"
    
    # GAA: declining average = improving
    trend = calculate_trend([3.0, 2.8, 2.6, 2.4, 2.2, 2.0], 'lower_wins')
    assert trend == 'improving', f"For GAA, declining values should be 'improving', got '{trend}'"
    
    print("  ✓ Trend calculation working correctly")


def run_all_tests():
    """Run all Phase 3 tests."""
    print("=" * 70)
    print("PHASE 3 TEST SUITE: Team Performance Analysis")
    print("=" * 70)
    print("\nSetting up test database with mock data...")
    
    try:
        # Setup test database
        db_path = setup_test_database()
        print(f"✓ Test database created: {db_path}")
        
        # Run tests
        test_team_rename()
        test_zero_goalie_data()
        test_insufficient_trend_data()
        test_gaa_direction()
        test_gap_sign_convention()
        test_improvement_priorities_sorted()
        test_assessment_buckets()
        test_empty_database()
        test_team_not_found()
        test_has_goalie_data_function()
        test_trend_calculation()
        
        # Success
        print("\n" + "=" * 70)
        print("✅ ALL PHASE 3 TESTS PASSED")
        print("=" * 70)
        print("\nPhase 3 implementation is working correctly!")
        print("\nYou can now run:")
        print("  - python main.py migrate      (upgrade schema)")
        print("  - python main.py fetch        (populate with real data)")
        print("  - python main.py team --list  (see all teams)")
        print("  - python main.py team --id X  (analyze specific team)")
        
        return 0
        
    except AssertionError as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"\nAssertion Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    except Exception as e:
        print("\n" + "=" * 70)
        print("❌ TEST FAILED")
        print("=" * 70)
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    finally:
        print("\n✓ Cleaning up test database...")
        cleanup_test_database()


if __name__ == "__main__":
    sys.exit(run_all_tests())
