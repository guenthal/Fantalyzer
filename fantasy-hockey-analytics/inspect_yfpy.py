import inspect
from yfpy.query import YahooFantasySportsQuery

print("SIGNATURE_START")
try:
    print(inspect.signature(YahooFantasySportsQuery.get_league_matchups_by_week))
except AttributeError:
    print("Method get_league_matchups_by_week not found")
    # Try looking for similar methods
    methods = [m for m in dir(YahooFantasySportsQuery) if 'matchup' in m]
    print(f"Alternative methods: {methods}")

print("SIGNATURE_END")
