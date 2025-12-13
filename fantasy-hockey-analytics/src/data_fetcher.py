from typing import Dict
from yfpy.query import YahooFantasySportsQuery
from .models import TeamStats, Matchup, SeasonData
import logging

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

logger = logging.getLogger(__name__)

class DataFetcher:
    def __init__(self, query: YahooFantasySportsQuery, league_id: str):
        self.query = query
        self.league_id = league_id
        
    def get_game_id(self, season: int) -> str:
        """Finds the Yahoo Game ID for the specified NHL season."""
        return self.query.get_game_key_by_season(season)

    def fetch_season_data(self, game_id: str, start_week: int, end_week: int) -> SeasonData:
        all_matchups = []
        
        for week in range(start_week, end_week + 1):
            logger.info(f"Fetching week {week}...")
            try:
                yfpy_matchups = self.query.get_league_matchups_by_week(chosen_week=week)
                
                for m in yfpy_matchups:
                    processed_matchup = self._process_matchup(m, week)
                    all_matchups.append(processed_matchup)
                    
            except Exception as e:
                logger.error(f"Error fetching week {week}: {e}")
                
        return SeasonData(
            league_id=int(self.league_id),
            season="2025-2026", 
            matchups=all_matchups
        )

    def _process_matchup(self, yfpy_matchup, week: int) -> Matchup:
        t1_raw = yfpy_matchup.teams[0]
        t2_raw = yfpy_matchup.teams[1]
        
        t1_stats = self._extract_stats(t1_raw)
        t2_stats = self._extract_stats(t2_raw)
        
        winners = self._determine_winners(t1_stats, t2_stats)
        
        is_complete = str(yfpy_matchup.status) == 'postevent'
        
        return Matchup(
            week=week,
            team1=t1_stats,
            team2=t2_stats,
            category_winners=winners,
            is_complete=is_complete
        )
        
    def _extract_stats(self, team_obj) -> TeamStats:
        # Helper to handle bytes or str
        def _decode(val):
            if isinstance(val, bytes):
                return val.decode('utf-8')
            return str(val) if val is not None else "Unknown"

        # Get team and manager names
        manager = "Unknown"
        if hasattr(team_obj, 'managers') and team_obj.managers:
             manager = _decode(team_obj.managers[0].nickname)

        ts = TeamStats(
            team_name=_decode(team_obj.name),
            manager_name=manager
        )
        
        # yfpy stores data in _extracted_data dictionary, NOT as direct attributes
        if hasattr(team_obj, '_extracted_data') and 'team_stats' in team_obj._extracted_data:
            team_stats_data = team_obj._extracted_data['team_stats']
            if isinstance(team_stats_data, dict) and 'stats' in team_stats_data:
                stats_list = team_stats_data['stats']
                
                for stat_wrapper in stats_list:
                    # stat_wrapper is a dict {'stat': StatObject}
                    if isinstance(stat_wrapper, dict) and 'stat' in stat_wrapper:
                        stat = stat_wrapper['stat']
                    elif hasattr(stat_wrapper, 'stat'):
                        stat = stat_wrapper.stat
                    else:
                        stat = stat_wrapper
                    
                    s_id = getattr(stat, 'stat_id', None)
                    val = getattr(stat, 'value', 0)
                    
                    # Ensure ID is treated as int
                    try:
                        if s_id is not None:
                            s_id = int(s_id)
                    except ValueError:
                        pass
                    
                    # value comes as string often, and might be '-'
                    if val == '-': val = 0
                    
                    if s_id in ID_TO_FIELD:
                        field_name = ID_TO_FIELD[s_id]
                        # Convert to int or float
                        try:
                            if field_name in ['save_pct', 'gaa']:
                                parsed_val = float(val)
                            else:
                                parsed_val = int(float(val)) # handle "7.0"
                            setattr(ts, field_name, parsed_val)
                        except ValueError:
                            pass # keep default 0
        
        return ts

    def _determine_winners(self, t1: TeamStats, t2: TeamStats) -> Dict[str, str]:
        winners = {}
        for field_name in ID_TO_FIELD.values():
            v1 = getattr(t1, field_name)
            v2 = getattr(t2, field_name)
            
            if v1 == v2:
                winners[field_name] = "Tie"
            else:
                if field_name in LOWER_IS_BETTER:
                    if v1 < v2: winners[field_name] = t1.team_name
                    else: winners[field_name] = t2.team_name
                else:
                    if v1 > v2: winners[field_name] = t1.team_name
                    else: winners[field_name] = t2.team_name
        return winners
