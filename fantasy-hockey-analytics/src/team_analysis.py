"""Team-specific performance analysis engine."""

import statistics
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional
from .database import (
    get_team_by_id, 
    get_team_category_values,
    team_exists
)
from .analytics import calculate_all_thresholds, CategoryThresholds
from .constants import ALL_CATEGORIES, LOWER_IS_BETTER


@dataclass
class CategoryAssessment:
    """Assessment of a team's performance in a single category."""
    category: str
    direction: str  # 'higher_wins' or 'lower_wins'
    
    # Team's performance
    team_average: float
    weeks_played: int
    weekly_values: List[float]
    
    # Threshold comparison
    threshold_median: float
    threshold_p75: float
    threshold_min_winning: float
    
    # Analysis results  
    gap: float  # Positive = good (above threshold, or below for GAA)
    win_rate: float  # 0.0 to 1.0, or -1 if undefined (all ties)
    wins: int
    losses: int
    ties: int
    
    # Qualitative
    assessment: str  # 'dominant', 'strong', 'competitive', 'weak', 'critical', 'no_data'
    trend: str  # 'improving', 'stable', 'declining', 'insufficient_data'


@dataclass 
class TeamAnalysisResult:
    """Complete analysis for a team."""
    team_id: int
    team_name: str
    weeks_analyzed: int
    assessments: Dict[str, CategoryAssessment]
    improvement_priorities: List[Tuple[str, float]]  # (category, gap) sorted by priority
    strengths: List[Tuple[str, str]]  # (category, assessment) for strong/dominant


def has_goalie_data(weekly_values: List[float], category: str) -> bool:
    """Returns False if this looks like zero goalie starts."""
    if category not in ['gaa', 'save_pct']:
        return True
    # All zeros = no goalie data
    if not weekly_values:
        return False
    return not all(v == 0.0 for v in weekly_values)


def calculate_trend(weekly_values: List[float], direction: str) -> str:
    """Calculate performance trend from weekly values."""
    if len(weekly_values) < 4:
        return 'insufficient_data'
    
    early_avg = statistics.mean(weekly_values[:3])
    recent_avg = statistics.mean(weekly_values[-3:])
    
    # Avoid division by zero
    if early_avg == 0:
        if recent_avg == 0:
            return 'stable'
        # Going from 0 to positive
        return 'improving' if recent_avg > 0 else 'stable'
    
    change_pct = (recent_avg - early_avg) / abs(early_avg)
    
    # For GAA, declining average is actually improving
    if direction == 'lower_wins':
        change_pct = -change_pct
    
    if change_pct > 0.10:
        return 'improving'
    elif change_pct < -0.10:
        return 'declining'
    else:
        return 'stable'


def calculate_assessment(team_avg: float, threshold: CategoryThresholds, direction: str) -> str:
    """Determine qualitative assessment based on threshold comparison."""
    
    if direction == 'higher_wins':
        # For categories where higher is better
        if team_avg >= threshold.p75_winning:
            return 'dominant'
        elif team_avg >= threshold.median_winning:
            return 'strong'
        elif team_avg >= threshold.min_winning:
            return 'competitive'
        elif team_avg >= threshold.min_winning * 0.85:
            return 'weak'
        else:
            return 'critical'
    else:
        # For GAA (lower is better) - invert comparisons
        if team_avg <= threshold.p75_winning:  # p75 for GAA is a LOW number
            return 'dominant'
        elif team_avg <= threshold.median_winning:
            return 'strong'
        elif team_avg <= threshold.max_winning:
            return 'competitive'
        elif team_avg <= threshold.max_winning * 1.15:
            return 'weak'
        else:
            return 'critical'


def calculate_gap(team_avg: float, threshold_median: float, direction: str) -> float:
    """
    Calculate gap from median threshold.
    Positive gap = good performance
    Negative gap = below threshold
    """
    if direction == 'higher_wins':
        gap = team_avg - threshold_median  # Positive = good
    else:  # GAA - lower is better
        gap = threshold_median - team_avg  # Positive = good (you're below median)
    
    return gap


