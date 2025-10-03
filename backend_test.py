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
                    required_fields = ['item_name', 'current_stock', 'need_to_buy', 'estimated_cost']
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

    def run_all_tests(self):
        """Run comprehensive API tests"""
        print("🧪 Starting Bar Stock API Tests")
        print("=" * 50)
        
        # Initialize sample data first
        print("\n📋 Setting up test data...")
        init_success, _ = self.test_initialize_sample_data()
        
        if not init_success:
            print("❌ Failed to initialize sample data. Stopping tests.")
            return False
        
        # Test items endpoint
        print("\n📦 Testing Items API...")
        items_success, items = self.test_get_items()
        
        if not items_success or not items:
            print("❌ No items found. Cannot continue with stock tests.")
            return False
        
        # Use first item for stock count tests
        test_item_id = items[0]['id']
        print(f"\n📊 Testing Stock Counts with item: {items[0]['name']} (ID: {test_item_id})")
        
        # Test stock count creation
        create_success, _ = self.test_create_stock_count(test_item_id)
        
        # Test stock count update
        update_success, _ = self.test_update_stock_count(test_item_id)
        
        # Test getting all stock counts
        print("\n📋 Testing Stock Count Retrieval...")
        self.test_get_stock_counts()
        
        # Test shopping list
        print("\n🛒 Testing Shopping List Generation...")
        self.test_get_shopping_list()
        
        # Test quick restock
        print("\n⚡ Testing Quick Restock...")
        self.test_quick_restock()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return True
        else:
            print("⚠️  Some tests failed. Check details above.")
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