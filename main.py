import json
import requests

url = "https://sportapi7.p.rapidapi.com/api/v1/sport/football/scheduled-events/2025-03-05"
headers = json.load(open("headers.json"))

answer = requests.get(url, headers=headers)
# Function to initialize a team if it doesn't exist
def initialize_team(team):
    if team not in teams:
        teams[team] = {
            "winstreak": 0,
            "losestreak": 0,
            "not_won": 0,
            "not_lost": 0
        }

# Load the match data from results.json
try:
    response = json.loads(answer.text)
except FileNotFoundError:
    print("Error: results.json file not found.")
    exit()

# Load the existing teams data from teams.json
try:
    teams = json.load(open("teams.json"))
except FileNotFoundError:
    teams = {}

# Process each match in the results.json file
for i in range(len(response["events"])):
    try:
        # Extract match data
        ht = response["events"][i]["homeTeam"]["name"]
        at = response["events"][i]["awayTeam"]["name"]
        hsc = response["events"][i]["homeScore"]["current"]
        asc = response["events"][i]["awayScore"]["current"]

        # Initialize teams if they don't exist
        initialize_team(ht)
        initialize_team(at)

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

        # Print updated match data
        print(f"Match: {ht} {hsc} - {asc} {at}")
        print(f"{ht} stats: {teams[ht]}")
        print(f"{at} stats: {teams[at]}")
        print("-" * 40)

    except KeyError as e:
        print(f"Error processing match {i}: Missing key {e}")
    except Exception as e:
        print(f"Error processing match {i}: {e}")

# Save the updated teams data back to teams.json
with open("teams.json", "w", encoding="utf-8") as f:
    json.dump(teams, f, indent=4)

print("Team statistics updated and saved to teams.json.")