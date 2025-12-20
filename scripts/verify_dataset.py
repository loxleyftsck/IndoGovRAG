import json

# Load dataset
with open('data/eval_dataset_50q.json', encoding='utf-8') as f:
    data = json.load(f)

# Count
total = len(data['questions'])
print(f"✅ Total questions: {total}")

# Category distribution
categories = {}
for q in data['questions']:
    cat = q['category']
    categories[cat] = categories.get(cat, 0) + 1

print(f"\n📊 Category Distribution:")
for cat, count in categories.items():
    print(f"  {cat}: {count}")

# Difficulty distribution  
difficulties = {}
for q in data['questions']:
    diff = q['difficulty']
    difficulties[diff] = difficulties.get(diff, 0) + 1

print(f"\n📈 Difficulty Distribution:")
for diff, count in difficulties.items():
    print(f"  {diff}: {count}")

# Validation
print(f"\n✅ Dataset Status: {'COMPLETE' if total == 50 else 'INCOMPLETE'}")
print(f"   Expected: 50")
print(f"   Actual: {total}")
