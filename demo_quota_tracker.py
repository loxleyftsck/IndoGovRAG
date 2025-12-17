"""
🧪 Demo Script: Gemini Quota Tracker
Test all features of the quota tracking system

Run: python demo_quota_tracker.py
"""

import os
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.monitoring.gemini_quota_tracker import (
    GeminiQuotaTracker,
    track_gemini_request,
    print_quota_status,
    check_throttle
)


def print_section(title: str):
    """Print section header."""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70 + "\n")


def demo_basic_tracking():
    """Demo 1: Basic quota tracking."""
    print_section("DEMO 1: Basic Quota Tracking")
    
    tracker = GeminiQuotaTracker(storage_path="data/demo_quota.json")
    
    print("📝 Simulating 5 API calls...\n")
    
    for i in range(5):
        result = tracker.track_request(
            input_tokens=400 + i*50,
            output_tokens=150 + i*30,
            query_preview=f"Demo query #{i+1}: What is RAG?"
        )
        
        print(f"✅ Request {i+1}:")
        print(f"   Input tokens:  {result['this_request']['input_tokens']}")
        print(f"   Output tokens: {result['this_request']['output_tokens']}")
        print(f"   Total tokens:  {result['this_request']['total_tokens']}")
        print(f"   Daily total:   {result['daily']['requests']}/{result['daily']['requests_limit']} requests")
        print(f"   Remaining:     {result['daily']['requests_remaining']} requests")
        
        if result["alerts"]:
            print("\n   🚨 ALERTS:")
            for alert in result["alerts"]:
                print(f"      {alert['message']}")
        
        print()
        time.sleep(0.3)
    
    print("\n📊 Final Status:")
    tracker.print_status()


def demo_helper_functions():
    """Demo 2: Quick helper functions."""
    print_section("DEMO 2: Quick Helper Functions")
    
    print("Using standalone helper functions...\n")
    
    # Track some requests
    for i in range(3):
        result = track_gemini_request(
            input_tokens=500,
            output_tokens=200,
            query_preview=f"Helper function test {i+1}"
        )
        print(f"✅ Tracked request {i+1}: {result['this_request']['total_tokens']} tokens")
        time.sleep(0.2)
    
    print("\n📊 Current Status:")
    print_quota_status()
    
    print("\n🔍 Checking throttle status...")
    if check_throttle():
        print("⏸️  Should throttle!")
    else:
        print("✅ All clear, no throttling needed")


def demo_alerts():
    """Demo 3: Alert system."""
    print_section("DEMO 3: Alert System Simulation")
    
    tracker = GeminiQuotaTracker(storage_path="data/demo_quota_alerts.json")
    
    print("Simulating high usage to trigger alerts...\n")
    
    # Simulate hitting 80% of daily limit
    requests_to_80_percent = int(tracker.FREE_TIER_LIMITS["rpd"] * 0.82)
    
    print(f"Simulating {requests_to_80_percent} requests to trigger WARNING alert...\n")
    
    # Fast-forward by manually setting counter
    tracker.data["daily_requests"] = requests_to_80_percent - 2
    tracker._save_data()
    
    # Make a few more requests to cross threshold
    for i in range(3):
        result = tracker.track_request(
            input_tokens=500,
            output_tokens=200,
            query_preview=f"Alert trigger test {i+1}"
        )
        
        print(f"Request {tracker.data['daily_requests']}:")
        
        if result["alerts"]:
            for alert in result["alerts"]:
                print(f"   {alert['message']}")
        else:
            print(f"   No alerts yet ({tracker.data['daily_requests']}/{tracker.FREE_TIER_LIMITS['rpd']})")
        
        time.sleep(0.2)
    
    print("\n📊 Status with alerts:")
    tracker.print_status()


def demo_throttle_check():
    """Demo 4: Throttle checking."""
    print_section("DEMO 4: Throttle Check & Prevention")
    
    tracker = GeminiQuotaTracker(storage_path="data/demo_quota_throttle.json")
    
    print("Simulating near-limit scenario...\n")
    
    # Simulate near daily limit
    tracker.data["daily_requests"] = int(tracker.FREE_TIER_LIMITS["rpd"] * 0.99)
    tracker._save_data()
    
    tracker.print_status()
    
    print("\n🔍 Checking if should throttle...")
    should_throttle, reason = tracker.should_throttle()
    
    if should_throttle:
        print(f"⏸️  THROTTLE RECOMMENDED!")
        print(f"   Reason: {reason}")
        print(f"   Action: Wait until quota resets (midnight)")
    else:
        print("✅ No throttling needed")


def demo_minute_limits():
    """Demo 5: Per-minute rate limiting."""
    print_section("DEMO 5: Per-Minute Rate Limits")
    
    tracker = GeminiQuotaTracker(storage_path="data/demo_quota_minute.json")
    
    print(f"Free tier limit: {tracker.FREE_TIER_LIMITS['rpm']} requests/minute\n")
    print("Simulating rapid requests...\n")
    
    for i in range(12):
        result = tracker.track_request(
            input_tokens=500,
            output_tokens=200,
            query_preview=f"Rapid request {i+1}"
        )
        
        rpm = result["minute"]["requests"]
        rpm_limit = result["minute"]["requests_limit"]
        rpm_percent = (rpm / rpm_limit) * 100
        
        print(f"Request {i+1:2d}: {rpm:2d}/{rpm_limit} RPM ({rpm_percent:5.1f}%)", end="")
        
        if result["alerts"]:
            alert_msgs = [a["message"] for a in result["alerts"] if "minute" in a["type"]]
            if alert_msgs:
                print(f" → {alert_msgs[0]}")
            else:
                print()
        else:
            print()
        
        time.sleep(0.1)
    
    print("\n📊 Final minute status:")
    status = tracker.get_status()
    print(f"Current minute: {status['minute']['requests']}/{status['minute']['requests_limit']} requests")
    print(f"Current minute: {status['minute']['tokens']:,}/{status['minute']['tokens_limit']:,} tokens")


def main():
    """Run all demos."""
    print("\n" + "🚀"*35)
    print("  GEMINI QUOTA TRACKER - DEMO SUITE")
    print("  100% FREE - Local JSON Tracking")
    print("🚀"*35)
    
    demos = [
        ("Basic Tracking", demo_basic_tracking),
        ("Helper Functions", demo_helper_functions),
        ("Alert System", demo_alerts),
        ("Throttle Check", demo_throttle_check),
        ("Minute Limits", demo_minute_limits),
    ]
    
    print("\nAvailable demos:")
    for i, (name, _) in enumerate(demos, 1):
        print(f"  {i}. {name}")
    print(f"  0. Run all demos")
    
    choice = input("\nSelect demo (0-5): ").strip()
    
    if choice == "0":
        for name, demo_func in demos:
            demo_func()
            input("\nPress Enter to continue to next demo...")
    elif choice in ["1", "2", "3", "4", "5"]:
        idx = int(choice) - 1
        demos[idx][1]()
    else:
        print("❌ Invalid choice")
        return
    
    print("\n" + "="*70)
    print("  ✅ Demo complete!")
    print("  📁 Check data/ folder for generated quota_tracking.json files")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
