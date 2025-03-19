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
        "match_history": [],
        "last_streak_match": None
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

def process_match(match, teams, processed_matches, date):
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
            process_match(match, teams, processed_matches, date)
    
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
