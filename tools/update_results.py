import json
import os
from datetime import datetime

"""
RETRO CUP 26 - Results Editor
Manual CLI tool to update src/data_official.json
"""

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, 'src', 'data.json')
OFFICIAL_PATH = os.path.join(BASE_DIR, 'src', 'data_official.json')

def get_local_date_str(iso_str):
    """Converts UTC ISO string to local YYYY-MM-DD, matching JS behavior."""
    if not iso_str or iso_str == 'TBD':
        return 'TBD'
    try:
        # Replace 'Z' with +00:00 for compatibility with Python < 3.11
        dt_utc = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        # .astimezone() with no args converts to system local time
        dt_local = dt_utc.astimezone()
        return dt_local.strftime("%Y-%m-%d")
    except (ValueError, TypeError):
        return 'TBD'

def get_valid_int(prompt):
    while True:
        val = input(f"{prompt}: ").strip()
        if val.isdigit():
            return int(val)
        print(" >> INVALID INPUT. PLEASE ENTER AN INTEGER.")

def load_json(path):
    if not os.path.exists(path):
        return [] if "official" in path else {}
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_json(path, data):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f)

def main():
    print("="*40)
    print("   RETRO CUP 26 - OFFICIAL UPDATER")
    print("="*40)

    # 1. Get Date
    date_input = input("ENTER DATE (YYYYMMDD): ").strip()
    try:
        target_date = datetime.strptime(date_input, "%Y%m%d").strftime("%Y-%m-%d")
    except ValueError:
        print(" >> ERROR: FORMAT MUST BE YYYYMMDD (e.g. 20260611)")
        return

    # 2. Load Data
    data = load_json(DATA_PATH)
    official = load_json(OFFICIAL_PATH)
    
    # Flatten all match stages to find matches on this date
    all_matches = []
    for stage in data.get('matches', {}).values():
        all_matches.extend(stage)

    daily_matches = [m for m in all_matches if get_local_date_str(m.get('date', '')) == target_date]

    if not daily_matches:
        print(f" >> NO MATCHES FOUND FOR {target_date}")
        return

    print(f"\nFOUND {len(daily_matches)} MATCHES ON {target_date}")
    
    new_results = []

    for m in daily_matches:
        print("\n" + "-"*30)
        print(f"MATCH #{m['id']} | {m['venue']}")
        print("-"*30)
        
        # Team 1 Input
        print(f"TEAM 1: {m['team1']['code']}")
        t1_score = get_valid_int("  Score")
        t1_yc = get_valid_int("  Yellow Cards")
        t1_rc = get_valid_int("  Red Cards")
        t1_pk = 0
        
        # Team 2 Input
        print(f"\nTEAM 2: {m['team2']['code']}")
        t2_score = get_valid_int("  Score")
        t2_yc = get_valid_int("  Yellow Cards")
        t2_rc = get_valid_int("  Red Cards")
        t2_pk = 0

        # Handle Penalties for Knockouts
        if m['id'] > 72 and t1_score == t2_score:
            print("\n[ PENALTY SHOOTOUT REQUIRED ]")
            t1_pk = get_valid_int(f"  {m['team1']['code']} PKS")
            t2_pk = get_valid_int(f"  {m['team2']['code']} PKS")

        result = {
            "id": m['id'],
            "played": True,
            "team1": {
                "score": t1_score,
                "yellow_cards": t1_yc,
                "red_cards": t1_rc,
                "penalties": t1_pk
            },
            "team2": {
                "score": t2_score,
                "yellow_cards": t2_yc,
                "red_cards": t2_rc,
                "penalties": t2_pk
            }
        }
        new_results.append(result)

    # 3. Confirmation
    print("\n" + "="*40)
    print("SUMMARY OF ENTRIES:")
    for r in new_results:
        m_info = next(m for m in daily_matches if m['id'] == r['id'])
        print(f" Match {r['id']}: {m_info['team1']['code']} {r['team1']['score']} - {r['team2']['score']} {m_info['team2']['code']}")

    confirm = input("\nCONFIRM SAVE? (Y/N): ").strip().upper()
    
    if confirm == 'Y':
        # Merge with existing official data
        # We create a map by ID to update existing entries instead of duplicating
        official_map = {m['id']: m for m in official}
        
        for r in new_results:
            official_map[r['id']] = r
            
        # Convert back to list and sort by match ID
        updated_official = sorted(official_map.values(), key=lambda x: x['id'])
        
        try:
            save_json(OFFICIAL_PATH, updated_official)
            print("\n >> SUCCESS: DATA_OFFICIAL.JSON UPDATED.")
        except Exception as e:
            print(f"\n >> ERROR SAVING FILE: {e}")
    else:
        print("\n >> ABORTED. NO CHANGES SAVED.")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n >> SESSION CANCELLED BY USER.")
    except Exception as e:
        print(f"\n >> CRITICAL ERROR: {e}")
