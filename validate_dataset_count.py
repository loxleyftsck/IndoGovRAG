import json
from pathlib import Path

# Load dataset
dataset_path = Path("data/eval_dataset_50q.json")
with open(dataset_path, encoding='utf-8') as f:
    data = json.load(f)

print("✅ JSON Valid")
print(f"\nTotal Questions: {len(data['questions'])}")

# Count categories
categories = {}
difficulties = {}
for q in data['questions']:
    cat = q['category']
    diff = q['difficulty']
    categories[cat] = categories.get(cat, 0) + 1
    difficulties[diff] = difficulties.get(diff, 0) + 1

print("\n📊 Category Distribution:")
for k, v in sorted(categories.items()):
    print(f"  {k}: {v}")

print("\n📊 Difficulty Distribution:")
for k, v in sorted(difficulties.items()):
    print(f"  {k}: {v}")

# Validate
assert len(data['questions']) == 50, f"Expected 50, got {len(data['questions'])}"
assert categories.get('factual', 0) == 20, "Factual count mismatch"
assert categories.get('multi_hop', 0) == 15, "Multi-hop count mismatch"
assert categories.get('summarization', 0) == 10, "Summarization count mismatch"  
assert categories.get('edge_case', 0) == 5, "Edge case count mismatch"

print("\n🎉 Dataset COMPLETE: 50/50 questions with correct distribution!")
print("✅ Ready for Week 3 optimization experiments")
