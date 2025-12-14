import sys
sys.path.insert(0, '.')

try:
    from test_phase3 import setup_test_database, analyze_team
    
    print("Setting up test database...")
    db_path = setup_test_database()
    print(f"Database created: {db_path}")
    
    print("\nTrying to analyze team 1...")
    result = analyze_team(1, db_path)
    print(f"Success! Team: {result.team_name}")
    
except Exception as e:
    print(f"\nError: {e}")
    import traceback
    traceback.print_exc()
