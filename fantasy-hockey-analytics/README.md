# Fantasy Hockey Analytics - Phase 3

## Overview

Phase 3 adds **team-specific performance analysis** that answers: *"How does my team compare to the league's winning thresholds?"* This transforms league-wide benchmarks into personalized, actionable insights.

## What's New in Phase 3

### ✅ Persistent Team ID Tracking
- **Schema V2**: Team IDs replace team names as the primary identifier
- **Handles renames**: Teams that change names mid-season are tracked correctly
- **Migration support**: Clean upgrade path from Phase 2 database

### ✅ Comprehensive Team Analysis Engine
- **11-category assessment**: Evaluates your team in every stat category
- **Direction-aware**: Correctly handles GAA (lower is better)
- **Gap calculation**: Shows how far above/below threshold you are
- **Win rate tracking**: Your W-L-T record in each category
- **Trend analysis**: Identifies improving, stable, or declining performance
- **Zero-goalie detection**: Distinguishes "no data" from "weak performance"

### ✅ Qualitative Assessments
Each category gets a status rating:
- **🟢 Dominant**: Above 75th percentile
- **🟢 Strong**: Above median
- **🟡 Competitive**: Above minimum winning
- **🔴 Weak**: Below minimum but in range
- **🔴 Critical**: Well below minimum
- **⚪ No Data**: No goalie starts or insufficient data

### ✅ Actionable Insights
- **Improvement Priorities**: Categories sorted by urgency (biggest gaps first)
- **Strengths**: Your dominant and strong categories highlighted
- **Trend indicators**: ↗ Improving | → Stable | ↘ Declining

### ✅ CLI Commands
```bash
python main.py team --list     # Show all teams
python main.py team --id 3     # Analyze team ID 3
python main.py team            # Analyze your team (uses MY_TEAM_ID from .env)
python main.py migrate         # Upgrade database schema
```

## Installation & Migration

### First Time (New Project)
No migration needed - just run:
```bash
python main.py fetch
python main.py team --list
```

### Upgrading from Phase 2
**⚠ Warning**: Migration deletes existing data (can be re-fetched)

```bash
# 1. Attempt to run - you'll see migration prompt
python main.py fetch

# 2. Run migration
python main.py migrate

#3. Re-fetch data with new schema
python main.py fetch

# 4. List teams and find your team ID
python main.py team --list

# 5. Set MY_TEAM_ID in .env
echo "MY_TEAM_ID=7" >> .env

# 6. Analyze your team
python main.py team
```

## Configuration

**`.env` file**:
```bash
# Your team ID (find with: python main.py team --list)
MY_TEAM_ID=7

# Optional: Custom database path
# FANTASY_DB_PATH=fantasy_hockey.db
```

## Usage Examples

### List All Teams

```bash
python main.py team --list
```

**Output:**
```
======================================================================
Available Teams
======================================================================
ID     Team Name                            Manager                  
----------------------------------------------------------------------
1      Dirty Mike and the Boys              Mike                     
2      The F Shack                          Alex                     
3      New Name FC                          Charlie                  
4      Zero Goalies                         Dana                     
5      Team Five                            Eve                      
======================================================================

Total: 10 teams

Use 'python main.py team --id <ID>' to analyze a specific team
```

### Analyze Specific Team

```bash
python main.py team --id 2
```

**Output:**
```
==========================================================================================
Team Analysis: The F Shack (ID: 2)
Performance vs League Winning Thresholds (9 weeks analyzed)
==========================================================================================
Category      You      Median   Gap       Win%    Status                 Trend          
------------------------------------------------------------------------------------------
Goals         26       24       +2.2      67%     🟢 Strong              ↗ Improving    
Assists       28       30       -1.9      44%     🟡 Competitive         → Stable       
Points        54       55       -0.5      44%     🟡 Competitive         → Stable       
Plus/Minus    1        2        -0.8      33%     🟡 Competitive         ↘ Declining    
PIM           20       22       -2.2      33%     🔴 Weak                → Stable       
PPP           11       12       -0.8      44%     🟡 Competitive         → Stable       
Hits          118      120      -2.5      44%     🟡 Competitive         → Stable       
Shots         218      225      -6.8      33%     🟡 Competitive         → Stable       
Wins          3        3        0.0       56%     🟡 Competitive         → Stable       
SV%           0.912    0.912    +0.000    50%     🟡 Competitive         → Stable       
GAA           2.820    2.650    -0.170    33%     🔴 Weak                → Stable       
------------------------------------------------------------------------------------------

📈 IMPROVEMENT PRIORITIES:
------------------------------------------------------------------------------------------
  • GAA: 0.170 above median (lower is better)
  • PIM: 2.2 below median
  • Shots: 6.8 below median
  • Hits: 2.5 below median

💪 STRENGTHS:
------------------------------------------------------------------------------------------
  ✓ Goals - Strong (gap: +2.2)

------------------------------------------------------------------------------------------
Status: 🟢 Strong/Dominant | 🟡 Competitive | 🔴 Weak/Critical | ⚪ No Data
Trend:  ↗ Improving | → Stable | ↘ Declining | ? Insufficient data
==========================================================================================
```

