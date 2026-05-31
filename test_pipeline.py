import sys
import os
import json
from pathlib import Path
import requests

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

def test_pipeline():
    print("=== Testing RAGPipeline Initialization ===")
    init_success = False
    try:
        from src.rag.pipeline import RAGPipeline
        print("Import successful. Initializing pipeline...")
        rp = RAGPipeline()
        print("Pipeline initialized successfully!")
        init_success = True
        
        # Test query inside Python
        print("Querying RAGPipeline directly...")
        query_text = "Berapa biaya membuat SIM A 2024?"
        result = rp.query(
            question=query_text,
            use_cache=False
        )
        print("Direct pipeline query result:")
        print(f"Answer: {result.get('answer')}")
        print(f"Sources: {result.get('sources')}")
        print(f"Confidence: {result.get('confidence')}")
        print(f"Model used: {result.get('model_used')}")
        
        # Write direct query result to a file
        with open("direct_query_result.json", "w", encoding="utf-8") as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
            
        print("OK")
    except Exception as e:
        print(f"Pipeline Test FAILED: {e}")
        import traceback
        traceback.print_exc()
    return init_success

def test_api():
    print("\n=== Testing API /query Endpoint ===")
    url = "http://localhost:8000/query"
    payload = {
        "query": "Berapa biaya membuat SIM A 2024?",
        "options": {
            "use_query_expansion": True,
            "use_reranking": False,
            "use_hybrid": True,
            "top_k": 3
        }
    }
    try:
        response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
        print(f"API Response Code: {response.status_code}")
        response_json = response.json()
        print("API Response Body:")
        print(json.dumps(response_json, indent=2, ensure_ascii=False))
        
        # Check if fallback was used
        metadata = response_json.get("metadata", {})
        status = metadata.get("status", "success")
        answer = response_json.get("answer", "")
        
        is_fallback = False
        if "fallback" in str(status) or status == "query_failed":
            is_fallback = True
        if "[Pencarian Dasar]" in answer or "sistem sedang dalam perbaikan" in answer:
            is_fallback = True
            
        if is_fallback:
            print(f"WARNING: The system returned a FALLBACK response (status: {status}).")
        else:
            print("SUCCESS: The system successfully returned an AI response instead of a fallback!")
            
        with open("api_query_result.json", "w", encoding="utf-8") as f:
            json.dump(response_json, f, indent=2, ensure_ascii=False)
            
    except Exception as e:
        print(f"API Test FAILED: {e}")

if __name__ == "__main__":
    init_ok = test_pipeline()
    if init_ok:
        test_api()
