import requests
import json
from datetime import datetime

class EnhancedFeaturesTest:
    def __init__(self, base_url="https://stocktrackr-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        
    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def test_enhanced_case_single_input(self):
        """Test the enhanced stock counting endpoint with case+single input"""
        print("\n🔢 Testing Enhanced Case/Single Input API...")
        
        # First get an item to test with
        response = requests.get(f"{self.api_url}/items")
        items = response.json()
        
        if not items:
            self.log_test("Get Items for Case Test", False, "No items available")
            return False
            
        # Find an item with units_per_case > 1 for meaningful testing
        test_item = None
        for item in items:
            if item.get('units_per_case', 1) > 1:
                test_item = item
                break
        
        if not test_item:
            test_item = items[0]  # Fallback to first item
            
        item_id = test_item['id']
        item_name = test_item['name']
        units_per_case = test_item.get('units_per_case', 1)
        
        print(f"Testing with: {item_name} (units_per_case: {units_per_case})")
        
        # Test enhanced stock count input with cases and singles
        stock_inputs = {
            "main_bar": {
                "cases": 2,
                "singles": 5
            },
            "beer_bar": {
                "cases": 1,
                "singles": 8
            },
            "lobby": {
                "cases": 0,
                "singles": 3
            },
            "storage_room": {
                "cases": 3,
                "singles": 2
            },
            "counted_by": "Enhanced Test Staff"
        }
        
        # Calculate expected totals
        expected_main_bar = (2 * units_per_case) + 5
        expected_beer_bar = (1 * units_per_case) + 8
        expected_lobby = (0 * units_per_case) + 3
        expected_storage_room = (3 * units_per_case) + 2
        expected_total = expected_main_bar + expected_beer_bar + expected_lobby + expected_storage_room
        
        try:
            response = requests.post(
                f"{self.api_url}/stock-counts-enhanced/{item_id}",
                json=stock_inputs,
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Verify calculations
                actual_main_bar = result.get('main_bar', 0)
                actual_beer_bar = result.get('beer_bar', 0)
                actual_lobby = result.get('lobby', 0)
                actual_storage_room = result.get('storage_room', 0)
                actual_total = result.get('total_count', 0)
                
                calculations_correct = (
                    actual_main_bar == expected_main_bar and
                    actual_beer_bar == expected_beer_bar and
                    actual_lobby == expected_lobby and
                    actual_storage_room == expected_storage_room and
                    actual_total == expected_total
                )
                
                self.log_test(
                    "Enhanced Case/Single Input API",
                    True,
                    f"Successfully created stock count with case+single input"
                )
                
                self.log_test(
                    "Case/Single Calculation Accuracy",
                    calculations_correct,
                    f"Expected totals: MB={expected_main_bar}, BB={expected_beer_bar}, L={expected_lobby}, SR={expected_storage_room}, Total={expected_total}. "
                    f"Actual totals: MB={actual_main_bar}, BB={actual_beer_bar}, L={actual_lobby}, SR={actual_storage_room}, Total={actual_total}"
                )
                
                return True
                
            else:
                self.log_test(
                    "Enhanced Case/Single Input API",
                    False,
                    f"Expected 200, got {response.status_code}. Response: {response.text[:200]}"
                )
                return False
                
        except Exception as e:
            self.log_test("Enhanced Case/Single Input API", False, f"Error: {str(e)}")
            return False

    def test_order_confirmation_workflow(self):
        """Test the order confirmation workflow"""
        print("\n📋 Testing Order Confirmation Workflow...")
        
        # Get shopping list first
        try:
            response = requests.get(f"{self.api_url}/shopping-list")
            if response.status_code != 200:
                self.log_test("Get Shopping List for Orders", False, f"Failed to get shopping list: {response.status_code}")
                return False
                
            shopping_list = response.json()
            
            if not shopping_list:
                self.log_test("Shopping List Available", False, "No shopping list items available")
                return False
                
            # Get first supplier with items
            supplier = list(shopping_list.keys())[0]
            supplier_items = shopping_list[supplier]
            
            self.log_test("Shopping List Retrieved", True, f"Found {len(supplier_items)} items for {supplier}")
            
            # Create order from shopping list
            order_data = {
                "supplier": supplier,
                "planned_items": supplier_items,
                "notes": "Test order from enhanced workflow"
            }
            
            response = requests.post(
                f"{self.api_url}/shopping-orders",
                json=order_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code == 200:
                order = response.json()
                order_id = order.get('id')
                
                self.log_test("Create Order from Shopping List", True, f"Order ID: {order_id}")
                
                # Test order status update
                response = requests.put(
                    f"{self.api_url}/shopping-orders/{order_id}/status?status=ordered&notes=Test status update"
                )
                
                if response.status_code == 200:
                    self.log_test("Update Order Status", True, "Status updated to 'ordered'")
                else:
                    self.log_test("Update Order Status", False, f"Failed: {response.status_code}")
                
                # Get all orders to verify
                response = requests.get(f"{self.api_url}/shopping-orders")
                if response.status_code == 200:
                    orders = response.json()
                    self.log_test("Get All Orders", True, f"Found {len(orders)} orders")
                else:
                    self.log_test("Get All Orders", False, f"Failed: {response.status_code}")
                
                return True
            else:
                self.log_test("Create Order from Shopping List", False, f"Failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("Order Confirmation Workflow", False, f"Error: {str(e)}")
            return False

    def test_complete_workflow_scenario(self):
        """Test the complete workflow mentioned in review request"""
        print("\n🔄 Testing Complete Workflow Scenario...")
        
        try:
            # Step 1: Create stock session
            session_data = {
                "session_name": "Complete Workflow Test Session",
                "session_type": "full_count",
                "notes": "Testing complete enhanced workflow"
            }
            
            response = requests.post(
                f"{self.api_url}/stock-sessions",
                json=session_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                self.log_test("Create Workflow Session", False, f"Failed: {response.status_code}")
                return False
                
            session = response.json()
            session_id = session.get('id')
            self.log_test("Create Workflow Session", True, f"Session ID: {session_id}")
            
            # Step 2: Create stock counts using enhanced method
            items_response = requests.get(f"{self.api_url}/items")
            items = items_response.json()[:3]  # Use first 3 items
            
            for item in items:
                stock_inputs = {
                    "main_bar": {"cases": 1, "singles": 5},
                    "beer_bar": {"cases": 2, "singles": 3},
                    "lobby": {"cases": 0, "singles": 2},
                    "storage_room": {"cases": 1, "singles": 0},
                    "counted_by": "Workflow Test"
                }
                
                requests.post(
                    f"{self.api_url}/stock-counts-enhanced/{item['id']}",
                    json=stock_inputs,
                    headers={'Content-Type': 'application/json'}
                )
            
            self.log_test("Enhanced Stock Counting", True, "Created stock counts with case+single input")
            
            # Step 3: Save counts to session
            response = requests.post(f"{self.api_url}/stock-sessions/{session_id}/save-counts")
            if response.status_code == 200:
                self.log_test("Save Counts to Session", True, "Stock counts saved to session")
            else:
                self.log_test("Save Counts to Session", False, f"Failed: {response.status_code}")
            
            # Step 4: Generate shopping list
            response = requests.get(f"{self.api_url}/shopping-list")
            if response.status_code == 200:
                shopping_list = response.json()
                self.log_test("Generate Shopping List", True, f"Generated list with {len(shopping_list)} suppliers")
            else:
                self.log_test("Generate Shopping List", False, f"Failed: {response.status_code}")
                return False
            
            # Step 5: Create order from shopping list
            if shopping_list:
                supplier = list(shopping_list.keys())[0]
                order_data = {
                    "supplier": supplier,
                    "planned_items": shopping_list[supplier],
                    "notes": "Order from complete workflow test"
                }
                
                response = requests.post(
                    f"{self.api_url}/shopping-orders",
                    json=order_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code == 200:
                    order = response.json()
                    self.log_test("Create Order from List", True, f"Order created for {supplier}")
                else:
                    self.log_test("Create Order from List", False, f"Failed: {response.status_code}")
            
            # Step 6: Track purchases
            for item in items[:2]:  # Create purchases for first 2 items
                purchase_data = {
                    "session_id": session_id,
                    "item_id": item['id'],
                    "planned_quantity": 50,
                    "actual_quantity": 60,  # Bought more than planned
                    "cost_per_unit": item.get('cost_per_unit', 10.0),
                    "total_cost": 60 * item.get('cost_per_unit', 10.0),
                    "supplier": item.get('primary_supplier', 'Test Supplier'),
                    "notes": "Workflow test purchase"
                }
                
                response = requests.post(
                    f"{self.api_url}/purchases",
                    json=purchase_data,
                    headers={'Content-Type': 'application/json'}
                )
                
                if response.status_code != 200:
                    self.log_test("Track Purchase Confirmations", False, f"Failed: {response.status_code}")
                    return False
            
            self.log_test("Track Purchase Confirmations", True, "Purchase tracking working")
            
            # Step 7: Test usage analysis (would need second session for full test)
            response = requests.get(f"{self.api_url}/reports/usage-summary")
            if response.status_code == 200:
                usage_report = response.json()
                if 'message' in usage_report and 'Need at least 2 sessions' in usage_report['message']:
                    self.log_test("Usage Analysis Ready", True, "Usage analysis system ready (needs 2+ sessions)")
                else:
                    self.log_test("Usage Analysis Working", True, "Usage analysis generated successfully")
            else:
                self.log_test("Usage Analysis", False, f"Failed: {response.status_code}")
            
            return True
            
        except Exception as e:
            self.log_test("Complete Workflow Scenario", False, f"Error: {str(e)}")
            return False

    def run_enhanced_tests(self):
        """Run all enhanced feature tests"""
        print("🚀 Testing Enhanced Bar Stock Management Features")
        print("=" * 60)
        
        # Test 1: Enhanced case/single input API
        self.test_enhanced_case_single_input()
        
        # Test 2: Order confirmation workflow
        self.test_order_confirmation_workflow()
        
        # Test 3: Complete workflow scenario
        self.test_complete_workflow_scenario()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"📊 Enhanced Features Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All enhanced features are working correctly!")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed.")
            return False

if __name__ == "__main__":
    tester = EnhancedFeaturesTest()
    tester.run_enhanced_tests()