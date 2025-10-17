from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
import math
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Define Models
class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str  # A, B, M, O, Z
    category_name: str  # Thai Alcohol, Beer, Mixers, Other Bar, Hostel Supplies
    units_per_case: int = 1
    min_stock: int = 0
    max_stock: int = 0
    primary_supplier: str
    secondary_supplier: Optional[str] = None
    cost_per_unit: float = 0.0
    cost_per_case: float = 0.0
    is_case_pricing: bool = False
    bought_by_case: bool = False  # New field: whether this item is commonly bought by case

class ItemCreate(BaseModel):
    name: str
    category: str
    category_name: str
    units_per_case: int = 1
    min_stock: int = 0
    max_stock: int = 0
    primary_supplier: str
    secondary_supplier: Optional[str] = None
    cost_per_unit: float = 0.0
    cost_per_case: float = 0.0
    is_case_pricing: bool = False
    bought_by_case: bool = False  # New field: whether this item is commonly bought by case

class StockCount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    main_bar: int = 0
    beer_bar: int = 0
    lobby: int = 0
    storage_room: int = 0
    total_count: int = 0
    count_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    counted_by: str = "Staff"

class StockCountCreate(BaseModel):
    item_id: str
    main_bar: int = 0
    beer_bar: int = 0
    lobby: int = 0
    storage_room: int = 0
    counted_by: str = "Staff"

class StockCountUpdate(BaseModel):
    main_bar: Optional[int] = None
    beer_bar: Optional[int] = None
    lobby: Optional[int] = None
    storage_room: Optional[int] = None

# New models for case/single input support
class LocationStockInput(BaseModel):
    singles: int = 0  # Individual units (cans, bottles, etc.)
    cases: int = 0    # Full cases/boxes

class StockCountInputs(BaseModel):
    main_bar: LocationStockInput = Field(default_factory=LocationStockInput)
    beer_bar: LocationStockInput = Field(default_factory=LocationStockInput)
    lobby: LocationStockInput = Field(default_factory=LocationStockInput)
    storage_room: LocationStockInput = Field(default_factory=LocationStockInput)
    counted_by: str = "Staff"

class CaseCalculation(BaseModel):
    total_units: int
    cases_needed: int
    extra_units: int
    cases_to_buy: int
    display_text: str

class ShoppingListItem(BaseModel):
    item_name: str
    item_id: str
    current_stock: int
    min_stock: int
    max_stock: int
    need_to_buy_units: int
    case_calculation: CaseCalculation
    supplier: str
    cost_per_unit: float
    cost_per_case: float
    estimated_cost: float

class StockSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str
    session_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    session_type: str = "full_count"  # full_count or quick_restock
    notes: Optional[str] = None

class StockSessionCreate(BaseModel):
    session_name: str
    session_type: str = "full_count"
    notes: Optional[str] = None

