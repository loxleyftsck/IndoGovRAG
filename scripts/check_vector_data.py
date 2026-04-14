"""Check vector store data"""
from src.retrieval.vector_search import VectorStore

vs = VectorStore()
total = vs.collection.count()

print(f"\n{'='*60}")
print(f"VECTOR STORE DATA CHECK")
print(f"{'='*60}")
print(f"Total documents: {total}")

# Get sample
results = vs.collection.get(limit=20, include=['documents', 'metadatas'])

print(f"\nSample documents (first 10):")
for i, meta in enumerate(results['metadatas'][:10], 1):
    source = meta.get('source', 'Unknown')
    print(f"  {i}. {source[:70]}")

# Check categories
print(f"\nDocument categories:")
categories = {}
for meta in results['metadatas']:
    doc_type = meta.get('doc_type', 'unknown')
    categories[doc_type] = categories.get(doc_type, 0) + 1

for cat, count in sorted(categories.items()):
    print(f"  {cat}: {count}")

print(f"{'='*60}\n")

if total < 50:
    print("⚠️  WARNING: Low document count (<50)")
    print("   Recommendation: Run Tier 2 scraper to enrich corpus")
elif total < 100:
    print("ℹ️  Document count adequate for basic testing")
    print("   Recommendation: Add more docs for production")
else:
    print("✅ Good document coverage!")
