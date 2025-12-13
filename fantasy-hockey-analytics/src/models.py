from dataclasses import dataclass, field
from typing import Dict, List, Optional

@dataclass
class TeamStats:
    team_name: str
    manager_name: str
    goals: int = 0
    assists: int = 0
    points: int = 0
    plus_minus: int = 0
    pim: int = 0
    ppp: int = 0
    hits: int = 0
    shots: int = 0
    goalie_wins: int = 0
    save_pct: float = 0.0
    gaa: float = 0.0

@dataclass
class Matchup:
    week: int
    team1: TeamStats
    team2: TeamStats
    category_winners: Dict[str, str] = field(default_factory=dict) # category_name -> winning_team_name
    is_complete: bool = False
    
    # Helper to print result summary (future use)
    def __str__(self):
        return f"Week {self.week}: {self.team1.team_name} vs {self.team2.team_name}"

@dataclass
class SeasonData:
    league_id: int
    season: str
    matchups: List[Matchup] = field(default_factory=list)
