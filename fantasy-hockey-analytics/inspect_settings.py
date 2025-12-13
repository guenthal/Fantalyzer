from src.auth import get_yahoo_query
import logging

logging.basicConfig(level=logging.INFO)

def inspect_settings():
    LEAGUE_ID = "16597"
    query = get_yahoo_query(LEAGUE_ID)
    
    print("Fetching league settings...")
    # yfpy method to get settings
    settings = query.get_league_settings()
    
    print("\n--- Stat Categories ---")
    if hasattr(settings, 'stat_categories') and hasattr(settings.stat_categories, 'stats'):
        for stat in settings.stat_categories.stats:
            # Stats are usually wrapped too? e.g. stat.stat.stat_id
            # Let's handle both cases to be safe in print
            s = stat.stat if hasattr(stat, 'stat') else stat
            
            s_id = getattr(s, 'stat_id', 'Unknown')
            name = getattr(s, 'name', 'Unknown')
            d_name = getattr(s, 'display_name', 'Unknown')
            
            print(f"ID: {s_id} | Name: {name} | Display: {d_name}")
    else:
        print("Could not find stat_categories in settings.")
        # detailed dump if needed
        # print(settings)

if __name__ == "__main__":
    inspect_settings()
