#!/usr/bin/env python3
"""
Script to send test requests to the Carmen API.

Reads test requests from test_requests.json and sends them sequentially,
waiting for each response before sending the next request.
"""

import json
import requests
import time
import sys
from pathlib import Path
from typing import List, Dict, Any

# Configuration
API_URL = "http://localhost:8000/api/analyze"
REQUEST_DELAY = 0.5  # Small delay between requests (in seconds)

# Get the directory where this script is located
SCRIPT_DIR = Path(__file__).parent
TEST_REQUESTS_FILE = SCRIPT_DIR / "test_requests.json"


def load_test_requests() -> List[Dict[str, Any]]:
    """Load test requests from JSON file."""
    try:
        with open(TEST_REQUESTS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"Error: File not found: {TEST_REQUESTS_FILE}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in {TEST_REQUESTS_FILE}: {e}")
        sys.exit(1)


def send_request(date: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """
    Send a single request to the API.
    
    Args:
        date: ISO format date string for test_date parameter
        body: Request body with sensor data
        
    Returns:
        Response from the API
    """
    try:
        # Prepare the request
        params = {"test_date": date}
        headers = {"Content-Type": "application/json"}
        
        print(f"📤 Sending request for {date}...")
        print(f"   Plant: {body.get('plant_id')} ({body.get('plant_type')})")
        print(f"   Data: humidity={body.get('humidity')}%, light={body.get('light')} lux, temp={body.get('temperature')}°C")
        
        # Send the request and wait for response
        response = requests.post(
            API_URL,
            params=params,
            json=body,
            headers=headers,
            timeout=60  # 60 second timeout
        )
        
        # Check response status
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ Response received: {result.get('status')} - {result.get('message', '')[:50]}...")
        print(f"   Action: {result.get('action', 'N/A')[:60]}...")
        print()
        
        return result
        
    except requests.exceptions.ConnectionError:
        print(f"❌ Error: Could not connect to {API_URL}")
        print("   Make sure the server is running!")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"❌ Error: Request timed out after 60 seconds")
        return None
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error: HTTP {response.status_code} - {e}")
        try:
            error_detail = response.json()
            print(f"   Details: {error_detail}")
        except:
            print(f"   Response: {response.text}")
        return None
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        return None


def main():
    """Main function to send all test requests."""
    print("=" * 70)
    print("🧪 Carmen API Test Request Sender")
    print("=" * 70)
    print(f"API URL: {API_URL}")
    print(f"Test requests file: {TEST_REQUESTS_FILE}")
    print()
    
    # Load test requests
    test_requests = load_test_requests()
    total_requests = len(test_requests)
    
    print(f"📋 Loaded {total_requests} test requests")
    print()
    
    # Confirm before sending
    response = input("Do you want to send all requests? (y/n): ").strip().lower()
    if response != 'y':
        print("Cancelled.")
        sys.exit(0)
    
    print()
    print("🚀 Starting to send requests...")
    print("=" * 70)
    print()
    
    # Track statistics
    successful = 0
    failed = 0
    start_time = time.time()
    
    # Send each request sequentially
    for i, request_data in enumerate(test_requests, 1):
        date = request_data.get("date")
        body = request_data.get("body")
        
        if not date or not body:
            print(f"⚠️  Skipping request {i}: missing date or body")
            failed += 1
            continue
        
        print(f"[{i}/{total_requests}] ", end="")
        
        result = send_request(date, body)
        
        if result:
            successful += 1
        else:
            failed += 1
        
        # Small delay between requests (except for the last one)
        if i < total_requests:
            time.sleep(REQUEST_DELAY)
    
    # Print summary
    elapsed_time = time.time() - start_time
    print("=" * 70)
    print("📊 Summary")
    print("=" * 70)
    print(f"Total requests: {total_requests}")
    print(f"✅ Successful: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"⏱️  Total time: {elapsed_time:.2f} seconds")
    print(f"📈 Average time per request: {elapsed_time/total_requests:.2f} seconds")
    print()
    
    if successful == total_requests:
        print("🎉 All requests completed successfully!")
    else:
        print(f"⚠️  {failed} request(s) failed. Check the errors above.")


if __name__ == "__main__":
    main()
