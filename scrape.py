import requests
import json
import os
from datetime import datetime

# Configuration - Edit these dates as needed
DATES = ["2025-03-10"]  # Add/remove dates here
BASE_URL = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
OUTPUT_DIR = "match_stats"

def initialize_team():
    """Return a new team structure with default values"""
    return {
        "winstreak": 0,
        "losestreak": 0,
        "not_won": 0,
        "not_lost": 0
    }

def create_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def get_matches(date):
    """Fetch matches for a specific date"""
    try:
        url = BASE_URL.format(date=date)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        return response.json().get('events', [])
    except Exception as e:
        print(f"Error fetching {date}: {str(e)}")
        return []

def process_matches(date, events, teams):
    """Process matches and update team statistics"""
    match_records = []
    
    for event in events:
        try:
            ht = event['homeTeam']['name']
            at = event['awayTeam']['name']
            hsc = event.get('homeScore', {}).get('current', 0)
            asc = event.get('awayScore', {}).get('current', 0)

            # Initialize teams if they don't exist
            if ht not in teams:
                teams[ht] = initialize_team()
            if at not in teams:
                teams[at] = initialize_team()

            # Update home team stats
            if hsc > asc:
                teams[ht]["winstreak"] += 1
                teams[ht]["losestreak"] = 0
                teams[ht]["not_won"] = 0
                teams[ht]["not_lost"] += 1
            elif hsc < asc:
                teams[ht]["losestreak"] += 1
                teams[ht]["winstreak"] = 0
                teams[ht]["not_won"] += 1
                teams[ht]["not_lost"] = 0
            else:
                teams[ht]["winstreak"] = 0
                teams[ht]["losestreak"] = 0
                teams[ht]["not_won"] += 1
                teams[ht]["not_lost"] += 1

            # Update away team stats
            if asc > hsc:
                teams[at]["winstreak"] += 1
                teams[at]["losestreak"] = 0
                teams[at]["not_won"] = 0
                teams[at]["not_lost"] += 1
            elif asc < hsc:
                teams[at]["losestreak"] += 1
                teams[at]["winstreak"] = 0
                teams[at]["not_won"] += 1
                teams[at]["not_lost"] = 0
            else:
                teams[at]["winstreak"] = 0
                teams[at]["losestreak"] = 0
                teams[at]["not_won"] += 1
                teams[at]["not_lost"] += 1

            # Create match record for output file
            match_records.append(f"{ht}, {hsc}\n{at}, {asc}")
            
            # Print match details
            print(f"Match: {ht} {hsc} - {asc} {at}")
            print(f"{ht} stats: {json.dumps(teams[ht], indent=2)}")
            print(f"{at} stats: {json.dumps(teams[at], indent=2)}")
            print("-" * 40)

        except KeyError as e:
            print(f"Error processing match: Missing key {e}")
        except Exception as e:
            print(f"Error processing match: {e}")
    
    return match_records

def save_data(date, match_records, teams):
    """Save match results and team statistics"""
    # Save match results
    if match_records:
        filename = f"scores_{date}.txt"
        file_path = os.path.join(OUTPUT_DIR, filename)
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n\n'.join(match_records))
            print(f"Saved match results to {filename}")
        except Exception as e:
            print(f"Error saving {filename}: {str(e)}")
    
    # Save team statistics
    try:
        with open("teams.json", 'w', encoding='utf-8') as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print("Team statistics updated in teams.json")
    except Exception as e:
        print(f"Error saving teams.json: {str(e)}")

def main():
    """Main program execution"""
    # Load existing team data
    try:
        with open("teams.json", 'r', encoding='utf-8') as f:
            teams = json.load(f)
    except FileNotFoundError:
        teams = {}
        print("Created new teams database")

    create_directory()

    for date in DATES:
        print(f"\nProcessing {date}...")
        events = get_matches(date)
        
        if not events:
            print(f"No matches found for {date}")
            continue
            
        match_records = process_matches(date, events, teams)
        save_data(date, match_records, teams)

if __name__ == "__main__":
    main()