#!/usr/bin/env python3
"""
Corpus Validator - Quality checks for vector database
Ensures sufficient coverage and data quality
"""
from src.retrieval.vector_search import VectorStore
import sys

def validate_corpus():
    """Run all validation checks"""
    print("🔍 CORPUS VALIDATION")
    print("=" * 60)
    
    vs = VectorStore()
    
    # CHECK 1: Minimum count
    print("\n1. Checking chunk count...")
    total = vs.collection.count()
    print(f"   Total chunks: {total}")
    
    if total < 50:
        print("   ❌ FAIL: Need at least 50 chunks for basic functionality")
        return False
    elif total < 200:
        print("   ⚠️ WARNING: Less than 200 chunks (recommended for production)")
    else:
        print("   ✅ PASS: Sufficient chunks for production")
    
    # CHECK 2: Coverage
    print("\n2. Checking topic coverage...")
    test_queries = {
        "KTP elektronik": "Administrasi kependudukan",
        "NPWP": "Perpajakan",
        "BPJS": "Jaminan sosial",
        "Paspor": "Keimigrasian",
        "SIM": "Lalu lintas"
    }
    
    coverage_pass = 0
    for query, topic in test_queries.items():
        results = vs.search(query, n_results=3)
        if len(results) > 0:
            print(f"   ✅ {query}: {len(results)} chunks found")
            coverage_pass += 1
        else:
            print(f"   ❌ {query}: No data found")
    
    coverage_rate = (coverage_pass / len(test_queries)) * 100
    print(f"\n   Coverage: {coverage_rate:.0f}% ({coverage_pass}/{len(test_queries)} topics)")
    
    if coverage_rate < 60:
        print("   ❌ FAIL: Coverage too low") 
        return False
    
    # CHECK 3: Quality
    print("\n3. Checking chunk quality...")
    sample = vs.search("persyaratan", n_results=5)
    
    quality_pass = 0
    for i, chunk in enumerate(sample, 1):
        checks = {
            'text_length': len(chunk.text) > 100,
            'has_metadata': hasattr(chunk, 'metadata'),
            'metadata_not_empty': bool(chunk.metadata) if hasattr(chunk, 'metadata') else False
        }
        
        if all(checks.values()):
            quality_pass += 1
            print(f"   ✅ Chunk {i}: Quality OK")
        else:
            print(f"   ⚠️ Chunk {i}: Quality issues - {checks}")
    
    quality_rate = (quality_pass / len(sample)) * 100 if sample else 0
    print(f"\n   Quality: {quality_rate:.0f}% ({quality_pass}/{len(sample)} chunks)")
    
    # SUMMARY
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print(f"   Chunks: {total}")
    print(f"   Coverage: {coverage_rate:.0f}%")
    print(f"   Quality: {quality_rate:.0f}%")
    
    if total >= 200 and coverage_rate >= 80 and quality_rate >= 80:
        print("\n✅ PRODUCTION READY!")
        return True
    elif total >= 50 and coverage_rate >= 60:
        print("\n⚠️ STAGING READY (needs improvement)")
        return True
    else:
        print("\n❌ NOT READY (needs more data)")
        return False

if __name__ == "__main__":
    success = validate_corpus()
    sys.exit(0 if success else 1)
