import requests
import json
import os
from datetime import datetime, timedelta

# Configuration - Edit these dates as needed
start_date = datetime.now() - timedelta(days=365)
end_date = datetime.now() - timedelta(days=1)
DATES = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]

BASE_URL = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
OUTPUT_DIR = "match_stats"
PROCESSED_DATES_FILE = "processed_dates.json"

def initialize_team():
    """Return a new team structure with default values"""
    return {
        "winstreak": 0,
        "losestreak": 0,
        "games_without_win": 0,
        "games_without_loss": 0,
        "last_matches_with_opponents": []
    }

def create_directory():
    """Create output directory if it doesn't exist"""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

def load_processed_dates():
    """Load processed dates from file"""
    if os.path.exists(PROCESSED_DATES_FILE):
        with open(PROCESSED_DATES_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_processed_dates(processed_dates):
    """Save processed dates to file"""
    with open(PROCESSED_DATES_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(processed_dates), f, indent=4)

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

def process_matches(date, events, teams, processed_matches):
    """Process matches and update team statistics"""
    match_records = []
    
    for event in events:
        try:
            ht = event['homeTeam']['name']
            at = event['awayTeam']['name']
            hsc = event.get('homeScore', {}).get('current', None)
            asc = event.get('awayScore', {}).get('current', None)
            
            # Skip unplayed or postponed matches where scores are None
            if hsc is None or asc is None:
                print(f"Skipping unplayed/postponed match: {ht} vs {at}")
                continue
                
            match_id = (ht, at, hsc, asc)

            # Skip if match already processed
            if match_id in processed_matches:
                continue
            processed_matches.add(match_id)

            # Initialize teams if they don't exist
            if ht not in teams:
                teams[ht] = initialize_team()
            if at not in teams:
                teams[at] = initialize_team()

            # Determine match result
            if hsc > asc:
                ht_result = 'w'
                at_result = 'l'
            elif hsc < asc:
                ht_result = 'l'
                at_result = 'w'
            elif hsc == asc:
                ht_result = 'd'
                at_result = 'd'
            else:
                # This should not happen, but just in case
                print(f"Unexpected score situation: {ht} {hsc} - {asc} {at}")
                continue

            # Update home team stats
            if hsc > asc:
                teams[ht]["winstreak"] += 1
                teams[ht]["losestreak"] = 0
                teams[ht]["games_without_win"] = 0
                teams[ht]["games_without_loss"] += 1
            elif hsc < asc:
                teams[ht]["losestreak"] += 1
                teams[ht]["winstreak"] = 0
                teams[ht]["games_without_win"] += 1
                teams[ht]["games_without_loss"] = 0
            elif hsc == asc:
                teams[ht]["winstreak"] = 0
                teams[ht]["losestreak"] = 0
                teams[ht]["games_without_win"] += 1
                teams[ht]["games_without_loss"] += 1

            # Update away team stats
            if asc > hsc:
                teams[at]["winstreak"] += 1
                teams[at]["losestreak"] = 0
                teams[at]["games_without_win"] = 0
                teams[at]["games_without_loss"] += 1
            elif asc < hsc:
                teams[at]["losestreak"] += 1
                teams[at]["winstreak"] = 0
                teams[at]["games_without_win"] += 1
                teams[at]["games_without_loss"] = 0
            elif asc == hsc:
                teams[at]["winstreak"] = 0
                teams[at]["losestreak"] = 0
                teams[at]["games_without_win"] += 1
                teams[at]["games_without_loss"] += 1

            # Update last matches with opponents
            teams[ht]["last_matches_with_opponents"].append(f"{ht_result} vs {at}")
            teams[at]["last_matches_with_opponents"].append(f"{at_result} vs {ht}")
            teams[ht]["last_matches_with_opponents"] = teams[ht]["last_matches_with_opponents"][-max(teams[ht]["games_without_win"], teams[ht]["games_without_loss"], 1):]
            teams[at]["last_matches_with_opponents"] = teams[at]["last_matches_with_opponents"][-max(teams[at]["games_without_win"], teams[at]["games_without_loss"], 1):]

            # Ensure no duplicate entries for the same match
            teams[ht]["last_matches_with_opponents"] = list(dict.fromkeys(teams[ht]["last_matches_with_opponents"]))
            teams[at]["last_matches_with_opponents"] = list(dict.fromkeys(teams[at]["last_matches_with_opponents"]))

            # Create match record for output file
            match_records.append(f"{ht}, {hsc}\n{at}, {asc}")

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
    processed_matches = set()
    processed_dates = load_processed_dates()

    for date in DATES:
        if date in processed_dates:
            print(f"\nSkipping {date}, already processed.")
            continue

        print(f"\nProcessing {date}...")
        events = get_matches(date)
        
        if not events:
            print(f"No matches found for {date}")
            continue
            
        match_records = process_matches(date, events, teams, processed_matches)
        save_data(date, match_records, teams)
        processed_dates.add(date)

    save_processed_dates(processed_dates)

if __name__ == "__main__":
    main()