def analyze_category(team_id: int, category: str,
                     threshold: CategoryThresholds,
                     db_path: str = "fantasy_hockey.db") -> CategoryAssessment:
    """Analyze single category for a team."""
    
    # Get team's weekly values for this category
    values_data = get_team_category_values(team_id, category, complete_only=True, db_path=db_path)
    
    if not values_data:
        # No data for this category
        return CategoryAssessment(
            category=category,
            direction=threshold.direction,
            team_average=0.0,
            weeks_played=0,
            weekly_values=[],
            threshold_median=threshold.median_winning,
            threshold_p75=threshold.p75_winning,
            threshold_min_winning=threshold.min_winning,
            gap=0.0,
            win_rate=-1,
            wins=0,
            losses=0,
            ties=0,
            assessment='no_data',
            trend='insufficient_data'
        )
    
    # Extract weekly values and win/loss record
    weekly_values = [v['team_value'] for v in values_data]
    wins = sum(1 for v in values_data if v['won'] == 1)
    losses = sum(1 for v in values_data if v['won'] == 0)
    ties = sum(1 for v in values_data if v['won'] is None)
    
    # Check for zero goalie data
    if not has_goalie_data(weekly_values, category):
        return CategoryAssessment(
            category=category,
            direction=threshold.direction,
            team_average=0.0,
            weeks_played=len(weekly_values),
            weekly_values=weekly_values,
            threshold_median=threshold.median_winning,
            threshold_p75=threshold.p75_winning,
            threshold_min_winning=threshold.min_winning,
            gap=0.0,
            win_rate=-1,
            wins=0,
            losses=0,
            ties=0,
            assessment='no_data',
            trend='insufficient_data'
        )
    
    # Calculate team average
    team_average = statistics.mean(weekly_values)
    
    # Calculate win rate
    total_decisions = wins + losses
    win_rate = wins / total_decisions if total_decisions > 0 else -1
    
    # Calculate gap
    gap = calculate_gap(team_average, threshold.median_winning, threshold.direction)
    
    # Determine assessment
    assessment = calculate_assessment(team_average, threshold, threshold.direction)
    
    # Calculate trend
    trend = calculate_trend(weekly_values, threshold.direction)
    
    return CategoryAssessment(
        category=category,
        direction=threshold.direction,
        team_average=team_average,
        weeks_played=len(weekly_values),
        weekly_values=weekly_values,
        threshold_median=threshold.median_winning,
        threshold_p75=threshold.p75_winning,
        threshold_min_winning=threshold.min_winning,
        gap=gap,
        win_rate=win_rate,
        wins=wins,
        losses=losses,
        ties=ties,
        assessment=assessment,
        trend=trend
    )


def get_improvement_priorities(assessments: Dict[str, CategoryAssessment]) -> List[Tuple[str, float]]:
    """
    Return (category, gap) tuples sorted by priority.
    
    Only include categories with negative gap (below threshold).
    Sort by gap ascending (most negative = highest priority).
    Exclude 'no_data' categories.
    """
    priorities = []
    
    for category, assessment in assessments.items():
        # Skip categories with no data
        if assessment.assessment == 'no_data':
            continue
        
        # Only include if below threshold (negative gap)
        if assessment.gap < 0:
            priorities.append((category, assessment.gap))
    
    # Sort by gap ascending (most negative first)
    priorities.sort(key=lambda x: x[1])
    
    return priorities


def identify_strengths(assessments: Dict[str, CategoryAssessment]) -> List[Tuple[str, str]]:
    """Return list of (category, assessment) for strong/dominant categories."""
    strengths = []
    
    for category, assessment in assessments.items():
        if assessment.assessment in ['strong', 'dominant']:
            strengths.append((category, assessment.assessment))
    
    # Sort by assessment (dominant first, then strong)
    strengths.sort(key=lambda x: 0 if x[1] == 'dominant' else 1)
    
    return strengths


def analyze_team(team_id: int, db_path: str = "fantasy_hockey.db") -> TeamAnalysisResult:
    """
    Full team analysis.
    
    1. Verify team exists
    2. Get thresholds via calculate_all_thresholds()
    3. For each category, call analyze_category()
    4. Compute improvement_priorities (sorted by negative gap)
    5. Identify strengths (dominant/strong categories)
    """
    
    # Verify team exists
    team = get_team_by_id(team_id, db_path)
    if not team:
        raise ValueError(f"Team ID {team_id} not found in database")
    
    # Get league-wide thresholds
    thresholds = calculate_all_thresholds(db_path)
    
    # Check if we have any threshold data
    if not thresholds or all(t.sample_size == 0 for t in thresholds.values()):
        raise ValueError("No threshold data available. Need at least one completed week.")
    
    # Analyze each category
    assessments = {}
    for category in ALL_CATEGORIES:
        threshold = thresholds[category]
        assessment = analyze_category(team_id, category, threshold, db_path)
        assessments[category] = assessment
    
    # Calculate weeks analyzed (use max weeks from any category)
    weeks_analyzed = max(
        (a.weeks_played for a in assessments.values() if a.weeks_played > 0),
        default=0
    )
    
    # Get improvement priorities
    improvement_priorities = get_improvement_priorities(assessments)
    
    # Identify strengths
    strengths = identify_strengths(assessments)
    
    return TeamAnalysisResult(
        team_id=team_id,
        team_name=team['current_name'],
        weeks_analyzed=weeks_analyzed,
        assessments=assessments,
        improvement_priorities=improvement_priorities,
        strengths=strengths
    )
