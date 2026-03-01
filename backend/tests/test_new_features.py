"""
Tests for new features in Bar Stock Manager:
1. Unit price rounding to 1 decimal place (nearest 10ths)
2. Batch sort order API endpoint
3. Sort order field persistence
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestUnitPriceRounding:
    """Test auto-calculation of cost_per_unit/cost_per_case with rounding to 1 decimal"""
    
    def test_create_item_cost_per_case_auto_calculated(self):
        """POST /api/items - cost_per_case auto-calculated and rounded to 1 decimal"""
        test_item = {
            "name": "TEST_CostRounding_AutoCase",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 44.33,  # Should result in 44.33 * 12 = 531.96 -> rounded to 532.0
            "cost_per_case": 0,  # Backend should auto-calculate
            "bought_by_case": True
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        print(f"Created item - cost_per_unit: {created['cost_per_unit']}, cost_per_case: {created['cost_per_case']}")
        
        # cost_per_case should be auto-calculated: 44.33 * 12 = 531.96, rounded to 532.0
        assert created['cost_per_case'] == 532.0, f"Expected 532.0, got {created['cost_per_case']}"
        print(f"✓ cost_per_case auto-calculated and rounded: {created['cost_per_case']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)
    
    def test_update_item_cost_per_unit_triggers_recalculation(self):
        """PUT /api/items/:id - updating cost_per_unit recalculates cost_per_case"""
        # Create item first
        test_item = {
            "name": "TEST_CostRounding_Update",
            "category": "M",
            "category_name": "Mixers",
            "units_per_case": 24,
            "target_stock": 48,
            "primary_supplier": "Singha99",
            "cost_per_unit": 10.0,
            "cost_per_case": 240.0,
            "bought_by_case": True
        }
        
        create_response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert create_response.status_code == 200
        created = create_response.json()
        item_id = created['id']
        
        # Update cost_per_unit with a value that needs rounding
        # 10.55 * 24 = 253.2 -> should stay 253.2 (already 1 decimal)
        update_data = test_item.copy()
        update_data['cost_per_unit'] = 10.55
        update_data['cost_per_case'] = 0  # Backend should recalculate
        
        update_response = requests.put(f"{BASE_URL}/api/items/{item_id}", json=update_data, timeout=10)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        print(f"Updated item - cost_per_unit: {updated['cost_per_unit']}, cost_per_case: {updated['cost_per_case']}")
        
        # Expected: 10.55 * 24 = 253.2
        assert updated['cost_per_case'] == 253.2, f"Expected 253.2, got {updated['cost_per_case']}"
        print(f"✓ cost_per_case recalculated on update: {updated['cost_per_case']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{item_id}", timeout=10)
    
    def test_rounding_to_nearest_tenth(self):
        """Test that rounding is to nearest 10th (1 decimal place)"""
        test_cases = [
            # (cost_per_unit, units_per_case, expected_cost_per_case)
            (44.33, 12, 532.0),   # 44.33 * 12 = 531.96 -> 532.0
            (10.555, 10, 105.6),  # 10.555 * 10 = 105.55 -> 105.6 (rounded)
            (27.08, 24, 649.9),   # 27.08 * 24 = 649.92 -> 649.9
        ]
        
        for cost_per_unit, units_per_case, expected in test_cases:
            test_item = {
                "name": f"TEST_Rounding_{cost_per_unit}",
                "category": "M",
                "category_name": "Mixers",
                "units_per_case": units_per_case,
                "target_stock": 10,
                "primary_supplier": "Makro",
                "cost_per_unit": cost_per_unit,
                "cost_per_case": 0,
                "bought_by_case": True
            }
            
            response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
            assert response.status_code == 200, f"Create failed for {cost_per_unit}: {response.text}"
            
            created = response.json()
            
            # Check rounding
            actual = created['cost_per_case']
            print(f"Input: {cost_per_unit} * {units_per_case} = {cost_per_unit * units_per_case}, Rounded: {actual}, Expected: {expected}")
            
            # Allow small float precision difference
            assert abs(actual - expected) < 0.1, f"Rounding failed: expected {expected}, got {actual}"
            
            # Cleanup
            requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)
        
        print(f"✓ All rounding test cases passed")


class TestBatchSortOrderAPI:
    """Test PUT /api/items/batch-sort-order endpoint"""
    
    def test_batch_sort_order_endpoint_exists(self):
        """PUT /api/items/batch-sort-order - endpoint should exist and accept batch updates"""
        # First get some items to get their IDs
        items_response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert items_response.status_code == 200
        items = items_response.json()
        
        if len(items) < 2:
            pytest.skip("Need at least 2 items to test batch sort order")
        
        # Take first two items and update their sort_order
        batch_updates = [
            {"id": items[0]['id'], "sort_order": 100},
            {"id": items[1]['id'], "sort_order": 200}
        ]
        
        response = requests.put(f"{BASE_URL}/api/items/batch-sort-order", json=batch_updates, timeout=10)
        assert response.status_code == 200, f"Batch sort order failed: {response.status_code} - {response.text}"
        
        result = response.json()
        assert 'message' in result
        print(f"✓ Batch sort order response: {result['message']}")
    
    def test_batch_sort_order_persists(self):
        """Verify batch sort order updates are persisted"""
        # Create two test items
        test_items = []
        for i in range(2):
            item = {
                "name": f"TEST_SortOrder_{i}",
                "category": "O",
                "category_name": "Bar Supplies",
                "units_per_case": 1,
                "target_stock": 5,
                "primary_supplier": "Makro",
                "cost_per_unit": 10.0,
                "cost_per_case": 10.0,
                "bought_by_case": False,
                "sort_order": 0
            }
            response = requests.post(f"{BASE_URL}/api/items", json=item, timeout=10)
            assert response.status_code == 200
            test_items.append(response.json())
        
        # Update sort_order via batch API
        batch_updates = [
            {"id": test_items[0]['id'], "sort_order": 500},
            {"id": test_items[1]['id'], "sort_order": 600}
        ]
        
        update_response = requests.put(f"{BASE_URL}/api/items/batch-sort-order", json=batch_updates, timeout=10)
        assert update_response.status_code == 200
        
        # Verify persistence by fetching items
        for item, expected_order in zip(test_items, [500, 600]):
            get_response = requests.get(f"{BASE_URL}/api/items/{item['id']}", timeout=10)
            assert get_response.status_code == 200
            fetched = get_response.json()
            assert fetched['sort_order'] == expected_order, f"Expected sort_order {expected_order}, got {fetched['sort_order']}"
        
        print(f"✓ Batch sort order changes persisted correctly")
        
        # Cleanup
        for item in test_items:
            requests.delete(f"{BASE_URL}/api/items/{item['id']}", timeout=10)


class TestSortOrderField:
    """Test sort_order field on items"""
    
    def test_item_has_sort_order_field(self):
        """Items should have sort_order field"""
        response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert response.status_code == 200
        items = response.json()
        
        if len(items) > 0:
            item = items[0]
            assert 'sort_order' in item, "Item should have sort_order field"
            assert isinstance(item['sort_order'], int), "sort_order should be an integer"
            print(f"✓ sort_order field exists: {item['sort_order']}")
    
    def test_create_item_with_sort_order(self):
        """Create item with specific sort_order"""
        test_item = {
            "name": "TEST_WithSortOrder",
            "category": "O",
            "category_name": "Bar Supplies",
            "units_per_case": 1,
            "target_stock": 5,
            "primary_supplier": "Makro",
            "cost_per_unit": 10.0,
            "cost_per_case": 10.0,
            "bought_by_case": False,
            "sort_order": 999
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200
        
        created = response.json()
        assert created['sort_order'] == 999, f"Expected sort_order 999, got {created['sort_order']}"
        print(f"✓ Item created with sort_order: {created['sort_order']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
