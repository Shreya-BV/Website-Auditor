import json

with open("scratch/test_output.txt", "r", encoding="utf-16le") as f:
    text = f.read()
    
# Find where JSON starts (it might have some playright logs before it)
start_idx = text.find("{")
if start_idx != -1:
    data = json.loads(text[start_idx:])
    print(f"Lenskart Score: {data.get('overall_score')}")
    print(f"Grade: {data.get('grade')}")
    print(f"Pillar Scores: {data.get('pillar_scores')}")
else:
    print("Could not parse JSON.")
