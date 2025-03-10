import argparse
import json
import requests
from datetime import datetime

# Configuration
BASE_URL = "https://api.sofascore.com/api/v1/sport/football/scheduled-events/{date}"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
}

def load_team_data():
    """Load existing team statistics"""
    try:
        with open("teams.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print("Error: teams.json not found. Run the main scraper first.")
        exit(1)

def get_daily_teams(date):
    """Get teams playing on specified date"""
    try:
        url = BASE_URL.format(date=date)
        response = requests.get(url, headers=HEADERS, timeout=10)
        response.raise_for_status()
        events = response.json().get("events", [])
        
        teams = set()
        for event in events:
            teams.add(event["homeTeam"]["name"])
            teams.add(event["awayTeam"]["name"])
        return list(teams)
    
    except Exception as e:
        print(f"Error fetching matches: {e}")
        exit(1)

def analyze_date(date):
    """Analyze teams playing on specific date"""
    # Get teams playing that day
    daily_teams = get_daily_teams(date)
    
    # Load all team stats
    all_teams = load_team_data()
    
    # Filter to only teams playing that day
    filtered_teams = {team: all_teams[team] for team in daily_teams if team in all_teams}
    
    if not filtered_teams:
        print(f"No team data available for matches on {date}")
        return
    
    # Categories to analyze
    categories = {
        "winstreak": "Current Win Streak",
        "losestreak": "Current Lose Streak", 
        "not_won": "Matches Without Win",
        "not_lost": "Matches Without Loss"
    }
    
    print(f"\nTop performers for {date} matches:")
    print("=" * 40)
    
    for cat, label in categories.items():
        # Sort teams by category value descending
        sorted_teams = sorted(
            filtered_teams.items(),
            key=lambda x: x[1][cat],
            reverse=True
        )[:3]  # Get top 3
        
        print(f"\n{label}:")
        for idx, (team, stats) in enumerate(sorted_teams, 1):
            print(f"{idx}. {team}: {stats[cat]}")

def show_team_stats(team_name):
    """Display statistics for a specific team"""
    teams = load_team_data()
    team_stats = teams.get(team_name.title())
    
    if not team_stats:
        print(f"Team '{team_name}' not found in database")
        return
    
    print(f"\nStatistics for {team_name.title()}:")
    print(f"- Current win streak: {team_stats['winstreak']}")
    print(f"- Current lose streak: {team_stats['losestreak']}")
    print(f"- Matches without win: {team_stats['not_won']}")
    print(f"- Matches without loss: {team_stats['not_lost']}")

def main():
    parser = argparse.ArgumentParser(description="Team Statistics Analyzer")
    parser.add_argument("--date", help="Date to analyze (YYYY-MM-DD)")
    parser.add_argument("--team", help="Team name to show statistics")
    
    args = parser.parse_args()
    
    if args.date:
        try:
            datetime.strptime(args.date, "%Y-%m-%d")
            analyze_date(args.date)
        except ValueError:
            print("Invalid date format. Use YYYY-MM-DD")
    elif args.team:
        show_team_stats(args.team)
    else:
        print("Please specify either --date or --team")

if __name__ == "__main__":
    main()