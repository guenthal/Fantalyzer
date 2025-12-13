# Fantasy Hockey Analytics - Phase 2

## Overview

Phase 2 adds **SQLite persistence** and a **threshold analytics engine** to answer the key question: *"What does it take to win each stat category in my league?"*

## What's New in Phase 2

### ✅ SQLite Database Persistence
- All matchup data is automatically saved to `fantasy_hockey.db`
- Handles both complete and incomplete weeks
- Re-fetching updates existing data (no duplicates)
- Lightweight - uses Python's built-in `sqlite3` module

### ✅ Threshold Analytics Engine
- Calculates winning thresholds for all 11 stat categories
- Metrics include:
  - **Min Winning**: Lowest value that won
  - **Median Winning**: Typical winning value
  - **75th Percentile**: Strong performance benchmark
  - **Max Losing**: Highest value that still lost
  - **Overlap Zone**: Range where outcomes are uncertain

### ✅ Direction-Aware Analysis
- Correctly handles **GAA** (lower is better)
- All other stats: higher is better
- Thresholds adjust based on stat direction

### ✅ CLI Interface
Three distinct modes for different workflows:

```bash
python main.py fetch      # Fetch latest data from Yahoo and save to DB
python main.py status     # Show which weeks are stored
python main.py analyze    # Run threshold analysis
python main.py            # Default: fetch + analyze
```

## Installation

No new dependencies! Phase 2 uses only Python built-ins:
- `sqlite3` - Database persistence
- `statistics` - Median/percentile calculations
- `argparse` - CLI argument parsing

## Usage Examples

### Fetch Fresh Data

```bash
# Activate virtual environment (WSL/Linux)
source venv/bin/activate

# Fetch weeks 1-10 from Yahoo API
python main.py fetch
```

**Output:**
```
============================================================
Fetching Data from Yahoo Fantasy API
============================================================
Initializing Yahoo API connection...
Resolved Game ID for 2025: nhl.l.16597
Fetching matchups for weeks 1-10...

============================================================
Fetch Summary
============================================================
Week 1: 5 matchups (complete)
Week 2: 5 matchups (complete)
...
Week 9: 5 matchups (complete)
Week 10: 5 matchups (in progress)
------------------------------------------------------------
Summary: 10 weeks stored (9 complete, 1 in progress)
============================================================

✓ Data persisted to fantasy_hockey.db
```

### Check Database Status

```bash
python main.py status
```

**Output:**
```
============================================================
Database Status
============================================================
Total weeks stored: 10
Complete weeks: 9
Incomplete weeks: 1
------------------------------------------------------------
Week 1: ✓ Complete
Week 2: ✓ Complete
...
Week 10: ⏳ In Progress
============================================================
```

### Run Threshold Analysis

```bash
python main.py analyze
```

**Output:**
```
================================================================================
League Winning Thresholds
================================================================================
Analysis Period: Weeks 1-9 (9 complete weeks, ~45 matchups)
Week(s) 10 in progress - excluded from analysis
--------------------------------------------------------------------------------
Category     Dir    Min Win    Median     75th %     Max Lose   Overlap Zone   
--------------------------------------------------------------------------------
Goals        Higher 18         24         28         26         18-26          
Assists      Higher 22         30         35         33         22-33          
Points       Higher 42         55         62         58         42-58          
Plus/Minus   Higher -1         2          4          1          -1 to 4        
PIM          Higher 14         22         28         25         14-25          
PPP          Higher 8          12         15         14         8-14           
Hits         Higher 85         120        145        135        85-135         
Shots        Higher 180        225        260        245        180-245        
Wins         Higher 2          3          4          3          2-3            
SV%          Higher 0.895      0.912      0.924      0.918      .895-.918      
GAA          Lower  2.350      2.650      2.850      2.500      2.50-2.85      
--------------------------------------------------------------------------------

Note: 'Overlap Zone' = range where both wins and losses occurred.
      Above the zone (or below for GAA) = likely win.
      Below the zone (or above for GAA) = likely loss.
================================================================================
```

## Understanding the Results

### Threshold Metrics Explained

