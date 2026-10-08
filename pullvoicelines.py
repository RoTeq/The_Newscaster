import json
import urllib.request

url = "https://deadlock.vlviewer.com/characters/newscaster.json"
print("Fetching Newscaster data...")

req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

try:
  with urllib.request.urlopen(req) as response:
    data = json.loads(response.read().decode("utf-8"))

    print("JSON keys found:", list(data.keys()))
    print(f"{data["interactions"]}")

    voicelines = []
    count = 0
    for interaction in data["interactions"]:
      print(interaction["text"])
      voiceline = {
        "category": interaction["category"],
        "text": interaction["text"],
        "with": interaction["with"]
      }
      voicelines.append(voiceline)
    with open("voicelines.json", "w") as f:
        json.dump(voicelines, f, indent=4)
      

except Exception as e:
  print(f"Error fetching data: {e}")