# Enhanced models for order confirmation and purchase tracking
class ShoppingListOrder(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    supplier: str
    order_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    status: str = "pending"  # pending, ordered, received, confirmed
    planned_items: List[Dict[str, Any]]  # original shopping list items
    notes: Optional[str] = None

class ShoppingListOrderCreate(BaseModel):
    supplier: str
    planned_items: List[Dict[str, Any]]
    notes: Optional[str] = None

class PurchaseEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    order_id: Optional[str] = None  # link to shopping list order
    session_id: str
    item_id: str
    planned_quantity: int  # from shopping list
    actual_quantity: int  # what was actually bought
    cost_per_unit: float
    total_cost: float
    supplier: str
    purchase_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    delivery_received: bool = False  # track if delivery was received
    notes: Optional[str] = None

class PurchaseEntryCreate(BaseModel):
    order_id: Optional[str] = None
    session_id: str
    item_id: str
    planned_quantity: int
    actual_quantity: int
    cost_per_unit: float
    total_cost: float
    supplier: str
    delivery_received: bool = False
    notes: Optional[str] = None

class SessionComparison(BaseModel):
    session1_id: str
    session1_name: str
    session1_date: datetime
    session2_id: str
    session2_name: str
    session2_date: datetime
    item_comparisons: List[Dict[str, Any]]
    total_usage_cost: float
    period_days: int

class UsageReport(BaseModel):
    item_id: str
    item_name: str
    opening_stock: int
    purchases_made: int
    closing_stock: int
    calculated_usage: int
    cost_per_unit: float
    total_usage_cost: float
    supplier: str

# Helper function to calculate cases
def calculate_cases(units_needed: int, units_per_case: int) -> CaseCalculation:
    if units_per_case <= 1:
        return CaseCalculation(
            total_units=units_needed,
            cases_needed=0,
            extra_units=units_needed,
            cases_to_buy=0,
            display_text=f"{units_needed} units"
        )
    
    full_cases = units_needed // units_per_case
    extra_units = units_needed % units_per_case
    
    # Round up to full case if there are extra units
    cases_to_buy = full_cases + (1 if extra_units > 0 else 0)
    
    if extra_units == 0:
        display_text = f"{full_cases} cases ({full_cases * units_per_case} units)"
    else:
        display_text = f"{cases_to_buy} cases ({full_cases} full + {extra_units} extra = {cases_to_buy * units_per_case} units)"
    
    return CaseCalculation(
        total_units=units_needed,
        cases_needed=full_cases,
        extra_units=extra_units,
        cases_to_buy=cases_to_buy,
        display_text=display_text
    )

# Helper function to prepare data for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value
        return data
    return data

# Helper function to parse data from MongoDB  
def parse_from_mongo(item):
    if isinstance(item, dict) and '_id' in item:
        del item['_id']
    return item

# Items endpoints
@api_router.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    item_dict = item.dict()
    # Calculate cost per case if not provided
    if item_dict['cost_per_case'] == 0 and item_dict['cost_per_unit'] > 0:
        item_dict['cost_per_case'] = item_dict['cost_per_unit'] * item_dict['units_per_case']
    
    item_obj = Item(**item_dict)
    result = await db.items.insert_one(prepare_for_mongo(item_obj.dict()))
    return item_obj

@api_router.get("/items", response_model=List[Item])
async def get_items():
    items = await db.items.find().to_list(1000)
    return [Item(**parse_from_mongo(item)) for item in items]

@api_router.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: str):
    item = await db.items.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    return Item(**parse_from_mongo(item))