| Metric | What It Means | How to Use It |
|--------|---------------|---------------|
| **Min Win** | The lowest value that won a matchup | Floor for competitive performance |
| **Median** | Typical winning value (50th percentile) | Target for consistent wins |
| **75th %** | Strong performance benchmark | Aim here to win more often |
| **Max Lose** | Highest value that still lost | Even great stats can lose sometimes |
| **Overlap Zone** | Where both wins/losses happened | Uncertain outcomes - need luck or other categories |

### The Overlap Zone

The **overlap zone** is the most interesting insight. It reveals where outcomes are unpredictable:

- **Goals: 18-26** means scoring 18-26 goals could win OR lose depending on your opponent
- **Above 26 goals**: Very likely to win the category
- **Below 18 goals**: Very likely to lose the category

For **GAA** (lower is better), the logic flips:
- **GAA: 2.50-2.85** is the uncertain zone
- **Below 2.50**: Very likely to win
- **Above 2.85**: Very likely to lose

## Data Integrity

### Complete vs Incomplete Weeks

Phase 2 strictly separates complete and incomplete matchups:

✅ **Complete weeks**: Included in all analytics  
⏳ **Incomplete weeks**: Stored but excluded from thresholds (marked as "in progress")

### Re-Fetching Updates

Running `python main.py fetch` multiple times is safe:
- Updates existing weeks when they complete
- Changes `is_complete` flag from `FALSE` → `TRUE`
- Refreshes all stats with latest values
- No duplicate entries

## Database Schema

The SQLite database has three tables:

### `weekly_snapshots`
Tracks when each week was fetched and its completion status.

### `matchup_results`
One row per matchup with overall results (e.g., "Team A wins 7-3-1").

### `category_outcomes`
**The key table for analytics.** One row per category per matchup.

Example row:
```
week_number: 5
category: 'goals'
team1_value: 28
team2_value: 22
winner: 'Team Alpha'
winning_value: 28
losing_value: 22
is_complete: TRUE
```

## Technical Details

### Stack
- **Language**: Python 3.12+
- **Database**: SQLite (via `sqlite3` module)
- **Statistics**: Python `statistics` module
- **CLI**: `argparse`

### Project Structure
```
fantasy-hockey-analytics/
├── src/
│   ├── __init__.py
│   ├── auth.py              # OAuth handling
│   ├── data_fetcher.py      # Yahoo API calls
│   ├── models.py            # Dataclasses
│   ├── display.py           # Console formatting (Phase 1 + 2)
│   ├── constants.py         # Shared constants (NEW)
│   ├── database.py          # SQLite persistence (NEW)
│   └── analytics.py         # Threshold calculations (NEW)
├── main.py                  # CLI entry point (UPDATED)
├── fantasy_hockey.db        # SQLite database (auto-created, git-ignored)
└── [config files]
```

### Constants Extraction
Phase 2 created `src/constants.py` to centralize:
- Stat ID mappings (`ID_TO_FIELD`)
- Direction flags (`LOWER_IS_BETTER`)
- Display names (`CATEGORY_DISPLAY_NAMES`)

This replaces duplicated constants previously in `data_fetcher.py`.

## Success Criteria ✓

All Phase 2 goals achieved:

1. ✅ `python main.py fetch` persists matchup data to SQLite
2. ✅ `python main.py status` shows weeks stored and completion status
3. ✅ `python main.py analyze` outputs threshold report for all 11 categories
4. ✅ Incomplete weeks clearly excluded from analysis with note in output
5. ✅ GAA correctly handled as "lower is better"
6. ✅ Re-running fetch updates existing weeks (no duplicates)
7. ✅ Overlap zone visible for each category

## Next Steps (Future Phases)

Phase 2 provides the **data foundation** for advanced features:

- **Phase 3**: Team-specific analysis ("Am I competitive in each category?")
- **Phase 4**: Projection engine ("What stats do I need this week to win?")
- **Phase 5**: Web UI with visualizations
- **Phase 6**: Free agent recommendations based on category gaps

## Troubleshooting

### "No module named 'yfpy'"
Activate the virtual environment:
```bash
source venv/bin/activate  # WSL/Linux
```

### "Insufficient data - no completed weeks"
- Run `python main.py fetch` first
- Check `python main.py status` to see if any weeks are complete
- Complete weeks are marked with `✓` in status output

### Database file not found
The database is created automatically. Just run:
```bash
python main.py fetch
```

## License

MIT

## Author

Built with Antigravity AI Assistant
