#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

def test_historical_analysis():
    base_url = "https://liquor-inventory-9.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🧪 Testing Historical Analysis APIs")
    print("=" * 50)
    
    # Initialize data and get items
    print("📋 Initializing data...")
    init_response = requests.post(f"{api_url}/initialize-real-data")
    print(f"Init status: {init_response.status_code}")
    
    items_response = requests.get(f"{api_url}/items")
    items = items_response.json()
    test_items = items[:3]  # Use first 3 items
    
    # Create stock counts for opening session
    print("\n📊 Creating opening stock counts...")
    for item in test_items:
        stock_data = {
            "item_id": item['id'],
            "main_bar": 100,
            "beer_bar": 50,
            "lobby": 25,
            "storage_room": 75,
            "counted_by": "Test Staff"
        }
        requests.post(f"{api_url}/stock-counts", json=stock_data)
    
    # Create opening session
    print("\n🗂️  Creating opening session...")
    session1_data = {
        "session_name": "Opening Count",
        "session_type": "full_count",
        "notes": "Opening stock count for usage analysis"
    }
    session1_response = requests.post(f"{api_url}/stock-sessions", json=session1_data)
    session1 = session1_response.json()
    session1_id = session1['id']
    print(f"Created opening session: {session1_id}")
    
    # Save counts to opening session
    print("\n💾 Saving counts to opening session...")
    save_response = requests.post(f"{api_url}/stock-sessions/{session1_id}/save-counts")
    print(f"Save counts status: {save_response.status_code}")
    print(f"Save response: {save_response.json()}")
    
    # Create purchases for the session
    print("\n💰 Creating purchase entries...")
    for i, item in enumerate(test_items):
        purchase_data = {
            "session_id": session1_id,
            "item_id": item['id'],
            "planned_quantity": 120,
            "actual_quantity": 150 + (i * 10),  # Different quantities
            "cost_per_unit": 44.0 + i,
            "total_cost": (150 + (i * 10)) * (44.0 + i),
            "supplier": "Singha99",
            "notes": f"Purchase for {item['name']}"
        }
        purchase_response = requests.post(f"{api_url}/purchases", json=purchase_data)
        print(f"Created purchase for {item['name']}: {purchase_response.status_code}")
    
    # Wait a moment for different timestamps
    time.sleep(2)
    
    # Update stock counts to simulate usage
    print("\n📊 Updating stock counts to simulate usage...")
    for item in test_items:
        # Reduce stock to simulate consumption
        stock_data = {
            "main_bar": 80,
            "beer_bar": 40,
            "lobby": 20,
            "storage_room": 60
        }
        requests.put(f"{api_url}/stock-counts/{item['id']}", json=stock_data)
    
    # Create closing session
    print("\n🗂️  Creating closing session...")
    session2_data = {
        "session_name": "Closing Count",
        "session_type": "full_count",
        "notes": "Closing stock count for usage analysis"
    }
    session2_response = requests.post(f"{api_url}/stock-sessions", json=session2_data)
    session2 = session2_response.json()
    session2_id = session2['id']
    print(f"Created closing session: {session2_id}")
    
    # Save counts to closing session
    print("\n💾 Saving counts to closing session...")
    save2_response = requests.post(f"{api_url}/stock-sessions/{session2_id}/save-counts")
    print(f"Save counts status: {save2_response.status_code}")
    
    # Test session comparison
    print("\n📈 Testing session comparison...")
    comparison_response = requests.get(f"{api_url}/reports/session-comparison/{session1_id}/{session2_id}")
    print(f"Comparison status: {comparison_response.status_code}")
    
    if comparison_response.status_code == 200:
        comparison = comparison_response.json()
        print(f"✅ Session comparison successful!")
        print(f"Period days: {comparison.get('period_days', 0)}")
        print(f"Total usage cost: ${comparison.get('total_usage_cost', 0):.2f}")
        print(f"Items analyzed: {len(comparison.get('item_comparisons', []))}")
        
        # Check usage calculation for first item
        if comparison.get('item_comparisons'):
            first_item = comparison['item_comparisons'][0]
            opening = first_item.get('opening_stock', 0)
            purchases = first_item.get('purchases_made', 0)
            closing = first_item.get('closing_stock', 0)
            calculated = first_item.get('calculated_usage', 0)
            expected = opening + purchases - closing
            
            print(f"\n🧮 Usage calculation verification:")
            print(f"Opening: {opening}, Purchases: {purchases}, Closing: {closing}")
            print(f"Calculated usage: {calculated}, Expected: {expected}")
            print(f"Formula correct: {calculated == expected}")
    else:
        print(f"❌ Session comparison failed: {comparison_response.text}")
    
    # Test usage summary report
    print("\n📊 Testing usage summary report...")
    summary_response = requests.get(f"{api_url}/reports/usage-summary")
    print(f"Usage summary status: {summary_response.status_code}")
    
    if summary_response.status_code == 200:
        summary = summary_response.json()
        if 'message' in summary:
            print(f"Summary message: {summary['message']}")
        else:
            print(f"✅ Usage summary successful!")
            print(f"Total usage cost: ${summary.get('total_usage_cost', 0):.2f}")
    else:
        print(f"❌ Usage summary failed: {summary_response.text}")

if __name__ == "__main__":
    test_historical_analysis()