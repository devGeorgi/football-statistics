import os
import json
from datetime import datetime

OUTPUT_DIR = "match_stats"

def initialize_team():
    """Return a new team structure with default values"""
    return {
        "winstreak": 0,
        "losestreak": 0,
        "games_without_win": 0,
        "games_without_loss": 0,
        "last_matches_with_opponents": []
    }

def get_available_dates():
    """Get list of dates with saved match data"""
    if not os.path.exists(OUTPUT_DIR):
        print(f"Error: {OUTPUT_DIR} directory not found")
        return []
    
    dates = []
    for filename in os.listdir(OUTPUT_DIR):
        if filename.startswith("scores_") and filename.endswith(".txt"):
            date_str = filename[7:-4]  # Extract date from "scores_YYYY-MM-DD.txt"
            try:
                datetime.strptime(date_str, "%Y-%m-%d")  # Validate date format
                dates.append(date_str)
            except ValueError:
                continue
    
    return sorted(dates)

def load_match_data(date):
    """Load match data from saved file for a specific date"""
    file_path = os.path.join(OUTPUT_DIR, f"scores_{date}.txt")
    
    if not os.path.exists(file_path):
        print(f"No data file found for {date}")
        return []
    
    matches = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Split by double newlines to get each match
        match_blocks = content.split('\n\n')
        
        for block in match_blocks:
            if not block.strip():
                continue
                
            # Split into home and away team lines
            lines = block.strip().split('\n')
            if len(lines) >= 2:
                home_data = lines[0].split(', ')
                away_data = lines[1].split(', ')
                
                if len(home_data) >= 2 and len(away_data) >= 2:
                    home_team = home_data[0]
                    home_score = int(home_data[1])
                    away_team = away_data[0]
                    away_score = int(away_data[1])
                    
                    matches.append({
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_score": home_score,
                        "away_score": away_score
                    })
    
    except Exception as e:
        print(f"Error loading data for {date}: {e}")
    
    return matches

def process_match(match, teams, processed_matches):
    """Process a single match and update team statistics"""
    ht = match["home_team"]
    at = match["away_team"]
    hsc = match["home_score"]
    asc = match["away_score"]
    
    # Create unique match identifier
    match_id = (ht, at, hsc, asc)
    
    # Skip if match already processed
    if match_id in processed_matches:
        return
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
        # This should not happen with properly formatted files, but just in case
        print(f"Unexpected score situation: {ht} {hsc} - {asc} {at}")
        return
    
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

def rebuild_statistics():
    """Rebuild team statistics from saved match data files"""
    # Reset teams data
    teams = {}
    processed_matches = set()
    
    # Get all available dates
    dates = get_available_dates()
    if not dates:
        print("No match data files found")
        return
    
    print(f"Found match data for {len(dates)} dates")
    
    # Process matches in chronological order
    for date in sorted(dates):
        print(f"Processing data for {date}...")
        matches = load_match_data(date)
        
        for match in matches:
            process_match(match, teams, processed_matches)
    
    # Save updated team statistics
    try:
        with open("teams.json", 'w', encoding='utf-8') as f:
            json.dump(teams, f, indent=4, ensure_ascii=False)
        print("Team statistics rebuilt and saved to teams.json")
    except Exception as e:
        print(f"Error saving teams.json: {e}")
    
    return teams

if __name__ == "__main__":
    print("Rebuilding team statistics from saved match data...")
    rebuild_statistics()
    print("Done!")
