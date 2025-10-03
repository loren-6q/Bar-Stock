#!/usr/bin/env python3

import requests
import json
from datetime import datetime

def test_purchase_management():
    base_url = "https://stocktrackr-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🧪 Testing Purchase Management APIs")
    print("=" * 50)
    
    # First, initialize data and get items
    print("📋 Initializing data...")
    init_response = requests.post(f"{api_url}/initialize-real-data")
    print(f"Init status: {init_response.status_code}")
    
    # Get items
    items_response = requests.get(f"{api_url}/items")
    items = items_response.json()
    test_item_id = items[0]['id']
    print(f"Using test item: {items[0]['name']} (ID: {test_item_id})")
    
    # Create a stock session
    print("\n🗂️  Creating stock session...")
    session_data = {
        "session_name": "Purchase Test Session",
        "session_type": "full_count",
        "notes": "Testing purchase functionality"
    }
    session_response = requests.post(f"{api_url}/stock-sessions", json=session_data)
    print(f"Session creation status: {session_response.status_code}")
    
    if session_response.status_code == 200:
        session = session_response.json()
        session_id = session['id']
        print(f"Created session: {session_id}")
        
        # Test purchase creation
        print("\n💰 Testing purchase creation...")
        purchase_data = {
            "session_id": session_id,
            "item_id": test_item_id,
            "planned_quantity": 120,
            "actual_quantity": 150,
            "cost_per_unit": 44.0,
            "total_cost": 6600.0,
            "supplier": "Singha99",
            "notes": "Test purchase entry"
        }
        
        purchase_response = requests.post(f"{api_url}/purchases", json=purchase_data)
        print(f"Purchase creation status: {purchase_response.status_code}")
        print(f"Purchase response: {purchase_response.text}")
        
        if purchase_response.status_code == 200:
            purchase = purchase_response.json()
            purchase_id = purchase['id']
            print(f"✅ Created purchase: {purchase_id}")
            
            # Test getting session purchases
            print("\n📋 Testing get session purchases...")
            get_purchases_response = requests.get(f"{api_url}/purchases/session/{session_id}")
            print(f"Get purchases status: {get_purchases_response.status_code}")
            print(f"Purchases found: {len(get_purchases_response.json())}")
            
            # Test purchase update
            print("\n✏️  Testing purchase update...")
            update_data = purchase_data.copy()
            update_data['actual_quantity'] = 140
            update_data['total_cost'] = 6160.0
            update_data['notes'] = "Updated purchase"
            
            update_response = requests.put(f"{api_url}/purchases/{purchase_id}", json=update_data)
            print(f"Update status: {update_response.status_code}")
            print(f"Update response: {update_response.text}")
            
            # Test purchase deletion
            print("\n🗑️  Testing purchase deletion...")
            delete_response = requests.delete(f"{api_url}/purchases/{purchase_id}")
            print(f"Delete status: {delete_response.status_code}")
            print(f"Delete response: {delete_response.text}")
            
        else:
            print(f"❌ Failed to create purchase: {purchase_response.text}")
    else:
        print(f"❌ Failed to create session: {session_response.text}")

if __name__ == "__main__":
    test_purchase_management()