@api_router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_update: ItemCreate):
    update_dict = item_update.dict()
    # Recalculate cost per case
    if update_dict['cost_per_case'] == 0 and update_dict['cost_per_unit'] > 0:
        update_dict['cost_per_case'] = update_dict['cost_per_unit'] * update_dict['units_per_case']
    
    result = await db.items.update_one(
        {"id": item_id}, 
        {"$set": update_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = await db.items.find_one({"id": item_id})
    return Item(**parse_from_mongo(updated_item))

@api_router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    # Also delete associated stock counts
    await db.stock_counts.delete_many({"item_id": item_id})
    
    result = await db.items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    return {"message": "Item deleted successfully"}

# Stock counting endpoints
@api_router.post("/stock-counts", response_model=StockCount)
async def create_stock_count(count: StockCountCreate):
    count_dict = count.dict()
    # Calculate total
    total = count_dict['main_bar'] + count_dict['beer_bar'] + count_dict['lobby'] + count_dict['storage_room']
    count_dict['total_count'] = total
    
    count_obj = StockCount(**count_dict)
    
    # Check if count exists for this item, if so update it
    existing_count = await db.stock_counts.find_one({"item_id": count.item_id})
    if existing_count:
        result = await db.stock_counts.update_one(
            {"item_id": count.item_id},
            {"$set": prepare_for_mongo(count_obj.dict())}
        )
    else:
        result = await db.stock_counts.insert_one(prepare_for_mongo(count_obj.dict()))
    
    return count_obj

@api_router.get("/stock-counts", response_model=List[StockCount])
async def get_stock_counts():
    counts = await db.stock_counts.find().to_list(1000)
    return [StockCount(**parse_from_mongo(count)) for count in counts]

@api_router.get("/stock-counts/{item_id}", response_model=StockCount)
async def get_stock_count(item_id: str):
    count = await db.stock_counts.find_one({"item_id": item_id})
    if not count:
        # Return empty count for item
        return StockCount(item_id=item_id)
    return StockCount(**parse_from_mongo(count))

@api_router.put("/stock-counts/{item_id}", response_model=StockCount)
async def update_stock_count(item_id: str, count_update: StockCountUpdate):
    existing_count = await db.stock_counts.find_one({"item_id": item_id})
    
    if existing_count:
        # Update only provided fields
        update_data = existing_count.copy()
        for field, value in count_update.dict().items():
            if value is not None:
                update_data[field] = value
        
        # Recalculate total
        update_data['total_count'] = update_data['main_bar'] + update_data['beer_bar'] + update_data['lobby'] + update_data['storage_room']
        update_data['count_date'] = datetime.now(timezone.utc)
        
        result = await db.stock_counts.update_one(
            {"item_id": item_id},
            {"$set": prepare_for_mongo(update_data)}
        )
        return StockCount(**parse_from_mongo(update_data))
    else:
        # Create new count
        count_dict = {"item_id": item_id}
        for field, value in count_update.dict().items():
            if value is not None:
                count_dict[field] = value
            else:
                count_dict[field] = 0
                
        count_dict['total_count'] = count_dict['main_bar'] + count_dict['beer_bar'] + count_dict['lobby'] + count_dict['storage_room']
        
        count_obj = StockCount(**count_dict)
        await db.stock_counts.insert_one(prepare_for_mongo(count_obj.dict()))
        return count_obj

# New endpoint for case/single input method
@api_router.post("/stock-counts-enhanced/{item_id}", response_model=StockCount)
async def create_enhanced_stock_count(item_id: str, stock_inputs: StockCountInputs):
    # Get item to check units per case
    item = await db.items.find_one({"id": item_id})
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    
    units_per_case = item.get('units_per_case', 1)
    
    # Calculate total units for each location (cases * units_per_case + singles)
    main_bar_total = (stock_inputs.main_bar.cases * units_per_case) + stock_inputs.main_bar.singles
    beer_bar_total = (stock_inputs.beer_bar.cases * units_per_case) + stock_inputs.beer_bar.singles
    lobby_total = (stock_inputs.lobby.cases * units_per_case) + stock_inputs.lobby.singles
    storage_room_total = (stock_inputs.storage_room.cases * units_per_case) + stock_inputs.storage_room.singles
    
    total_count = main_bar_total + beer_bar_total + lobby_total + storage_room_total
    
    # Create or update stock count
    stock_count_data = {
        "item_id": item_id,
        "main_bar": main_bar_total,
        "beer_bar": beer_bar_total,
        "lobby": lobby_total,
        "storage_room": storage_room_total,
        "total_count": total_count,
        "counted_by": stock_inputs.counted_by,
        "count_date": datetime.now(timezone.utc)
    }
    
    # Try to update existing, or create new
    existing = await db.stock_counts.find_one({"item_id": item_id})
    if existing:
        await db.stock_counts.update_one({"item_id": item_id}, {"$set": stock_count_data})
    else:
        stock_count = StockCount(**stock_count_data)
        await db.stock_counts.insert_one(prepare_for_mongo(stock_count.dict()))
    
    updated_count = await db.stock_counts.find_one({"item_id": item_id})
    return StockCount(**parse_from_mongo(updated_count))

# Shopping list endpoint with case logic
@api_router.get("/shopping-list")
async def get_shopping_list():
    # Get all items
    items = await db.items.find().to_list(1000)
    # Get all stock counts
    counts = await db.stock_counts.find().to_list(1000)
    
    # Create a map of stock counts by item_id
    stock_map = {count['item_id']: count for count in counts}
    
    shopping_list = {}
    
    for item in items:
        item_obj = Item(**parse_from_mongo(item))
        current_stock = 0
        
        if item_obj.id in stock_map:
            current_stock = stock_map[item_obj.id]['total_count']
        
        # Calculate need to buy
        need_to_buy = max(0, item_obj.max_stock - current_stock)
        
        if need_to_buy > 0:
            supplier = item_obj.primary_supplier
            if supplier not in shopping_list:
                shopping_list[supplier] = []
            
            # Calculate case logic
            case_calc = calculate_cases(need_to_buy, item_obj.units_per_case)
            
            # Calculate cost (prefer case pricing if available and buying full cases)
            if item_obj.cost_per_case > 0 and case_calc.cases_to_buy > 0:
                estimated_cost = case_calc.cases_to_buy * item_obj.cost_per_case
            else:
                estimated_cost = need_to_buy * item_obj.cost_per_unit
            
            shopping_item = ShoppingListItem(
                item_name=item_obj.name,
                item_id=item_obj.id,
                current_stock=current_stock,
                min_stock=item_obj.min_stock,
                max_stock=item_obj.max_stock,
                need_to_buy_units=need_to_buy,
                case_calculation=case_calc,
                supplier=supplier,
                cost_per_unit=item_obj.cost_per_unit,
                cost_per_case=item_obj.cost_per_case,
                estimated_cost=estimated_cost
            )
            
            shopping_list[supplier].append(shopping_item.dict())
    
    return shopping_list

# Plain text shopping list for messaging (especially Singha99)
@api_router.get("/shopping-list-text/{supplier}")
async def get_shopping_list_text(supplier: str):
    shopping_data = await get_shopping_list()
    
    if supplier not in shopping_data:
        return {"text": f"No items needed from {supplier}"}
    
    items = shopping_data[supplier]
    
    # Create plain text format
    text_lines = [f"Order for {supplier}:", ""]
    total_cost = 0
    
    for item in items:
        case_calc = item['case_calculation']
        name = item['item_name']
        cost = item['estimated_cost']
        total_cost += cost
        
        if case_calc['cases_to_buy'] > 0:
            text_lines.append(f"• {name}: {case_calc['display_text']} - ฿{cost:.2f}")
        else:
            text_lines.append(f"• {name}: {item['need_to_buy_units']} units - ฿{cost:.2f}")
    
    text_lines.append("")
    text_lines.append(f"Total: ฿{total_cost:.2f}")
    
    return {"text": "\n".join(text_lines), "total_cost": total_cost}

# Quick restock check
@api_router.get("/quick-restock")
async def get_quick_restock():
    # Get items that are below minimum stock
    items = await db.items.find().to_list(1000)
    counts = await db.stock_counts.find().to_list(1000)
    
    stock_map = {count['item_id']: count for count in counts}
    
    low_stock_items = []
    
    for item in items:
        item_obj = Item(**parse_from_mongo(item))
        current_stock = 0
        
        if item_obj.id in stock_map:
            current_stock = stock_map[item_obj.id]['total_count']
        
        if current_stock < item_obj.min_stock:
            low_stock_items.append({
                "item_name": item_obj.name,
                "item_id": item_obj.id,
                "current_stock": current_stock,
                "min_stock": item_obj.min_stock,
                "category": item_obj.category_name,
                "primary_supplier": item_obj.primary_supplier
            })
    
    return low_stock_items

# Stock Sessions for historical tracking
@api_router.post("/stock-sessions", response_model=StockSession)
async def create_stock_session(session: StockSessionCreate):
    # Mark all other sessions as inactive
    await db.stock_sessions.update_many({}, {"$set": {"is_active": False}})
    
    session_obj = StockSession(**session.dict())
    await db.stock_sessions.insert_one(prepare_for_mongo(session_obj.dict()))
    return session_obj

@api_router.get("/stock-sessions", response_model=List[StockSession])
async def get_stock_sessions():
    sessions = await db.stock_sessions.find().sort("session_date", -1).to_list(100)
    return [StockSession(**parse_from_mongo(session)) for session in sessions]

@api_router.get("/stock-sessions/current", response_model=Optional[StockSession])
async def get_current_session():
    session = await db.stock_sessions.find_one({"is_active": True})
    if session:
        return StockSession(**parse_from_mongo(session))
    return None

# Purchase management endpoints
@api_router.post("/purchases", response_model=PurchaseEntry)
async def create_purchase_entry(purchase: PurchaseEntryCreate):
    purchase_obj = PurchaseEntry(**purchase.dict())
    await db.purchases.insert_one(prepare_for_mongo(purchase_obj.dict()))
    return purchase_obj

@api_router.get("/purchases/session/{session_id}", response_model=List[PurchaseEntry])
async def get_session_purchases(session_id: str):
    purchases = await db.purchases.find({"session_id": session_id}).to_list(1000)
    return [PurchaseEntry(**parse_from_mongo(purchase)) for purchase in purchases]

@api_router.put("/purchases/{purchase_id}", response_model=PurchaseEntry)
async def update_purchase_entry(purchase_id: str, purchase_update: PurchaseEntryCreate):
    update_dict = purchase_update.dict()
    result = await db.purchases.update_one(
        {"id": purchase_id}, 
        {"$set": update_dict}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Purchase entry not found")
    
    updated_purchase = await db.purchases.find_one({"id": purchase_id})
    return PurchaseEntry(**parse_from_mongo(updated_purchase))

@api_router.delete("/purchases/{purchase_id}")
async def delete_purchase_entry(purchase_id: str):
    result = await db.purchases.delete_one({"id": purchase_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Purchase entry not found")
    return {"message": "Purchase entry deleted successfully"}

# Historical analysis and reporting endpoints
@api_router.get("/reports/session-comparison/{session1_id}/{session2_id}")
async def compare_sessions(session1_id: str, session2_id: str):
    # Get both sessions
    session1 = await db.stock_sessions.find_one({"id": session1_id})
    session2 = await db.stock_sessions.find_one({"id": session2_id})
    
    if not session1 or not session2:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Get stock counts for both sessions from historical_counts collection
    counts1 = await db.historical_counts.find({"session_id": session1_id}).to_list(1000)
    counts2 = await db.historical_counts.find({"session_id": session2_id}).to_list(1000)
    
    # Get purchases between sessions (purchases made after session1 and before/during session2)
    # For now, we'll look for purchases in either session
    purchases = await db.purchases.find({
        "$or": [
            {"session_id": session1_id},
            {"session_id": session2_id}
        ]
    }).to_list(1000)
    
    # Get all items for reference
    items = await db.items.find().to_list(1000)
    items_map = {item['id']: item for item in items}
    
    # Calculate usage and costs
    item_comparisons = []
    total_usage_cost = 0.0
    
    counts1_map = {count['item_id']: count for count in counts1}
    counts2_map = {count['item_id']: count for count in counts2}
    purchases_map = {purchase['item_id']: purchase for purchase in purchases}
    
    for item in items:
        item_id = item['id']
        item_name = item['name']
        
        # Get counts (default to 0 if not found)
        opening_stock = counts1_map.get(item_id, {}).get('total_count', 0)
        closing_stock = counts2_map.get(item_id, {}).get('total_count', 0)
        
        # Get purchases (default to 0 if not found)
        purchases_made = purchases_map.get(item_id, {}).get('actual_quantity', 0)
        
        # Calculate usage: opening + purchases - closing
        calculated_usage = opening_stock + purchases_made - closing_stock
        
        # Calculate cost
        cost_per_unit = item.get('cost_per_unit', 0.0)
        usage_cost = calculated_usage * cost_per_unit if calculated_usage > 0 else 0.0
        total_usage_cost += usage_cost
        
        if calculated_usage != 0 or purchases_made != 0:  # Only include items with activity
            item_comparisons.append({
                "item_id": item_id,
                "item_name": item_name,
                "opening_stock": opening_stock,
                "purchases_made": purchases_made,
                "closing_stock": closing_stock,
                "calculated_usage": calculated_usage,
                "cost_per_unit": cost_per_unit,
                "usage_cost": usage_cost,
                "supplier": item.get('primary_supplier', 'Unknown')
            })
    
    # Calculate period between sessions
    session1_date = datetime.fromisoformat(session1['session_date'].replace('Z', '+00:00')) if isinstance(session1['session_date'], str) else session1['session_date']
    session2_date = datetime.fromisoformat(session2['session_date'].replace('Z', '+00:00')) if isinstance(session2['session_date'], str) else session2['session_date']
    period_days = (session2_date - session1_date).days
    
    return {
        "session1_id": session1_id,
        "session1_name": session1['session_name'],
        "session1_date": session1_date,
        "session2_id": session2_id,
        "session2_name": session2['session_name'],
        "session2_date": session2_date,
        "item_comparisons": item_comparisons,
        "total_usage_cost": total_usage_cost,
        "period_days": period_days
    }

@api_router.get("/reports/usage-summary")
async def get_usage_summary():
    # Get last two sessions
    sessions = await db.stock_sessions.find().sort("session_date", -1).limit(2).to_list(2)
    
    if len(sessions) < 2:
        return {"message": "Need at least 2 sessions to generate usage report", "sessions_available": len(sessions)}
    
    # Use the comparison endpoint logic
    latest_session = sessions[0]
    previous_session = sessions[1]
    
    return await compare_sessions(previous_session['id'], latest_session['id'])

# Endpoint to save current stock counts to a session
@api_router.post("/stock-sessions/{session_id}/save-counts")
async def save_counts_to_session(session_id: str):
    # Get current stock counts
    current_counts = await db.stock_counts.find().to_list(1000)
    
    if not current_counts:
        raise HTTPException(status_code=400, detail="No stock counts available to save")
    
    # Save each count with session_id reference
    for count in current_counts:
        # Remove the MongoDB _id to avoid conflicts
        if '_id' in count:
            del count['_id']
        count['session_id'] = session_id
        count['saved_date'] = datetime.now(timezone.utc)
        # Create a historical record
        await db.historical_counts.insert_one(prepare_for_mongo(count))
    
    return {"message": f"Saved {len(current_counts)} stock counts to session", "count": len(current_counts)}

# Initialize with real data from spreadsheet
@api_router.post("/initialize-real-data")
async def initialize_real_data():
    # Clear existing data
    await db.items.delete_many({})
    await db.stock_counts.delete_many({})
    
    # Enhanced real items based on the spreadsheet with proper case calculations and complete data
    real_items = [
        # Beers (most popular items) - commonly bought by case
        {"name": "Big Chang", "category": "B", "category_name": "Beer", "units_per_case": 15, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 44.0, "cost_per_case": 660.0, "bought_by_case": True},
        {"name": "Small Chang", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 48, "max_stock": 192, "primary_supplier": "Singha99", "cost_per_unit": 45.0, "cost_per_case": 1080.0, "bought_by_case": True},
        {"name": "Big Leo", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 45.0, "cost_per_case": 540.0, "bought_by_case": True},
        {"name": "Small Leo", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 48, "max_stock": 192, "primary_supplier": "Singha99", "cost_per_unit": 45.0, "cost_per_case": 1080.0, "bought_by_case": True},
        {"name": "Big Singha", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 50.08, "cost_per_case": 601.0, "bought_by_case": True},
        {"name": "Small Singha", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 48, "max_stock": 192, "primary_supplier": "Singha99", "cost_per_unit": 27.08, "cost_per_case": 650.0, "bought_by_case": True},
        {"name": "Small Heineken", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 31.75, "cost_per_case": 762.0, "bought_by_case": True},
        {"name": "Small San Miguel Lite", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 30.75, "cost_per_case": 738.0, "bought_by_case": True},
        {"name": "Bam Bam (can)", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 12, "max_stock": 48, "primary_supplier": "Vendor", "cost_per_unit": 14.0, "cost_per_case": 168.0, "bought_by_case": True},
        {"name": "Soju", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 12, "max_stock": 48, "primary_supplier": "Vendor", "cost_per_unit": 0.75, "cost_per_case": 9.0, "bought_by_case": True},
        
        # Thai Alcohol - commonly bought by case/box
        {"name": "Charles House Rum", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 24.0, "cost_per_case": 288.0, "bought_by_case": True},
        {"name": "Charles House Gin", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 23.0, "cost_per_case": 276.0, "bought_by_case": True},
        {"name": "Yeow Ngeah Vodka", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Vendor", "cost_per_unit": 15.0, "cost_per_case": 180.0, "bought_by_case": True},
        {"name": "Sangsom (Black)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Singha99", "cost_per_unit": 45.0, "cost_per_case": 540.0, "bought_by_case": True},
        {"name": "Hong Thong", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Singha99", "cost_per_unit": 4.0, "cost_per_case": 48.0, "bought_by_case": True},
        
        # Import Alcohol (premium by bottle)
        {"name": "Bacardi Rum", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "zBKK", "cost_per_unit": 850.0},
        {"name": "Jack Daniels", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "zBKK", "cost_per_unit": 1200.0},
        {"name": "Grey Goose Vodka", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 2500.0},
        {"name": "Bombay Gin", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 900.0},
        {"name": "Captain Morgan Spiced Rum", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 750.0},
        {"name": "Jagermeister", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 1100.0},
        {"name": "Jose Cuervo Gold Tequila", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 850.0},
        {"name": "Skyy Vodka", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 650.0},
        
        # Mixers - case items marked as commonly bought by case
        {"name": "Big Coke", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 12.0, "cost_per_case": 144.0, "bought_by_case": True},
        {"name": "Big Sprite", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 12.0, "cost_per_case": 144.0, "bought_by_case": True},
        {"name": "Soda Water", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 48, "max_stock": 144, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Tonic Water", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 48, "max_stock": 144, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Schweppes Lime", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Schweppes Ginger Ale", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Fanta Orange", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Red Bull", "category": "M", "category_name": "Mixers", "units_per_case": 50, "min_stock": 100, "max_stock": 300, "primary_supplier": "Singha99", "cost_per_unit": 4.0, "cost_per_case": 200.0, "bought_by_case": True},
        {"name": "Small Water (600ml)", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 5.5, "cost_per_case": 66.0, "bought_by_case": True},
        {"name": "Big Water (1.5L)", "category": "M", "category_name": "Mixers", "units_per_case": 6, "min_stock": 12, "max_stock": 48, "primary_supplier": "Singha99", "cost_per_unit": 5.5, "cost_per_case": 33.0, "bought_by_case": True},
        {"name": "Orange Juice (1L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 55.0},
        {"name": "Cranberry Juice (1L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Singha99", "cost_per_unit": 65.0},
        
        # Bar Supplies
        {"name": "Buckets", "category": "O", "category_name": "Bar Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 10, "primary_supplier": "Makro", "cost_per_unit": 59.0},
        {"name": "Limes (25 pack)", "category": "O", "category_name": "Bar Supplies", "units_per_case": 25, "min_stock": 50, "max_stock": 200, "primary_supplier": "Makro", "cost_per_unit": 0.4, "cost_per_case": 10.0},
        {"name": "Plastic Cups (16oz)", "category": "O", "category_name": "Bar Supplies", "units_per_case": 50, "min_stock": 100, "max_stock": 500, "primary_supplier": "Makro", "cost_per_unit": 2.18, "cost_per_case": 109.0},
        {"name": "Paper Cups (16oz)", "category": "O", "category_name": "Bar Supplies", "units_per_case": 50, "min_stock": 100, "max_stock": 500, "primary_supplier": "Makro", "cost_per_unit": 1.58, "cost_per_case": 79.0},
        {"name": "Straws", "category": "O", "category_name": "Bar Supplies", "units_per_case": 100, "min_stock": 200, "max_stock": 1000, "primary_supplier": "Makro", "cost_per_unit": 0.68, "cost_per_case": 68.0},
        
        # Missing Import Alcohol (Premium Spirits)
        {"name": "Fireball", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 1050.0},
        {"name": "Jack Daniels Honey", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 1300.0},
        {"name": "Jameson", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 1400.0},
        {"name": "Jose Cuervo Silver Tequila", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 900.0},
        {"name": "Malibu", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 800.0},
        {"name": "Bacardi Black Rum", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 900.0},
        
        # Missing Thai Alcohol & Liqueurs
        {"name": "Thai Tequila (Matador)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Singha99", "cost_per_unit": 280.0},
        {"name": "Thai Malibu (Coconut Liquor)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Singha99", "cost_per_unit": 250.0},
        {"name": "Fox (Jagermeister)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Singha99", "cost_per_unit": 320.0},
        {"name": "Dark Rum (Phoenix)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Singha99", "cost_per_unit": 200.0},
        {"name": "Triplesec (Charles House)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "Singha99", "cost_per_unit": 180.0},
        {"name": "Blue Curacao (Charles House)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "Singha99", "cost_per_unit": 200.0},
        {"name": "Sambuca", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Singha99", "cost_per_unit": 450.0},
        {"name": "Peach Schnapps", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "Singha99", "cost_per_unit": 220.0},
        
        # Missing Mixers & Concentrates
        {"name": "Fanta Strawberry", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 12, "max_stock": 48, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Blue Concentrate", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 150.0},
        {"name": "Orange Concentrate (45L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 800.0},
        {"name": "Pineapple Juice (1L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Makro", "cost_per_unit": 65.0},
        {"name": "Pineapple Concentrate (11.5L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 450.0},
        {"name": "Mango Juice (1L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Makro", "cost_per_unit": 70.0},
        {"name": "Mango Concentrate (11.5L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 480.0},
        {"name": "Strawberry Concentrate (11.5L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 460.0},
        {"name": "Passionfruit Concentrate (11.5L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 500.0},
        {"name": "Lime Juice", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 45.0},
        {"name": "Grenadine", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 85.0},
        
        # Complete Housekeeping & Supplies
        {"name": "Toilet Paper (Jumbo Roll)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 4, "min_stock": 8, "max_stock": 32, "primary_supplier": "Makro", "cost_per_unit": 45.0, "cost_per_case": 180.0},
        {"name": "Toilet Paper (Small Roll)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 24, "min_stock": 24, "max_stock": 96, "primary_supplier": "Makro", "cost_per_unit": 5.0, "cost_per_case": 120.0},
        {"name": "Trash Bags Small (24x28)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 5, "min_stock": 10, "max_stock": 50, "primary_supplier": "Makro", "cost_per_unit": 15.0, "cost_per_case": 75.0},
        {"name": "Trash Bags Big (30x40)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 5, "min_stock": 10, "max_stock": 40, "primary_supplier": "Makro", "cost_per_unit": 25.0, "cost_per_case": 125.0},
        {"name": "Floor Cleaner (Concentrate)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 4, "min_stock": 4, "max_stock": 16, "primary_supplier": "Makro", "cost_per_unit": 28.0, "cost_per_case": 112.0},
        {"name": "Toilet Cleaner", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 35.0},
        {"name": "Bleach", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 25.0},
        {"name": "Laundry Washing Powder (25kg)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 350.0},
        {"name": "Laundry Softener (20L)", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "Makro", "cost_per_unit": 180.0},
        {"name": "Hand Soap", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Makro", "cost_per_unit": 35.0},
        {"name": "Body Soap", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Makro", "cost_per_unit": 40.0},
        {"name": "Shampoo", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 65.0},
        {"name": "Air Freshener Spray", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 45.0},
        {"name": "Dish Soap", "category": "Z", "category_name": "Hostel Supplies", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "Makro", "cost_per_unit": 30.0},
    ]
    
    # Insert real items
    for item_data in real_items:
        item = Item(**item_data)
        await db.items.insert_one(prepare_for_mongo(item.dict()))
    
    return {"message": "Complete data initialized successfully - ALL items from spreadsheet", "items_count": len(real_items)}

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()