### Analyze Your Team (Using Config)

```bash
# Set MY_TEAM_ID=2 in .env first
python main.py team
```

## Understanding the Analysis

### Gap Calculation

The **gap** shows how far you are from the median winning threshold:
- **Positive gap** = Good! You're above the threshold (or below for GAA)
- **Negative gap** = Below threshold - needs improvement

**For "higher wins" categories** (Goals, Assists, etc.):
- Gap = Your Average - Median Threshold
- Example: Goals = 26, Median = 24 → Gap = +2.2 (good!)

**For GAA (lower is better)**:
- Gap = Median Threshold - Your Average
- Example: GAA = 2.82, Median = 2.65 → Gap = -0.17 (bad - you're above median)

### Assessment Buckets

| Assessment | Condition (Higher Wins) | Condition (GAA - Lower Wins) |
|------------|------------------------|------------------------------|
| **Dominant** | ≥ 75th percentile | ≤ 75th percentile |
| **Strong** | ≥ Median | ≤ Median |
| **Competitive** | ≥ Min Winning | ≤ Max Winning |
| **Weak** | ≥ 85% of Min | ≤ 115% of Max |
| **Critical** | < 85% of Min | > 115% of Max |
| **No Data** | All zeros (goalies) | All zeros (goalies) |

### Trend Analysis

Trends compare your first 3 weeks vs. last 3 weeks:
- **Improving**: >10% improvement
- **Declining**: >10% decline
- **Stable**: Within ±10%
- **Insufficient Data**: <4 weeks played

**Note**: For GAA, declining average = improving performance!

### Win Rate

- **Calculated from**: Your W-L-T record in that category across all matchups
- **Displayed as**: Percentage of decisions won (ties excluded from denominator)
- **Shows as "--"**: When all outcomes are ties or no data

## Edge Cases Handled

### Team Renames
**Problem**: Team changes name from "Old Name FC" to "New Name FC" in week 5

**Solution**: Schema uses persistent `team_id`:
- Analysis includes all weeks under both names
- Display shows current name
- No duplicate teams or lost history

### Zero Goalie Starts
**Problem**: Team never starts goalies (GAA=0.000, SV%=0.000)

**Solution**: Detected as "No Data":
- Assessment = ⚪ No Data (not 🔴 Critical)
- Not included in improvement priorities
- Trend shows "Insufficient data"

### New Teams Mid-Season
**Problem**: Team joins in week 8, only 2 weeks of data

**Solution**: Analysis works but limited:
- All trends show "Insufficient data" (<4 weeks)
- Assessments still calculated from available data
- Clear indication of weeks analyzed

### All-Ties in a Category
**Problem**: All matchups in a category ended in ties

**Solution**: Win rate shows "--":
- Doesn't divide by zero
- Doesn't inflate/deflate performance metrics
- Assessment based on average vs threshold

## Technical Details

### Schema V2 Changes

#### Added: `teams` table
```sql
teams (
    team_id INTEGER PRIMARY KEY,      -- Yahoo's persistent ID
    current_name TEXT NOT NULL,        -- Updates when team renames
    manager_name TEXT,
    first_seen_week INTEGER,
    last_seen_week INTEGER
)
```

#### Modified: `matchup_results`
```sql
-- Before (V1)
team1_name TEXT
team2_name TEXT
team1_manager TEXT
team2_manager TEXT

-- After (V2)
team1_id INTEGER REFERENCES teams(team_id)
team2_id INTEGER REFERENCES teams(team_id)
```

#### Modified: `category_outcomes`
```sql
-- Added
team1_id INTEGER
team2_id INTEGER
winner_team_id INTEGER  -- NULL for ties

-- Changed
winner TEXT → winner_team_id INTEGER
```

### Migration Process

1. **Detection**: `init_db()` checks schema version
2. **Prompt**: If old schema detected, exits with message
3. **User action**: Run `python main.py migrate`
4. **Execution**:
   - Drops all old tables
   - Creates new schema
   - Prompts for confirmation (requires "yes")
5. **Re-fetch**: User runs `python main.py fetch` to repopulate

### Team ID Extraction

**Primary**: `team_obj.team_id` (direct attribute)

**Fallback**: Parse from `team_obj.team_key`
- Format: `"nhl.l.16597.t.3"`
- Extract: Last segment after split('.')
- Result: `team_id = 3`

### Database Indexes

For performance on team-specific queries:
```sql
CREATE INDEX idx_category_outcomes_team1 
ON category_outcomes(team1_id, category, is_complete);

CREATE INDEX idx_category_outcomes_team2 
ON category_outcomes(team2_id, category, is_complete);
```

## Project Structure

```
fantasy-hockey-analytics/
├── src/
│   ├── __init__.py
│   ├── auth.py              # Phase 1 - OAuth
│   ├── data_fetcher.py      # Phase 1 + 3 - Extracts team_id
│   ├── models.py            # Phase 1 + 3 - Added team_id field
│   ├── display.py           # Phase 1 + 2 + 3 - Added team displays
│   ├── constants.py         # Phase 2 - Shared constants
│   ├── database.py          # Phase 2 + 3 - Schema V2
│   ├── analytics.py         # Phase 2 + 3 - Updated for new schema
│   ├── team_analysis.py     # Phase 3 - NEW
│   └── config.py            # Phase 3 - NEW
├── main.py                  # Phase 1 + 2 + 3 - Added team command
├── test_phase2.py           # Phase 2 tests
├── test_phase3.py           # Phase 3 tests (NEW)
├── .env.example             # Phase 3 - Config template (NEW)
├── fantasy_hockey.db        # SQLite database (auto-created)
└── [config files]
```

## Success Criteria ✓

All Phase 3 goals achieved:

1. ✅ `python main.py migrate` updates schema cleanly
2. ✅ `python main.py fetch` populates new schema with team_ids
3. ✅ `python main.py team --list` shows all teams with IDs
4. ✅ `python main.py team --id 7` shows full analysis
5. ✅ `python main.py team` works with MY_TEAM_ID configured
6. ✅ Team renames handled (same team_id, different names work)
7. ✅ GAA shows correctly (low value = strong, positive gap = good)
8. ✅ Zero goalie data shows "No Data" not "Critical"
9. ✅ Trends show "Insufficient Data" with < 4 weeks
10. ✅ `test_phase3.py` passes all tests

## Testing

### Automated Test Suite

```bash
python test_phase3.py
```

**Test Coverage**:
- ✅ Team rename handling
- ✅ Zero goalie data detection
- ✅ Insufficient trend data (<4 weeks)
- ✅ All-ties category (win rate undefined)
- ✅ GAA direction-aware logic
- ✅ Gap sign convention (positive = good)
- ✅ Assessment bucket thresholds
- ✅ Improvement priorities sorting
- ✅ Empty database handling
- ✅ Team not found error
- ✅ Trend calculation edge cases

**All tests use mock data** - no Yahoo API required!

### Manual Testing

1. Migrate database: `python main.py migrate`
2. Fetch real data: `python main.py fetch`
3. List teams: `python main.py team --list`
4. Analyze team: `python main.py team --id <your_id>`
5. Configure .env and test: `python main.py team`

## Troubleshooting

### "DATABASE SCHEMA MIGRATION REQUIRED"
**Solution**: Run `python main.py migrate` then re-fetch data

### "Team ID X not found"
**Solution**: Run `python main.py team --list` to see valid IDs

### "No team specified"
**Solution**: Either:
- Set `MY_TEAM_ID=X` in `.env` file, OR
- Use `--id X` flag: `python main.py team --id X`

### "Insufficient data - no completed weeks"
**Solution**: Run `python main.py fetch` to get more data

### All trends show "Insufficient data"
**Reason**: <4 completed weeks
**Solution**: Wait for more weeks to complete, then re-fetch

## Next Steps (Future Phases)

Phase 3 provides team-level insights. Future phases could add:

- **Phase 4**: Weekly projections ("What stats do I need this week to win?")
- **Phase 5**: Head-to-head matchup simulator
- **Phase 6**: Free agent recommendations based on category gaps
- **Phase 7**: Web UI with interactive charts
- **Phase 8**: Trade analyzer

## License

MIT

## Author

Built with Antigravity AI Assistant
