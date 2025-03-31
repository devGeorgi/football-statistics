import requests
import json
import os
from datetime import datetime, timedelta
from match_logger import get_logger

# Configuration - Edit these dates as needed
start_date = datetime.now() - timedelta(days=10)
end_date = datetime.now() - timedelta(days=1)
DATES = [(start_date + timedelta(days=i)).strftime("%Y-%m-%d") for i in range((end_date - start_date).days + 1)]

BASE_URL = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}
OUTPUT_DIR = "match_stats"
PROCESSED_DATES_FILE = "processed_dates.json"
SKIPPED_MATCHES_LOG = "skipped_matches.log"

# Initialize the logger
match_logger = get_logger(SKIPPED_MATCHES_LOG)

def initialize_team():
    """Return a new team structure with default values"""
    return {
        "winstreak": 0,
        "losestreak": 0,
        "games_without_win": 0,
        "games_without_loss": 0,
        "match_history": [],
        "last_streak_match": None
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
                # Log to file instead of printing to terminal
                match_logger.log_skipped_match(date, ht, at)
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

            # Create compact match records with date and score
            ht_match_detail = [
                date,           # date
                at,             # opponent
                ht_result,      # result (w/l/d)
                f"{hsc}-{asc}"  # score
            ]
            
            at_match_detail = [
                date,           # date
                ht,             # opponent
                at_result,      # result (w/l/d)
                f"{asc}-{hsc}"  # score
            ]

            # Track previous streak values to detect changes
            ht_prev_without_win = teams[ht]["games_without_win"]
            ht_prev_without_loss = teams[ht]["games_without_loss"]
            at_prev_without_win = teams[at]["games_without_win"]
            at_prev_without_loss = teams[at]["games_without_loss"]

            # Update home team stats based on match result
            if hsc > asc:  # Home team won
                # Record this win if it's the start of a new win streak
                teams[ht]["winstreak"] += 1
                teams[ht]["losestreak"] = 0
                teams[ht]["games_without_win"] = 0
                teams[ht]["games_without_loss"] += 1
                # Store this match as the last win before a potential "without win" streak
                teams[ht]["last_streak_match"] = ht_match_detail
                
            elif hsc < asc:  # Home team lost
                # Record this loss as the transition point for "games_without_loss"
                if teams[ht]["games_without_loss"] > 0:
                    teams[ht]["last_streak_match"] = ht_match_detail
                    teams[ht]["match_history"] = []
                
                teams[ht]["losestreak"] += 1
                teams[ht]["winstreak"] = 0
                teams[ht]["games_without_win"] += 1
                teams[ht]["games_without_loss"] = 0
                
            elif hsc == asc:  # Draw
                teams[ht]["winstreak"] = 0
                teams[ht]["losestreak"] = 0
                teams[ht]["games_without_win"] += 1
                teams[ht]["games_without_loss"] += 1

            # Always add the current match to match history - it's part of the current streak
            teams[ht]["match_history"].append(ht_match_detail)
            
            # For 'games_without_loss' streak, keep all those matches
            if teams[ht]["games_without_loss"] > 0:
                # Ensure we only keep the matches that are part of the current streak
                teams[ht]["match_history"] = teams[ht]["match_history"][-teams[ht]["games_without_loss"]:]
            # For 'games_without_win' streak, keep all those matches 
            elif teams[ht]["games_without_win"] > 0:
                teams[ht]["match_history"] = teams[ht]["match_history"][-teams[ht]["games_without_win"]:]

            # Update away team stats based on match result
            if asc > hsc:  # Away team won
                teams[at]["winstreak"] += 1
                teams[at]["losestreak"] = 0
                teams[at]["games_without_win"] = 0
                teams[at]["games_without_loss"] += 1
                # Store this match as the last win before a potential "without win" streak
                teams[at]["last_streak_match"] = at_match_detail
                
            elif asc < hsc:  # Away team lost
                # Record this loss as the transition point for "games_without_loss"
                if teams[at]["games_without_loss"] > 0:
                    teams[at]["last_streak_match"] = at_match_detail
                    teams[at]["match_history"] = []
                
                teams[at]["losestreak"] += 1
                teams[at]["winstreak"] = 0
                teams[at]["games_without_win"] += 1
                teams[at]["games_without_loss"] = 0
                
            elif asc == hsc:  # Draw
                teams[at]["winstreak"] = 0
                teams[at]["losestreak"] = 0
                teams[at]["games_without_win"] += 1
                teams[at]["games_without_loss"] += 1
            
            # Always add the current match to match history - it's part of the current streak
            teams[at]["match_history"].append(at_match_detail)
            
            # For 'games_without_loss' streak, keep all those matches
            if teams[at]["games_without_loss"] > 0:
                # Ensure we only keep the matches that are part of the current streak
                teams[at]["match_history"] = teams[at]["match_history"][-teams[at]["games_without_loss"]:]
            # For 'games_without_win' streak, keep all those matches
            elif teams[at]["games_without_win"] > 0:
                teams[at]["match_history"] = teams[at]["match_history"][-teams[at]["games_without_win"]:]

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