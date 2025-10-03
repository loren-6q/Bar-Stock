import requests
import sys
import json
from datetime import datetime
import time

class BarStockAPITester:
    def __init__(self, base_url="https://stocktrackr-1.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        self.test_session_id = None
        self.test_session2_id = None
        self.test_item_ids = []
        self.test_purchase_ids = []

    def log_test(self, name, success, details=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if details:
            print(f"    Details: {details}")

    def run_test(self, name, method, endpoint, expected_status, data=None, headers=None):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}"
        if headers is None:
            headers = {'Content-Type': 'application/json'}

        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)
            elif method == 'PUT':
                response = requests.put(url, json=data, headers=headers, timeout=10)
            elif method == 'DELETE':
                response = requests.delete(url, headers=headers, timeout=10)

            success = response.status_code == expected_status
            
            if success:
                try:
                    response_data = response.json()
                    details = f"Status: {response.status_code}, Response: {json.dumps(response_data, indent=2)[:200]}..."
                except:
                    details = f"Status: {response.status_code}, Response: {response.text[:200]}..."
            else:
                details = f"Expected {expected_status}, got {response.status_code}. Response: {response.text[:200]}..."

            self.log_test(name, success, details)
            return success, response.json() if success and response.text else {}

        except Exception as e:
            self.log_test(name, False, f"Error: {str(e)}")
            return False, {}

    def test_initialize_real_data(self):
        """Initialize enhanced real data from spreadsheet"""
        success, response = self.run_test(
            "Initialize Enhanced Real Data",
            "POST",
            "initialize-real-data",
            200
        )
        
        if success:
            items_count = response.get('items_count', 0)
            if items_count >= 40:  # Should have 45+ items
                self.log_test("Real Data Items Count", True, f"Initialized {items_count} items")
            else:
                self.log_test("Real Data Items Count", False, f"Expected 40+ items, got {items_count}")
        
        return success, response

    def test_get_items(self):
        """Test getting all items"""
        success, response = self.run_test(
            "Get All Items",
            "GET", 
            "items",
            200
        )
        
        if success and isinstance(response, list):
            self.log_test("Items Response Format", True, f"Found {len(response)} items")
            return True, response
        else:
            self.log_test("Items Response Format", False, "Response is not a list")
            return False, []

    def test_create_stock_count(self, item_id):
        """Test creating stock count"""
        stock_data = {
            "item_id": item_id,
            "main_bar": 10,
            "beer_bar": 15,
            "lobby": 5,
            "storage_room": 20,
            "counted_by": "Test Staff"
        }
        
        success, response = self.run_test(
            "Create Stock Count",
            "POST",
            "stock-counts",
            200,
            data=stock_data
        )
        
        if success:
            expected_total = 10 + 15 + 5 + 20  # 50
            actual_total = response.get('total_count', 0)
            if actual_total == expected_total:
                self.log_test("Stock Count Total Calculation", True, f"Total: {actual_total}")
            else:
                self.log_test("Stock Count Total Calculation", False, f"Expected {expected_total}, got {actual_total}")
        
        return success, response

    def test_update_stock_count(self, item_id):
        """Test updating stock count"""
        update_data = {
            "main_bar": 25,
            "beer_bar": 30
        }
        
        success, response = self.run_test(
            "Update Stock Count",
            "PUT",
            f"stock-counts/{item_id}",
            200,
            data=update_data
        )
        
        if success:
            # Check if the update worked correctly
            if response.get('main_bar') == 25 and response.get('beer_bar') == 30:
                self.log_test("Stock Count Update Values", True, "Values updated correctly")
            else:
                self.log_test("Stock Count Update Values", False, f"Update failed: {response}")
        
        return success, response

    def test_get_stock_counts(self):
        """Test getting all stock counts"""
        return self.run_test(
            "Get All Stock Counts",
            "GET",
            "stock-counts", 
            200
        )

    def test_get_shopping_list(self):
        """Test shopping list generation"""
        success, response = self.run_test(
            "Get Shopping List",
            "GET",
            "shopping-list",
            200
        )
        
        if success and isinstance(response, dict):
            suppliers = list(response.keys())
            self.log_test("Shopping List Format", True, f"Found suppliers: {suppliers}")
            
            # Check if shopping list has proper structure
            for supplier, items in response.items():
                if isinstance(items, list) and len(items) > 0:
                    first_item = items[0]
                    required_fields = ['item_name', 'current_stock', 'need_to_buy_units', 'estimated_cost']
                    has_all_fields = all(field in first_item for field in required_fields)
                    self.log_test(f"Shopping List Item Structure - {supplier}", has_all_fields, 
                                f"Item fields: {list(first_item.keys())}")
        
        return success, response

    def test_quick_restock(self):
        """Test quick restock endpoint"""
        return self.run_test(
            "Get Quick Restock",
            "GET",
            "quick-restock",
            200
        )

    # NEW PURCHASE MANAGEMENT TESTS
    def test_create_stock_session(self, session_name="Test Session"):
        """Test creating a stock session"""
        session_data = {
            "session_name": session_name,
            "session_type": "full_count",
            "notes": "Test session for purchase tracking"
        }
        
        success, response = self.run_test(
            f"Create Stock Session - {session_name}",
            "POST",
            "stock-sessions",
            200,
            data=session_data
        )
        
        if success:
            session_id = response.get('id')
            if session_id:
                if session_name == "Test Session":
                    self.test_session_id = session_id
                else:
                    self.test_session2_id = session_id
                self.log_test("Session ID Generated", True, f"Session ID: {session_id}")
            else:
                self.log_test("Session ID Generated", False, "No session ID in response")
        
        return success, response

    def test_create_purchase_entry(self, session_id, item_id):
        """Test creating a purchase entry"""
        purchase_data = {
            "session_id": session_id,
            "item_id": item_id,
            "planned_quantity": 120,  # From shopping list
            "actual_quantity": 150,   # What was actually bought
            "cost_per_unit": 44.0,
            "total_cost": 6600.0,     # 150 * 44
            "supplier": "Singha99",
            "notes": "Test purchase - bought more than planned"
        }
        
        success, response = self.run_test(
            "Create Purchase Entry",
            "POST",
            "purchases",
            200,
            data=purchase_data
        )
        
        if success:
            purchase_id = response.get('id')
            if purchase_id:
                self.test_purchase_ids.append(purchase_id)
                self.log_test("Purchase Entry Created", True, f"Purchase ID: {purchase_id}")
                
                # Verify calculation
                expected_total = purchase_data['actual_quantity'] * purchase_data['cost_per_unit']
                actual_total = response.get('total_cost', 0)
                if abs(actual_total - expected_total) < 0.01:
                    self.log_test("Purchase Cost Calculation", True, f"Total: {actual_total}")
                else:
                    self.log_test("Purchase Cost Calculation", False, f"Expected {expected_total}, got {actual_total}")
            else:
                self.log_test("Purchase Entry Created", False, "No purchase ID in response")
        
        return success, response

    def test_get_session_purchases(self, session_id):
        """Test getting purchases for a session"""
        success, response = self.run_test(
            "Get Session Purchases",
            "GET",
            f"purchases/session/{session_id}",
            200
        )
        
        if success and isinstance(response, list):
            self.log_test("Session Purchases Format", True, f"Found {len(response)} purchases")
            
            # Verify purchase structure
            if len(response) > 0:
                purchase = response[0]
                required_fields = ['id', 'session_id', 'item_id', 'planned_quantity', 'actual_quantity', 'total_cost']
                has_all_fields = all(field in purchase for field in required_fields)
                self.log_test("Purchase Entry Structure", has_all_fields, f"Fields: {list(purchase.keys())}")
        else:
            self.log_test("Session Purchases Format", False, "Response is not a list")
        
        return success, response

    def test_update_purchase_entry(self, purchase_id):
        """Test updating a purchase entry"""
        update_data = {
            "session_id": self.test_session_id,
            "item_id": self.test_item_ids[0] if self.test_item_ids else "test-item",
            "planned_quantity": 120,
            "actual_quantity": 140,  # Updated quantity
            "cost_per_unit": 44.0,
            "total_cost": 6160.0,    # 140 * 44
            "supplier": "Singha99",
            "notes": "Updated purchase quantity"
        }
        
        success, response = self.run_test(
            "Update Purchase Entry",
            "PUT",
            f"purchases/{purchase_id}",
            200,
            data=update_data
        )
        
        if success:
            actual_quantity = response.get('actual_quantity', 0)
            if actual_quantity == 140:
                self.log_test("Purchase Update Values", True, "Quantity updated correctly")
            else:
                self.log_test("Purchase Update Values", False, f"Expected 140, got {actual_quantity}")
        
        return success, response

    def test_delete_purchase_entry(self, purchase_id):
        """Test deleting a purchase entry"""
        success, response = self.run_test(
            "Delete Purchase Entry",
            "DELETE",
            f"purchases/{purchase_id}",
            200
        )
        
        if success:
            message = response.get('message', '')
            if 'deleted successfully' in message:
                self.log_test("Purchase Deletion Message", True, message)
            else:
                self.log_test("Purchase Deletion Message", False, f"Unexpected message: {message}")
        
        return success, response

    # HISTORICAL ANALYSIS TESTS
    def test_save_counts_to_session(self, session_id):
        """Test saving current stock counts to a session"""
        success, response = self.run_test(
            "Save Stock Counts to Session",
            "POST",
            f"stock-sessions/{session_id}/save-counts",
            200
        )
        
        if success:
            count = response.get('count', 0)
            if count > 0:
                self.log_test("Stock Counts Saved", True, f"Saved {count} stock counts")
            else:
                self.log_test("Stock Counts Saved", False, "No stock counts were saved")
        
        return success, response

    def test_session_comparison(self, session1_id, session2_id):
        """Test comparing two sessions for usage calculation"""
        success, response = self.run_test(
            "Session Comparison Analysis",
            "GET",
            f"reports/session-comparison/{session1_id}/{session2_id}",
            200
        )
        
        if success:
            # Verify response structure
            required_fields = ['session1_id', 'session2_id', 'item_comparisons', 'total_usage_cost', 'period_days']
            has_all_fields = all(field in response for field in required_fields)
            self.log_test("Session Comparison Structure", has_all_fields, f"Fields: {list(response.keys())}")
            
            # Check item comparisons
            item_comparisons = response.get('item_comparisons', [])
            if item_comparisons:
                first_item = item_comparisons[0]
                usage_fields = ['opening_stock', 'purchases_made', 'closing_stock', 'calculated_usage', 'usage_cost']
                has_usage_fields = all(field in first_item for field in usage_fields)
                self.log_test("Usage Calculation Fields", has_usage_fields, f"Item fields: {list(first_item.keys())}")
                
                # Verify usage calculation formula: opening + purchases - closing = usage
                opening = first_item.get('opening_stock', 0)
                purchases = first_item.get('purchases_made', 0)
                closing = first_item.get('closing_stock', 0)
                calculated = first_item.get('calculated_usage', 0)
                expected_usage = opening + purchases - closing
                
                if calculated == expected_usage:
                    self.log_test("Usage Formula Verification", True, f"Formula correct: {opening} + {purchases} - {closing} = {calculated}")
                else:
                    self.log_test("Usage Formula Verification", False, f"Expected {expected_usage}, got {calculated}")
            else:
                self.log_test("Item Comparisons Data", False, "No item comparisons found")
        
        return success, response

    def test_usage_summary_report(self):
        """Test getting usage summary report"""
        success, response = self.run_test(
            "Usage Summary Report",
            "GET",
            "reports/usage-summary",
            200
        )
        
        if success:
            # Check if it's a proper usage report or a message about insufficient sessions
            if 'message' in response:
                message = response.get('message', '')
                if 'Need at least 2 sessions' in message:
                    self.log_test("Usage Report Sessions Check", True, "Correctly requires 2+ sessions")
                else:
                    self.log_test("Usage Report Message", True, f"Message: {message}")
            else:
                # Should have the same structure as session comparison
                required_fields = ['session1_id', 'session2_id', 'item_comparisons', 'total_usage_cost']
                has_all_fields = all(field in response for field in required_fields)
                self.log_test("Usage Summary Structure", has_all_fields, f"Fields: {list(response.keys())}")
        
        return success, response

    def test_get_stock_sessions(self):
        """Test getting all stock sessions"""
        success, response = self.run_test(
            "Get Stock Sessions",
            "GET",
            "stock-sessions",
            200
        )
        
        if success and isinstance(response, list):
            self.log_test("Stock Sessions Format", True, f"Found {len(response)} sessions")
            
            if len(response) > 0:
                session = response[0]
                required_fields = ['id', 'session_name', 'session_date', 'is_active']
                has_all_fields = all(field in session for field in required_fields)
                self.log_test("Session Structure", has_all_fields, f"Fields: {list(session.keys())}")
        else:
            self.log_test("Stock Sessions Format", False, "Response is not a list")
        
        return success, response

    def test_get_current_session(self):
        """Test getting current active session"""
        success, response = self.run_test(
            "Get Current Session",
            "GET",
            "stock-sessions/current",
            200
        )
        
        if success:
            if response and 'id' in response:
                is_active = response.get('is_active', False)
                if is_active:
                    self.log_test("Current Session Active", True, f"Active session: {response.get('session_name')}")
                else:
                    self.log_test("Current Session Active", False, "Session is not marked as active")
            else:
                self.log_test("Current Session Response", True, "No current session (valid state)")
        
        return success, response

    def run_all_tests(self):
        """Run comprehensive API tests including new purchase management and historical analysis"""
        print("🧪 Starting Comprehensive Bar Stock API Tests")
        print("=" * 60)
        
        # Initialize enhanced real data first
        print("\n📋 Setting up enhanced test data...")
        init_success, init_response = self.test_initialize_real_data()
        
        if not init_success:
            print("❌ Failed to initialize enhanced real data. Stopping tests.")
            return False
        
        # Test items endpoint
        print("\n📦 Testing Items API...")
        items_success, items = self.test_get_items()
        
        if not items_success or not items:
            print("❌ No items found. Cannot continue with stock tests.")
            return False
        
        # Store test item IDs for later use
        self.test_item_ids = [item['id'] for item in items[:5]]  # Use first 5 items
        
        # Use first few items for comprehensive testing
        test_item_id = items[0]['id']
        test_item_name = items[0]['name']
        print(f"\n📊 Testing Stock Counts with item: {test_item_name} (ID: {test_item_id})")
        
        # Test stock count creation and updates
        create_success, _ = self.test_create_stock_count(test_item_id)
        update_success, _ = self.test_update_stock_count(test_item_id)
        
        # Create stock counts for multiple items to enable meaningful tests
        print("\n📊 Creating stock counts for multiple items...")
        for i, item in enumerate(items[:5]):
            if i > 0:  # Skip first item as it's already created
                self.test_create_stock_count(item['id'])
        
        # Test getting all stock counts
        print("\n📋 Testing Stock Count Retrieval...")
        self.test_get_stock_counts()
        
        # Test shopping list
        print("\n🛒 Testing Shopping List Generation...")
        self.test_get_shopping_list()
        
        # Test quick restock
        print("\n⚡ Testing Quick Restock...")
        self.test_quick_restock()
        
        # NEW TESTS: Stock Sessions and Purchase Management
        print("\n🗂️  Testing Stock Sessions...")
        session1_success, _ = self.test_create_stock_session("Opening Count Session")
        
        if session1_success and self.test_session_id:
            # Save current stock counts to first session
            print("\n💾 Testing Save Stock Counts to Session...")
            self.test_save_counts_to_session(self.test_session_id)
            
            # Test purchase management
            print("\n💰 Testing Purchase Management...")
            purchase_success, _ = self.test_create_purchase_entry(self.test_session_id, test_item_id)
            
            if purchase_success and self.test_purchase_ids:
                # Test getting session purchases
                self.test_get_session_purchases(self.test_session_id)
                
                # Test updating purchase entry
                self.test_update_purchase_entry(self.test_purchase_ids[0])
                
                # Create additional purchases for better testing
                for item_id in self.test_item_ids[1:3]:  # Create 2 more purchases
                    self.test_create_purchase_entry(self.test_session_id, item_id)
            
            # Wait a moment then create second session for comparison
            print("\n⏱️  Creating second session for historical analysis...")
            time.sleep(1)  # Ensure different timestamps
            
            # Update some stock counts to simulate usage
            print("\n📊 Simulating stock usage...")
            for item_id in self.test_item_ids[:3]:
                # Reduce stock to simulate consumption
                update_data = {
                    "main_bar": 5,
                    "beer_bar": 8,
                    "lobby": 2,
                    "storage_room": 15
                }
                self.run_test(f"Update Stock for Usage Simulation", "PUT", f"stock-counts/{item_id}", 200, data=update_data)
            
            session2_success, _ = self.test_create_stock_session("Closing Count Session")
            
            if session2_success and self.test_session2_id:
                # Save counts to second session
                self.test_save_counts_to_session(self.test_session2_id)
                
                # Test historical analysis
                print("\n📈 Testing Historical Analysis...")
                self.test_session_comparison(self.test_session_id, self.test_session2_id)
                
                # Test usage summary report
                self.test_usage_summary_report()
        
        # Test session management endpoints
        print("\n🗂️  Testing Session Management...")
        self.test_get_stock_sessions()
        self.test_get_current_session()
        
        # Clean up test data (delete one purchase to test deletion)
        if self.test_purchase_ids:
            print("\n🗑️  Testing Purchase Deletion...")
            self.test_delete_purchase_entry(self.test_purchase_ids[-1])
        
        # Print comprehensive summary
        print("\n" + "=" * 60)
        print(f"📊 Comprehensive Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        print(f"📈 Success Rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        # Categorize results
        failed_tests = [test for test in self.test_results if not test['success']]
        if failed_tests:
            print(f"\n❌ Failed Tests ({len(failed_tests)}):")
            for test in failed_tests:
                print(f"   • {test['test_name']}: {test['details']}")
        
        if self.tests_passed == self.tests_run:
            print("\n🎉 All tests passed! New functionality is working correctly.")
            return True
        else:
            print(f"\n⚠️  {self.tests_run - self.tests_passed} tests failed. Check details above.")
            return False

def main():
    tester = BarStockAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open('/app/test_reports/backend_api_results.json', 'w') as f:
        json.dump({
            'summary': {
                'total_tests': tester.tests_run,
                'passed_tests': tester.tests_passed,
                'success_rate': f"{(tester.tests_passed/tester.tests_run)*100:.1f}%" if tester.tests_run > 0 else "0%",
                'timestamp': datetime.now().isoformat()
            },
            'test_results': tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())