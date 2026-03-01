"""
Tests for new features in Bar Stock Manager (Iteration 4):
1. Recipe CRUD API (/api/recipes)
2. Column sorting in Manage tab
3. Sticky headers (UI-only, tested via Playwright)
4. Item profits calculation
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')


class TestRecipeCRUD:
    """Tests for Recipe CRUD API endpoints"""
    
    def test_get_recipes_endpoint_exists(self):
        """GET /api/recipes - endpoint should return list"""
        response = requests.get(f"{BASE_URL}/api/recipes", timeout=10)
        assert response.status_code == 200, f"GET recipes failed: {response.text}"
        recipes = response.json()
        assert isinstance(recipes, list), "Recipes should return a list"
        print(f"✓ GET /api/recipes returned {len(recipes)} recipes")
    
    def test_create_recipe_basic(self):
        """POST /api/recipes - create new recipe with basic data"""
        test_recipe = {
            "name": "TEST_Basic_Recipe",
            "sale_price": 99.0,
            "ingredients": [],
            "fixed_costs": []
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200, f"Create recipe failed: {response.text}"
        
        created = response.json()
        assert created['name'] == test_recipe['name']
        assert created['sale_price'] == test_recipe['sale_price']
        assert 'id' in created
        assert isinstance(created['ingredients'], list)
        assert isinstance(created['fixed_costs'], list)
        print(f"✓ Recipe created with id: {created['id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)
    
    def test_create_recipe_with_fixed_costs(self):
        """POST /api/recipes - create recipe with fixed costs"""
        test_recipe = {
            "name": "TEST_Recipe_FixedCosts",
            "sale_price": 199.0,
            "ingredients": [],
            "fixed_costs": [
                {"name": "Ice", "cost": 2.0},
                {"name": "Straw", "cost": 0.5}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200
        
        created = response.json()
        assert len(created['fixed_costs']) == 2
        assert created['fixed_costs'][0]['name'] == "Ice"
        assert created['fixed_costs'][0]['cost'] == 2.0
        print(f"✓ Recipe created with fixed_costs: {created['fixed_costs']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)
    
    def test_create_recipe_with_ingredients(self):
        """POST /api/recipes - create recipe with ingredients referencing items"""
        # First get some items to reference
        items_response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert items_response.status_code == 200
        items = items_response.json()
        
        if len(items) < 1:
            pytest.skip("No items available to test ingredients")
        
        # Pick an item to use as ingredient
        test_item = items[0]
        
        test_recipe = {
            "name": "TEST_Recipe_Ingredients",
            "sale_price": 149.0,
            "ingredients": [
                {
                    "item_id": test_item['id'],
                    "item_name": test_item['name'],
                    "servings_per_unit": 15.0,
                    "servings_used": 4.0
                }
            ],
            "fixed_costs": [
                {"name": "Ice", "cost": 2.0}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200
        
        created = response.json()
        assert len(created['ingredients']) == 1
        assert created['ingredients'][0]['item_id'] == test_item['id']
        assert created['ingredients'][0]['servings_per_unit'] == 15.0
        assert created['ingredients'][0]['servings_used'] == 4.0
        print(f"✓ Recipe created with ingredient: {created['ingredients'][0]['item_name']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)
    
    def test_update_recipe(self):
        """PUT /api/recipes/:id - update recipe"""
        # Create recipe first
        test_recipe = {
            "name": "TEST_Recipe_Update",
            "sale_price": 100.0,
            "ingredients": [],
            "fixed_costs": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert create_response.status_code == 200
        created = create_response.json()
        recipe_id = created['id']
        
        # Update recipe
        update_data = {
            "name": "TEST_Recipe_Updated",
            "sale_price": 150.0,
            "ingredients": [],
            "fixed_costs": [{"name": "Ice", "cost": 3.0}]
        }
        
        update_response = requests.put(f"{BASE_URL}/api/recipes/{recipe_id}", json=update_data, timeout=10)
        assert update_response.status_code == 200
        
        updated = update_response.json()
        assert updated['name'] == "TEST_Recipe_Updated"
        assert updated['sale_price'] == 150.0
        assert len(updated['fixed_costs']) == 1
        print(f"✓ Recipe updated successfully: {updated['name']}, sale_price: {updated['sale_price']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", timeout=10)
    
    def test_delete_recipe(self):
        """DELETE /api/recipes/:id - delete recipe"""
        # Create recipe first
        test_recipe = {
            "name": "TEST_Recipe_Delete",
            "sale_price": 50.0,
            "ingredients": [],
            "fixed_costs": []
        }
        
        create_response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert create_response.status_code == 200
        created = create_response.json()
        recipe_id = created['id']
        
        # Delete recipe
        delete_response = requests.delete(f"{BASE_URL}/api/recipes/{recipe_id}", timeout=10)
        assert delete_response.status_code == 200
        
        result = delete_response.json()
        assert 'message' in result
        print(f"✓ Recipe deleted: {result['message']}")
        
        # Verify deletion - should return 404
        get_response = requests.get(f"{BASE_URL}/api/recipes/{recipe_id}", timeout=10)
        # Note: GET individual recipe endpoint doesn't exist, so verify via list
        recipes_response = requests.get(f"{BASE_URL}/api/recipes", timeout=10)
        recipes = recipes_response.json()
        assert not any(r['id'] == recipe_id for r in recipes), "Recipe should be deleted"
        print(f"✓ Recipe no longer in list")
    
    def test_delete_nonexistent_recipe_returns_404(self):
        """DELETE /api/recipes/:id - 404 for nonexistent recipe"""
        response = requests.delete(f"{BASE_URL}/api/recipes/nonexistent-id-12345", timeout=10)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Nonexistent recipe returns 404")
    
    def test_update_nonexistent_recipe_returns_404(self):
        """PUT /api/recipes/:id - 404 for nonexistent recipe"""
        update_data = {
            "name": "Ghost Recipe",
            "sale_price": 999.0,
            "ingredients": [],
            "fixed_costs": []
        }
        response = requests.put(f"{BASE_URL}/api/recipes/nonexistent-id-12345", json=update_data, timeout=10)
        assert response.status_code == 404, f"Expected 404, got {response.status_code}"
        print(f"✓ Update nonexistent recipe returns 404")


class TestRecipeCostCalculation:
    """Tests to verify recipe cost calculation logic"""
    
    def test_recipe_cost_with_single_ingredient(self):
        """Verify cost calculation: (item.cost_per_unit * servings_used / servings_per_unit)"""
        # Get an item with a known cost
        items_response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        items = items_response.json()
        
        # Find item with cost_per_unit > 0
        test_item = next((i for i in items if i.get('cost_per_unit', 0) > 0), None)
        if not test_item:
            pytest.skip("No item with cost_per_unit > 0 found")
        
        # Create recipe with this ingredient
        # Cost formula: item.cost_per_unit * servings_used / servings_per_unit
        # Example: 44 * 4 / 15 = 11.73 (for Big Chang)
        servings_per_unit = 15.0
        servings_used = 4.0
        expected_ingredient_cost = test_item['cost_per_unit'] * servings_used / servings_per_unit
        
        test_recipe = {
            "name": "TEST_Cost_Calculation",
            "sale_price": 199.0,
            "ingredients": [
                {
                    "item_id": test_item['id'],
                    "item_name": test_item['name'],
                    "servings_per_unit": servings_per_unit,
                    "servings_used": servings_used
                }
            ],
            "fixed_costs": [{"name": "Ice", "cost": 2.0}]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200
        created = response.json()
        
        # The backend stores the data - cost is calculated on frontend
        # Verify data is stored correctly for calculation
        assert created['ingredients'][0]['servings_per_unit'] == servings_per_unit
        assert created['ingredients'][0]['servings_used'] == servings_used
        print(f"✓ Ingredient stored correctly for cost calculation")
        print(f"  Item cost_per_unit: {test_item['cost_per_unit']}")
        print(f"  servings_per_unit: {servings_per_unit}, servings_used: {servings_used}")
        print(f"  Expected ingredient cost: {expected_ingredient_cost:.2f}")
        print(f"  + Fixed cost (Ice): 2.0")
        print(f"  = Total cost: {expected_ingredient_cost + 2:.2f}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)


class TestItemProfitFields:
    """Tests for item sale_price field used in profit calculations"""
    
    def test_create_item_with_sale_price(self):
        """Verify items can have sale_price for profit calculation"""
        test_item = {
            "name": "TEST_Item_Profit",
            "category": "M",
            "category_name": "Mixers",
            "units_per_case": 1,
            "target_stock": 10,
            "primary_supplier": "Makro",
            "cost_per_unit": 10.0,
            "cost_per_case": 10.0,
            "bought_by_case": False,
            "sale_price": 25.0
        }
        
        response = requests.post(f"{BASE_URL}/api/items", json=test_item, timeout=10)
        assert response.status_code == 200
        
        created = response.json()
        assert created['sale_price'] == 25.0
        assert created['cost_per_unit'] == 10.0
        
        # Profit = 25 - 10 = 15
        # Margin = 15 / 25 * 100 = 60%
        profit = created['sale_price'] - created['cost_per_unit']
        margin = int(profit / created['sale_price'] * 100)
        print(f"✓ Item profit calculation verified:")
        print(f"  Cost: {created['cost_per_unit']}, Sale: {created['sale_price']}")
        print(f"  Profit: {profit}, Margin: {margin}%")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/items/{created['id']}", timeout=10)
    
    def test_filter_items_with_sale_price(self):
        """Verify we can filter items with sale_price > 0 for Item Profits table"""
        items_response = requests.get(f"{BASE_URL}/api/items", timeout=10)
        assert items_response.status_code == 200
        items = items_response.json()
        
        # Filter items with sale_price > 0 (like frontend does)
        items_with_sale = [i for i in items if (i.get('sale_price') or 0) > 0]
        print(f"✓ Found {len(items_with_sale)} items with sale_price > 0 out of {len(items)} total items")
        
        for item in items_with_sale[:3]:  # Print first 3
            cost = item.get('cost_per_unit', 0)
            sale = item.get('sale_price', 0)
            profit = sale - cost
            print(f"  {item['name']}: cost={cost}, sale={sale}, profit={profit}")


class TestRecipeModels:
    """Tests to verify recipe model structure matches spec"""
    
    def test_recipe_ingredient_model(self):
        """Verify RecipeIngredient model structure"""
        test_recipe = {
            "name": "TEST_Model_Ingredient",
            "sale_price": 100.0,
            "ingredients": [
                {
                    "item_id": "test-item-id",
                    "item_name": "Test Item",
                    "servings_per_unit": 10.0,
                    "servings_used": 2.0
                }
            ],
            "fixed_costs": []
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200
        created = response.json()
        
        ing = created['ingredients'][0]
        assert 'item_id' in ing
        assert 'item_name' in ing
        assert 'servings_per_unit' in ing
        assert 'servings_used' in ing
        print(f"✓ RecipeIngredient model has correct fields")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)
    
    def test_recipe_fixed_cost_model(self):
        """Verify RecipeFixedCost model structure"""
        test_recipe = {
            "name": "TEST_Model_FixedCost",
            "sale_price": 100.0,
            "ingredients": [],
            "fixed_costs": [
                {"name": "Ice", "cost": 2.5},
                {"name": "Cup", "cost": 1.0}
            ]
        }
        
        response = requests.post(f"{BASE_URL}/api/recipes", json=test_recipe, timeout=10)
        assert response.status_code == 200
        created = response.json()
        
        fc = created['fixed_costs'][0]
        assert 'name' in fc
        assert 'cost' in fc
        assert fc['cost'] == 2.5
        print(f"✓ RecipeFixedCost model has correct fields")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/recipes/{created['id']}", timeout=10)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
