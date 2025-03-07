import json
import requests

url = "https://sportapi7.p.rapidapi.com/api/v1/sport/football/scheduled-events/2025-03-07"
headers = json.load(open("headers.json"))

answer = requests.get(url, headers=headers)

#create a file .json that stores the answer 
with open("results.json", "w", encoding="utf-8") as f:
    f.write(answer.text)