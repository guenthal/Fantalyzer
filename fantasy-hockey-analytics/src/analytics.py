"""Analytical engine for calculating winning thresholds across stat categories."""

import statistics
from dataclasses import dataclass
from typing import Dict, List
from .database import get_all_category_outcomes, get_weeks_stored
from .constants import ALL_CATEGORIES, LOWER_IS_BETTER


@dataclass
class CategoryThresholds:
    """Threshold metrics for a single stat category."""
    category: str
    direction: str  # 'higher_wins' or 'lower_wins'
    sample_size: int  # number of non-tie outcomes from complete weeks
    weeks_analyzed: int  # number of complete weeks included
    min_winning: float
    max_winning: float
    median_winning: float
    p75_winning: float
    p90_winning: float
    max_losing: float
    min_losing: float
    overlap_exists: bool
    overlap_low: float   # lower bound of uncertain zone
    overlap_high: float  # upper bound of uncertain zone


def calculate_thresholds(category: str, db_path: str = "fantasy_hockey.db") -> CategoryThresholds:
    """Calculate all threshold metrics for a single category using complete weeks only."""
    
    # Get all completed outcomes for this category
    outcomes = get_all_category_outcomes(category, complete_only=True, db_path=db_path)
    
    # Filter out ties and gather winning/losing values
    winning_values = []
    losing_values = []
    
    for outcome in outcomes:
        # In new schema, winner_team_id is NULL for ties
        if outcome['winner_team_id'] is not None:
            winning_values.append(outcome['winning_value'])
            losing_values.append(outcome['losing_value'])
    
    # Count weeks analyzed
    weeks_analyzed = len(set(outcome['week_number'] for outcome in outcomes))
    
    # Require at least some data
    if not winning_values:
        # Return empty thresholds if no data
        direction = 'lower_wins' if category in LOWER_IS_BETTER else 'higher_wins'
        return CategoryThresholds(
            category=category,
            direction=direction,
            sample_size=0,
            weeks_analyzed=0,
            min_winning=0.0,
            max_winning=0.0,
            median_winning=0.0,
            p75_winning=0.0,
            p90_winning=0.0,
            max_losing=0.0,
            min_losing=0.0,
            overlap_exists=False,
            overlap_low=0.0,
            overlap_high=0.0
        )
    
    # Calculate metrics
    direction = 'lower_wins' if category in LOWER_IS_BETTER else 'higher_wins'
    sample_size = len(winning_values)
    
    min_winning = min(winning_values)
    max_winning = max(winning_values)
    median_winning = statistics.median(winning_values)
    
    # Calculate percentiles
    sorted_winning = sorted(winning_values)
    p75_idx = int(len(sorted_winning) * 0.75)
    p90_idx = int(len(sorted_winning) * 0.90)
    p75_winning = sorted_winning[p75_idx] if p75_idx < len(sorted_winning) else max_winning
    p90_winning = sorted_winning[p90_idx] if p90_idx < len(sorted_winning) else max_winning
    
    max_losing = max(losing_values)
    min_losing = min(losing_values)
    
    # Calculate overlap zone
    if direction == 'higher_wins':
        # In higher_wins categories, overlap exists if max_losing >= min_winning
        overlap_exists = max_losing >= min_winning
        overlap_low = min_winning if overlap_exists else 0.0
        overlap_high = max_losing if overlap_exists else 0.0
    else:  # lower_wins (e.g., GAA)
        # In lower_wins categories, overlap exists if min_losing <= max_winning
        overlap_exists = min_losing <= max_winning
        overlap_low = min_losing if overlap_exists else 0.0
        overlap_high = max_winning if overlap_exists else 0.0
    
    return CategoryThresholds(
        category=category,
        direction=direction,
        sample_size=sample_size,
        weeks_analyzed=weeks_analyzed,
        min_winning=min_winning,
        max_winning=max_winning,
        median_winning=median_winning,
        p75_winning=p75_winning,
        p90_winning=p90_winning,
        max_losing=max_losing,
        min_losing=min_losing,
        overlap_exists=overlap_exists,
        overlap_low=overlap_low,
        overlap_high=overlap_high
    )


def calculate_all_thresholds(db_path: str = "fantasy_hockey.db") -> Dict[str, CategoryThresholds]:
    """Calculate thresholds for all categories. Returns dict keyed by category name."""
    thresholds = {}
    
    for category in ALL_CATEGORIES:
        thresholds[category] = calculate_thresholds(category, db_path)
    
    return thresholds


def get_analysis_summary(db_path: str = "fantasy_hockey.db") -> dict:
    """Return metadata: weeks_analyzed, weeks_excluded, total_matchups, date_range."""
    weeks = get_weeks_stored(db_path)
    
    complete_weeks = [w for w in weeks if w['is_complete']]
    incomplete_weeks = [w for w in weeks if not w['is_complete']]
    
    # Calculate total matchups from complete weeks
    # Note: This is a rough estimate (5 matchups per week for a 10-team league)
    # We could query the database for exact count if needed
    total_matchups = len(complete_weeks) * 5  # Approximate
    
    return {
        'weeks_analyzed': len(complete_weeks),
        'weeks_excluded': len(incomplete_weeks),
        'total_matchups': total_matchups,
        'complete_week_numbers': [w['week'] for w in complete_weeks],
        'incomplete_week_numbers': [w['week'] for w in incomplete_weeks]
    }
