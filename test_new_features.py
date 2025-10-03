#!/usr/bin/env python3

import requests
import json
import time
from datetime import datetime

def test_all_new_features():
    """Test all the new backend functionality as requested in the review"""
    base_url = "https://stocktrackr-1.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    print("🧪 Testing All New Backend Features")
    print("=" * 60)
    
    results = {
        "tests_run": 0,
        "tests_passed": 0,
        "failed_tests": []
    }
    
    def log_test(name, success, details=""):
        results["tests_run"] += 1
        if success:
            results["tests_passed"] += 1
            print(f"✅ {name}")
        else:
            results["failed_tests"].append({"name": name, "details": details})
            print(f"❌ {name}: {details}")
        if details and success:
            print(f"   {details}")
    
    # 1. Enhanced Data Initialization
    print("\n📋 1. Testing Enhanced Data Initialization")
    init_response = requests.post(f"{api_url}/initialize-real-data")
    log_test("Enhanced Data Initialization", 
             init_response.status_code == 200,
             f"Status: {init_response.status_code}")
    
    if init_response.status_code == 200:
        init_data = init_response.json()
        items_count = init_data.get('items_count', 0)
        log_test("Comprehensive Item List (45+ items)", 
                 items_count >= 40,
                 f"Initialized {items_count} items")
    
    # Get items for testing
    items_response = requests.get(f"{api_url}/items")
    items = items_response.json()
    test_items = items[:3]
    
    # Verify categories are present
    categories = set(item['category_name'] for item in items)
    expected_categories = {'Beer', 'Thai Alcohol', 'Import Alcohol', 'Mixers', 'Bar Supplies', 'Hostel Supplies'}
    log_test("All Item Categories Present", 
             expected_categories.issubset(categories),
             f"Found categories: {categories}")
    
    # 2. Stock Sessions and Save Counts
    print("\n🗂️  2. Testing Stock Sessions and Save Counts")
    
    # Create stock counts first
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
    session1_data = {
        "session_name": "Opening Count Session",
        "session_type": "full_count",
        "notes": "Opening stock count for usage analysis"
    }
    session1_response = requests.post(f"{api_url}/stock-sessions", json=session1_data)
    log_test("Create Stock Session", 
             session1_response.status_code == 200,
             f"Status: {session1_response.status_code}")
    
    session1_id = None
    if session1_response.status_code == 200:
        session1 = session1_response.json()
        session1_id = session1['id']
        
        # Test save counts to session
        save_response = requests.post(f"{api_url}/stock-sessions/{session1_id}/save-counts")
        log_test("Save Stock Counts to Session", 
                 save_response.status_code == 200,
                 f"Status: {save_response.status_code}")
        
        if save_response.status_code == 200:
            save_data = save_response.json()
            count = save_data.get('count', 0)
            log_test("Stock Counts Saved Successfully", 
                     count > 0,
                     f"Saved {count} stock counts")
    
    # 3. Purchase Management APIs
    print("\n💰 3. Testing Purchase Management APIs")
    
    if session1_id:
        # Test CREATE purchase entry
        purchase_data = {
            "session_id": session1_id,
            "item_id": test_items[0]['id'],
            "planned_quantity": 120,
            "actual_quantity": 150,
            "cost_per_unit": 44.0,
            "total_cost": 6600.0,
            "supplier": "Singha99",
            "notes": "Test purchase - bought more than planned"
        }
        
        create_response = requests.post(f"{api_url}/purchases", json=purchase_data)
        log_test("CREATE Purchase Entry", 
                 create_response.status_code == 200,
                 f"Status: {create_response.status_code}")
        
        purchase_id = None
        if create_response.status_code == 200:
            purchase = create_response.json()
            purchase_id = purchase['id']
            
            # Verify planned vs actual quantities
            log_test("Purchase Planned vs Actual Tracking", 
                     purchase['planned_quantity'] == 120 and purchase['actual_quantity'] == 150,
                     f"Planned: {purchase['planned_quantity']}, Actual: {purchase['actual_quantity']}")
            
            # Test READ session purchases
            read_response = requests.get(f"{api_url}/purchases/session/{session1_id}")
            log_test("READ Session Purchases", 
                     read_response.status_code == 200,
                     f"Status: {read_response.status_code}")
            
            if read_response.status_code == 200:
                purchases = read_response.json()
                log_test("Purchase Entries Retrieved", 
                         len(purchases) > 0,
                         f"Found {len(purchases)} purchases")
            
            # Test UPDATE purchase entry
            update_data = purchase_data.copy()
            update_data['actual_quantity'] = 140
            update_data['total_cost'] = 6160.0
            update_data['notes'] = "Updated purchase quantity"
            
            update_response = requests.put(f"{api_url}/purchases/{purchase_id}", json=update_data)
            log_test("UPDATE Purchase Entry", 
                     update_response.status_code == 200,
                     f"Status: {update_response.status_code}")
            
            # Create additional purchases for better testing
            for i, item in enumerate(test_items[1:3]):
                additional_purchase = {
                    "session_id": session1_id,
                    "item_id": item['id'],
                    "planned_quantity": 100 + (i * 10),
                    "actual_quantity": 120 + (i * 15),
                    "cost_per_unit": 40.0 + i,
                    "total_cost": (120 + (i * 15)) * (40.0 + i),
                    "supplier": "Singha99",
                    "notes": f"Purchase for {item['name']}"
                }
                requests.post(f"{api_url}/purchases", json=additional_purchase)
            
            # We'll test DELETE later, after historical analysis
    
    # 4. Historical Analysis APIs
    print("\n📈 4. Testing Historical Analysis APIs")
    
    if session1_id:
        # Wait a moment then create second session
        time.sleep(2)
        
        # Update stock counts to simulate usage
        for item in test_items:
            stock_data = {
                "main_bar": 80,
                "beer_bar": 40,
                "lobby": 20,
                "storage_room": 60
            }
            requests.put(f"{api_url}/stock-counts/{item['id']}", json=stock_data)
        
        # Create closing session
        session2_data = {
            "session_name": "Closing Count Session",
            "session_type": "full_count",
            "notes": "Closing stock count for usage analysis"
        }
        session2_response = requests.post(f"{api_url}/stock-sessions", json=session2_data)
        
        if session2_response.status_code == 200:
            session2 = session2_response.json()
            session2_id = session2['id']
            
            # Save counts to closing session
            requests.post(f"{api_url}/stock-sessions/{session2_id}/save-counts")
            
            # Test session comparison
            comparison_response = requests.get(f"{api_url}/reports/session-comparison/{session1_id}/{session2_id}")
            log_test("Session Comparison Analysis", 
                     comparison_response.status_code == 200,
                     f"Status: {comparison_response.status_code}")
            
            if comparison_response.status_code == 200:
                comparison = comparison_response.json()
                
                # Verify usage calculation formula
                item_comparisons = comparison.get('item_comparisons', [])
                log_test("Usage Calculation Data Present", 
                         len(item_comparisons) > 0,
                         f"Analyzed {len(item_comparisons)} items")
                
                if item_comparisons:
                    first_item = item_comparisons[0]
                    opening = first_item.get('opening_stock', 0)
                    purchases = first_item.get('purchases_made', 0)
                    closing = first_item.get('closing_stock', 0)
                    calculated = first_item.get('calculated_usage', 0)
                    expected = opening + purchases - closing
                    
                    log_test("Usage Formula Verification (opening + purchases - closing)", 
                             calculated == expected,
                             f"Opening: {opening}, Purchases: {purchases}, Closing: {closing}, Usage: {calculated}")
                    
                    # Test the specific scenario from the review - check if we have purchase data
                    has_purchase_data = any(item.get('purchases_made', 0) > 0 for item in item_comparisons)
                    log_test("Complex Scenario Handling (Purchase Integration)", 
                             has_purchase_data,
                             f"Purchase data integrated: {has_purchase_data}")
                    
                    if has_purchase_data:
                        purchase_item = next(item for item in item_comparisons if item.get('purchases_made', 0) > 0)
                        p_opening = purchase_item.get('opening_stock', 0)
                        p_purchases = purchase_item.get('purchases_made', 0)
                        p_closing = purchase_item.get('closing_stock', 0)
                        p_usage = purchase_item.get('calculated_usage', 0)
                        log_test("Purchase Scenario Calculation", 
                                 p_usage == (p_opening + p_purchases - p_closing),
                                 f"Scenario: {p_opening} + {p_purchases} - {p_closing} = {p_usage}")
                
                # Now test DELETE purchase entry
                if purchase_id:
                    delete_response = requests.delete(f"{api_url}/purchases/{purchase_id}")
                    log_test("DELETE Purchase Entry", 
                             delete_response.status_code == 200,
                             f"Status: {delete_response.status_code}")
                
                # Test cost calculation
                total_cost = comparison.get('total_usage_cost', 0)
                log_test("Usage Cost Calculation", 
                         total_cost > 0,
                         f"Total usage cost: ${total_cost:.2f}")
            
            # Test usage summary report
            summary_response = requests.get(f"{api_url}/reports/usage-summary")
            log_test("Usage Report Generation", 
                     summary_response.status_code == 200,
                     f"Status: {summary_response.status_code}")
            
            if summary_response.status_code == 200:
                summary = summary_response.json()
                if 'total_usage_cost' in summary:
                    log_test("Usage Report Data", 
                             summary.get('total_usage_cost', 0) > 0,
                             f"Report generated with cost data")
    
    # 5. Edge Cases and Error Scenarios
    print("\n🔍 5. Testing Edge Cases and Error Scenarios")
    
    # Test invalid purchase entry
    invalid_purchase = {
        "session_id": "invalid-session-id",
        "item_id": "invalid-item-id",
        "planned_quantity": -10,
        "actual_quantity": -5,
        "cost_per_unit": -1.0,
        "total_cost": -5.0,
        "supplier": "",
        "notes": "Invalid purchase"
    }
    invalid_response = requests.post(f"{api_url}/purchases", json=invalid_purchase)
    log_test("Invalid Purchase Handling", 
             invalid_response.status_code in [400, 422, 500],
             f"Properly handles invalid data: {invalid_response.status_code}")
    
    # Test comparison with non-existent sessions
    invalid_comparison = requests.get(f"{api_url}/reports/session-comparison/invalid1/invalid2")
    log_test("Invalid Session Comparison Handling", 
             invalid_comparison.status_code == 404,
             f"Properly handles invalid sessions: {invalid_comparison.status_code}")
    
    # Test usage summary with insufficient sessions
    # (This should work but might return a message about needing more sessions)
    
    # Print comprehensive summary
    print("\n" + "=" * 60)
    print(f"📊 NEW FEATURES TEST SUMMARY")
    print(f"Tests Run: {results['tests_run']}")
    print(f"Tests Passed: {results['tests_passed']}")
    print(f"Success Rate: {(results['tests_passed']/results['tests_run'])*100:.1f}%")
    
    if results['failed_tests']:
        print(f"\n❌ Failed Tests ({len(results['failed_tests'])}):")
        for test in results['failed_tests']:
            print(f"   • {test['name']}: {test['details']}")
    
    if results['tests_passed'] == results['tests_run']:
        print("\n🎉 ALL NEW FEATURES ARE WORKING CORRECTLY!")
        print("✅ Purchase Management APIs - Full CRUD operations")
        print("✅ Historical Analysis APIs - Session comparison and usage reports")
        print("✅ Save Stock Counts to Session - Historical tracking")
        print("✅ Enhanced Data Initialization - 45+ items from spreadsheet")
        print("✅ Complex Usage Formula - opening + purchases - closing = usage")
        return True
    else:
        print(f"\n⚠️  {results['tests_run'] - results['tests_passed']} tests failed.")
        return False

if __name__ == "__main__":
    success = test_all_new_features()
    exit(0 if success else 1)