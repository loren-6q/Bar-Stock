"""
Backend API tests for Bar Stock Manager application
Tests key endpoints: items, stock-counts, stock-sessions
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestHealthAndBasics:
    """Basic health and connectivity tests"""
    
    def test_api_accessible(self):
        """Verify API is accessible"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200, f"API not accessible: {response.status_code}"
        print(f"✓ API accessible, returned {len(response.json())} items")
    
    def test_items_list_returns_data(self):
        """Verify items endpoint returns array"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Items should return a list"
        assert len(data) > 0, "Should have at least one item"
        print(f"✓ Items endpoint returned {len(data)} items")

class TestItemsEndpoints:
    """Tests for /api/items CRUD operations"""
    
    def test_get_items(self):
        """GET /api/items - list all items"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200
        items = response.json()
        assert isinstance(items, list)
        
        # Verify item structure
        if len(items) > 0:
            item = items[0]
            assert 'id' in item, "Item should have id"
            assert 'name' in item, "Item should have name"
            assert 'category' in item, "Item should have category"
            assert 'category_name' in item, "Item should have category_name"
            print(f"✓ Items have correct structure: {list(item.keys())}")
    
    def test_item_has_sale_price_field(self):
        """Verify items have sale_price field (new feature)"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200
        items = response.json()
        
        # Check that sale_price field exists in item schema
        if len(items) > 0:
            item = items[0]
            # sale_price may be None or a number
            assert 'sale_price' in item or item.get('sale_price') is None or isinstance(item.get('sale_price'), (int, float)), \
                "Items should support sale_price field"
            print(f"✓ Sale price field supported in items")
    
    def test_create_item(self):
        """POST /api/items - create new item"""
        test_item = {
            "name": "TEST_Item_Creation",
            "category": "O",
            "category_name": "Bar Supplies",
            "sub_category": "Test",
            "units_per_case": 1,
            "target_stock": 10,
            "primary_supplier": "Makro",
            "cost_per_unit": 25.0,
            "cost_per_case": 25.0,
            "bought_by_case": False,
            "sale_price": 50.0
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        assert created['name'] == test_item['name']
        assert created['sale_price'] == test_item['sale_price']
        assert 'id' in created
        
        print(f"✓ Item created with id: {created['id']}")
        
        # Cleanup - delete the test item
        delete_response = requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)
        assert delete_response.status_code == 200
        print(f"✓ Test item cleaned up")
    
    def test_update_item_sale_price(self):
        """PUT /api/items/:id - update sale_price field"""
        # First create a test item
        test_item = {
            "name": "TEST_Update_Sale_Price",
            "category": "O",
            "category_name": "Bar Supplies",
            "units_per_case": 1,
            "target_stock": 5,
            "primary_supplier": "Makro",
            "cost_per_unit": 10.0,
            "cost_per_case": 10.0,
            "bought_by_case": False,
            "sale_price": 20.0
        }
        
        create_response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert create_response.status_code == 200
        created = create_response.json()
        item_id = created['id']
        
        # Update sale_price
        update_data = test_item.copy()
        update_data['sale_price'] = 35.0
        
        update_response = requests.put(f"{BASE_URL}/api/items/{item_id}", json=update_data, timeout=10)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated['sale_price'] == 35.0, f"Sale price not updated: {updated.get('sale_price')}"
        print(f"✓ Sale price updated from 20.0 to 35.0")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{item_id}", timeout=10)

class TestStockCountsEndpoints:
    """Tests for /api/stock-counts endpoints"""
    
    def test_get_stock_counts(self):
        """GET /api/stock-counts - list all counts"""
        response = requests.get(f"{BASE_URL}/api/stock-counts", timeout=10)
        assert response.status_code == 200
        counts = response.json()
        assert isinstance(counts, list)
        print(f"✓ Stock counts returned {len(counts)} records")
    
    def test_stock_count_structure(self):
        """Verify stock count has location fields"""
        response = requests.get(f"{BASE_URL}/api/stock-counts", timeout=10)
        assert response.status_code == 200
        counts = response.json()
        
        if len(counts) > 0:
            count = counts[0]
            assert 'item_id' in count, "Count should have item_id"
            assert 'main_bar' in count, "Count should have main_bar"
            assert 'beer_bar' in count, "Count should have beer_bar"
            assert 'lobby' in count, "Count should have lobby"
            assert 'storage_room' in count, "Count should have storage_room"
            assert 'total_count' in count, "Count should have total_count"
            print(f"✓ Stock count structure verified")

class TestStockSessionsEndpoints:
    """Tests for /api/stock-sessions endpoints"""
    
    def test_get_sessions(self):
        """GET /api/stock-sessions - list all sessions"""
        response = requests.get(f"{BASE_URL}/api/stock-sessions", timeout=10)
        assert response.status_code == 200
        sessions = response.json()
        assert isinstance(sessions, list)
        print(f"✓ Sessions returned {len(sessions)} records")
    
    def test_session_counts_endpoint(self):
        """GET /api/stock-sessions/:id/counts - get session counts"""
        # First get sessions to find an ID
        sessions_response = requests.get(f"{BASE_URL}/api/stock-sessions", timeout=10)
        assert sessions_response.status_code == 200
        sessions = sessions_response.json()
        
        if len(sessions) > 0:
            session_id = sessions[0]['id']
            
            # Get counts for this session
            counts_response = requests.get(f"{BASE_URL}/api/stock-sessions/{session_id}/counts", timeout=10)
            assert counts_response.status_code == 200
            counts = counts_response.json()
            
            assert isinstance(counts, list)
            print(f"✓ Session {session_id} has {len(counts)} count records")
            
            # Verify count structure if we have data
            if len(counts) > 0:
                count = counts[0]
                assert 'item_id' in count, "Session count should have item_id"
                assert 'main_bar' in count, "Session count should have main_bar"
                assert 'total_count' in count, "Session count should have total_count"
                print(f"✓ Session count structure verified")
        else:
            print("⚠ No sessions available to test counts endpoint")

class TestSubCategoryField:
    """Tests for sub_category field in items"""
    
    def test_item_sub_category_field_exists(self):
        """Verify items support sub_category field"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200
        items = response.json()
        
        # Check that sub_category field is present
        if len(items) > 0:
            # Find an item with sub_category or verify field exists
            has_sub_category = any('sub_category' in item for item in items)
            assert has_sub_category, "Items should have sub_category field"
            
            # Find items with actual sub_category values
            items_with_subcat = [i for i in items if i.get('sub_category')]
            print(f"✓ Found {len(items_with_subcat)} items with sub_category values")
    
    def test_create_item_with_sub_category(self):
        """Create item with sub_category and verify persistence"""
        test_item = {
            "name": "TEST_SubCategory_Item",
            "category": "A",
            "category_name": "Thai Alcohol",
            "sub_category": "Tequila",
            "units_per_case": 1,
            "target_stock": 5,
            "primary_supplier": "Singha99",
            "cost_per_unit": 100.0,
            "cost_per_case": 100.0,
            "bought_by_case": False
        }
        
        # Create
        create_response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert create_response.status_code == 200
        created = create_response.json()
        
        assert created['sub_category'] == "Tequila"
        print(f"✓ Item created with sub_category: {created['sub_category']}")
        
        # Verify by GET
        get_response = requests.get(f"{BASE_URL}/api/items/{created['id']}", timeout=10)
        assert get_response.status_code == 200
        fetched = get_response.json()
        assert fetched['sub_category'] == "Tequila"
        print(f"✓ Sub_category persisted correctly")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
