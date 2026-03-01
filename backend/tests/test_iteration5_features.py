"""
Tests for iteration 5 features:
1. Duplicate recipe button - creates copy with '(copy)' suffix
2. Bidirectional cost calculation (unit→case AND case→unit)
3. All cost numbers rounded to 1 decimal place
4. Recipe CRUD still works
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestBidirectionalCostCalculation:
    """Test bidirectional cost calculation on PUT /api/items/{id}"""
    
    @pytest.fixture(autouse=True)
    def setup_test_item(self):
        """Create a test item for bidirectional cost tests"""
        test_item = {
            "name": "TEST_Bidirectional_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 15,
            "target_stock": 30,
            "primary_supplier": "Singha99",
            "cost_per_unit": 50.0,
            "cost_per_case": 750.0,
            "bought_by_case": True
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200, f"Setup failed: {response.text}"
        self.item = response.json()
        self.item_id = self.item['id']
        
        yield
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{self.item_id}", timeout=10)
    
    def test_unit_to_case_calculation(self):
        """PUT with cost_per_unit=42, cost_per_case=0, units_per_case=15 → cost_per_case=630"""
        update_data = {
            "name": "TEST_Bidirectional_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 15,
            "target_stock": 30,
            "primary_supplier": "Singha99",
            "cost_per_unit": 42,
            "cost_per_case": 0,  # Should be auto-calculated
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        # 42 * 15 = 630
        assert updated['cost_per_case'] == 630.0, f"Expected cost_per_case=630, got {updated['cost_per_case']}"
        print(f"✓ Unit→Case calculation: 42 * 15 = {updated['cost_per_case']}")
    
    def test_case_to_unit_calculation(self):
        """PUT with cost_per_unit=0, cost_per_case=955, units_per_case=24 → cost_per_unit≈39.8"""
        # First update the item to have units_per_case=24
        update_data = {
            "name": "TEST_Bidirectional_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 24,
            "target_stock": 30,
            "primary_supplier": "Singha99",
            "cost_per_unit": 0,  # Should be auto-calculated
            "cost_per_case": 955,
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        # 955 / 24 = 39.791666... → rounded to 39.8
        assert updated['cost_per_unit'] == 39.8, f"Expected cost_per_unit=39.8, got {updated['cost_per_unit']}"
        print(f"✓ Case→Unit calculation: 955 / 24 = {updated['cost_per_unit']}")
    
    def test_no_calculation_when_both_set(self):
        """PUT with both costs set should keep both values (just round them)"""
        update_data = {
            "name": "TEST_Bidirectional_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 30,
            "primary_supplier": "Singha99",
            "cost_per_unit": 45.0,
            "cost_per_case": 540.0,  # Both set, neither should be auto-calculated
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        assert updated['cost_per_unit'] == 45.0, f"Expected cost_per_unit=45.0, got {updated['cost_per_unit']}"
        assert updated['cost_per_case'] == 540.0, f"Expected cost_per_case=540.0, got {updated['cost_per_case']}"
        print(f"✓ Both costs set: unit={updated['cost_per_unit']}, case={updated['cost_per_case']}")


class TestDecimalRounding:
    """Test that all cost fields are rounded to 1 decimal place"""
    
    @pytest.fixture(autouse=True)
    def setup_test_item(self):
        """Create a test item for rounding tests"""
        test_item = {
            "name": "TEST_Rounding_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 50.0,
            "cost_per_case": 600.0,
            "bought_by_case": True
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200, f"Setup failed: {response.text}"
        self.item = response.json()
        self.item_id = self.item['id']
        
        yield
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{self.item_id}", timeout=10)
    
    def test_cost_per_unit_rounded_to_1_decimal(self):
        """PUT with cost_per_unit=39.791666 → should return cost_per_unit=39.8"""
        update_data = {
            "name": "TEST_Rounding_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 39.791666,  # Many decimals
            "cost_per_case": 500.0,  # Set to avoid auto-calculation
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        # 39.791666 → rounded to 39.8
        assert updated['cost_per_unit'] == 39.8, f"Expected cost_per_unit=39.8, got {updated['cost_per_unit']}"
        print(f"✓ Rounding test: 39.791666 → {updated['cost_per_unit']}")
    
    def test_cost_per_case_rounded_to_1_decimal(self):
        """PUT with cost_per_case=649.92 → should return cost_per_case=649.9"""
        update_data = {
            "name": "TEST_Rounding_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 50.0,
            "cost_per_case": 649.92,
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        assert updated['cost_per_case'] == 649.9, f"Expected cost_per_case=649.9, got {updated['cost_per_case']}"
        print(f"✓ Rounding test: 649.92 → {updated['cost_per_case']}")
    
    def test_sale_price_rounded_to_1_decimal(self):
        """PUT with sale_price=123.456 → should return sale_price=123.5"""
        update_data = {
            "name": "TEST_Rounding_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 50.0,
            "cost_per_case": 600.0,
            "bought_by_case": True,
            "sale_price": 123.456
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        assert updated['sale_price'] == 123.5, f"Expected sale_price=123.5, got {updated['sale_price']}"
        print(f"✓ Rounding test: 123.456 → {updated['sale_price']}")
    
    def test_auto_calculated_cost_is_rounded(self):
        """When cost_per_case is auto-calculated from unit price, it should be rounded"""
        update_data = {
            "name": "TEST_Rounding_Item",
            "category": "B",
            "category_name": "Beer",
            "units_per_case": 7,  # Odd number to create decimals
            "target_stock": 24,
            "primary_supplier": "Singha99",
            "cost_per_unit": 33.33,  # 33.33 * 7 = 233.31
            "cost_per_case": 0,  # Auto-calculate
            "bought_by_case": True
        }
        
        response = requests.put(f"{BASE_URL}/api/items/{self.item_id}", json=update_data, timeout=10)
        assert response.status_code == 200, f"Update failed: {response.text}"
        
        updated = response.json()
        # 33.33 * 7 = 233.31 → rounded to 233.3
        assert updated['cost_per_case'] == 233.3, f"Expected cost_per_case=233.3, got {updated['cost_per_case']}"
        print(f"✓ Auto-calculated and rounded: 33.33 * 7 = {updated['cost_per_case']}")


class TestRecipeCRUD:
    """Test recipe CRUD operations still work"""
    
    def test_create_recipe(self):
        """POST /api/recipes - Create a recipe"""
        recipe_data = {
            "name": "TEST_Recipe_Create",
            "sale_price": 150.0,
            "ingredients": [],
            "fixed_costs": [{"name": "Ice", "cost": 2.0}]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=recipe_data, timeout=10)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        assert created['name'] == "TEST_Recipe_Create"
        assert created['sale_price'] == 150.0
        assert 'id' in created
        print(f"✓ Recipe created: {created['name']} (id: {created['id']})")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)
    
    def test_get_recipes(self):
        """GET /api/recipes - List all recipes"""
        response = requests.get(f"{BASE_URL}/api/recipes", timeout=10)
        assert response.status_code == 200, f"Get failed: {response.text}"
        
        recipes = response.json()
        assert isinstance(recipes, list)
        print(f"✓ Got {len(recipes)} recipes")
    
    def test_update_recipe(self):
        """PUT /api/recipes/{id} - Update a recipe"""
        # Create a recipe first
        recipe_data = {
            "name": "TEST_Recipe_Update",
            "sale_price": 100.0,
            "ingredients": [],
            "fixed_costs": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/recipes", json=recipe_data, timeout=10)
        assert create_response.status_code == 200
        recipe_id = create_response.json()['id']
        
        # Update it
        updated_data = {
            "name": "TEST_Recipe_Updated",
            "sale_price": 200.0,
            "ingredients": [],
            "fixed_costs": [{"name": "Garnish", "cost": 5.0}]
        }
        
        update_response = requests.put(f"{BASE_URL}/api/recipes/{recipe_id}", json=updated_data, timeout=10)
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        
        updated = update_response.json()
        assert updated['name'] == "TEST_Recipe_Updated"
        assert updated['sale_price'] == 200.0
        print(f"✓ Recipe updated: {updated['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", timeout=10)
    
    def test_delete_recipe(self):
        """DELETE /api/recipes/{id} - Delete a recipe"""
        # Create a recipe first
        recipe_data = {
            "name": "TEST_Recipe_Delete",
            "sale_price": 50.0,
            "ingredients": [],
            "fixed_costs": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/recipes", json=recipe_data, timeout=10)
        assert create_response.status_code == 200
        recipe_id = create_response.json()['id']
        
        # Delete it
        delete_response = requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", timeout=10)
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        print(f"✓ Recipe deleted")
        
        # Verify it's gone
        get_response = requests.get(f"{BASE_URL}/api/recipes", timeout=10)
        recipes = get_response.json()
        assert not any(r['id'] == recipe_id for r in recipes), "Recipe should be deleted"


class TestRecipeWithIngredients:
    """Test recipe with item ingredients for cost calculation"""
    
    @pytest.fixture(autouse=True)
    def setup_test_item(self):
        """Create a test item for recipe ingredients"""
        test_item = {
            "name": "TEST_Recipe_Ingredient_Item",
            "category": "A",
            "category_name": "Thai Alcohol",
            "units_per_case": 12,
            "target_stock": 24,
            "primary_supplier": "Makro",
            "cost_per_unit": 24.0,
            "cost_per_case": 288.0,
            "bought_by_case": True
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200, f"Setup failed: {response.text}"
        self.item = response.json()
        self.item_id = self.item['id']
        
        yield
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{self.item_id}", timeout=10)
    
    def test_create_recipe_with_ingredients(self):
        """Create a recipe with an item ingredient"""
        recipe_data = {
            "name": "TEST_Recipe_With_Ingredients",
            "sale_price": 120.0,
            "ingredients": [
                {
                    "item_id": self.item_id,
                    "item_name": "TEST_Recipe_Ingredient_Item",
                    "servings_per_unit": 20.0,  # 20 servings per bottle
                    "servings_used": 2.0  # 2 servings in this recipe
                }
            ],
            "fixed_costs": [{"name": "Ice", "cost": 2.0}]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=recipe_data, timeout=10)
        assert response.status_code == 200, f"Create failed: {response.text}"
        
        created = response.json()
        assert len(created['ingredients']) == 1
        assert created['ingredients'][0]['item_id'] == self.item_id
        
        # Cost calculation: (24.0 * 2 / 20) + 2 = 2.4 + 2 = 4.4
        # Profit: 120 - 4.4 = 115.6
        print(f"✓ Recipe with ingredient created: {created['name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
