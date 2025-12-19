import json

with open("data/eval_dataset_50q.json", encoding="utf-8") as f:
    data = json.load(f)

total = len(data["questions"])
print(f"✅ Total Questions: {total}")

categories = {}
for q in data["questions"]:
    cat = q["category"]
    categories[cat] = categories.get(cat, 0) + 1

print("\n📊 Category Counts:")
for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}")

if total == 50:
    print("\n🎉 SUCCESS: Dataset complete with 50 questions!")
else:
    print(f"\n⚠️ Expected 50, got {total}")
