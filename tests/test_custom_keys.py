import json
import urllib.request
import urllib.error
import pytest
from fastapi.testclient import TestClient
from api.main import app

def make_request(headers, data):
    url = "http://127.0.0.1:8005/query"
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode("utf-8"),
        headers=headers,
        method="POST"
    )
    try:
        with urllib.request.urlopen(req) as response:
            return response.status, response.read().decode("utf-8"), None
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8"), e
    except Exception as e:
        return 0, "", e

def test_custom_groq_key_real_server():
    """Test against the running server at http://127.0.0.1:8005"""
    headers = {
        "Content-Type": "application/json",
        "X-Custom-Groq-Key": "gsk_invalid_test_key"
    }
    data = {
        "query": "Tes custom key",
        "options": {
            "use_cache": False
        }
    }
    
    print("\n[REAL SERVER TEST]")
    status_code, body, error = make_request(headers, data)
    print(f"Status Code: {status_code}")
    print(f"Response Body: {body}")
    if error:
        print(f"Error: {error}")

def test_custom_groq_key_in_process():
    """Test using FastAPI TestClient to verify custom key injection"""
    client = TestClient(app)
    headers = {
        "Content-Type": "application/json",
        "X-Custom-Groq-Key": "gsk_invalid_test_key"
    }
    data = {
        "query": "Tes custom key",
        "options": {
            "use_cache": False
        }
    }
    
    print("\n[IN-PROCESS CLIENT TEST]")
    response = client.post("/query", json=data, headers=headers)
    print(f"Status Code: {response.status_code}")
    print(f"Response Body: {response.text}")

if __name__ == "__main__":
    test_custom_groq_key_real_server()
