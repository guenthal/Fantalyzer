"""Shared constants for the Fantasy Hockey Analytics application."""

# Map Yahoo Stat ID to our internal field names
ID_TO_FIELD = {
    1: 'goals',
    2: 'assists',
    3: 'points',
    4: 'plus_minus',
    5: 'pim',
    8: 'ppp',
    31: 'hits',
    14: 'shots',
    19: 'goalie_wins',
    26: 'save_pct',
    23: 'gaa'
}

# Categories where lower is better (use internal field names)
LOWER_IS_BETTER = {'gaa'}

# All stat categories in display order
ALL_CATEGORIES = [
    'goals', 'assists', 'points', 'plus_minus', 'pim', 
    'ppp', 'hits', 'shots', 'goalie_wins', 'save_pct', 'gaa'
]

# Display names for categories
CATEGORY_DISPLAY_NAMES = {
    'goals': 'Goals',
    'assists': 'Assists',
    'points': 'Points',
    'plus_minus': 'Plus/Minus',
    'pim': 'PIM',
    'ppp': 'PPP',
    'hits': 'Hits',
    'shots': 'Shots',
    'goalie_wins': 'Wins',
    'save_pct': 'SV%',
    'gaa': 'GAA'
}
