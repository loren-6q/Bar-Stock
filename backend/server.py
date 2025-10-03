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

# New models for historical tracking and purchase confirmation
class PurchaseEntry(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_id: str
    item_id: str
    planned_quantity: int  # from shopping list
    actual_quantity: int  # what was actually bought
    cost_per_unit: float
    total_cost: float
    supplier: str
    purchase_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    notes: Optional[str] = None

class PurchaseEntryCreate(BaseModel):
    session_id: str
    item_id: str
    planned_quantity: int
    actual_quantity: int
    cost_per_unit: float
    total_cost: float
    supplier: str
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

# Initialize with real data from spreadsheet
@api_router.post("/initialize-real-data")
async def initialize_real_data():
    # Clear existing data
    await db.items.delete_many({})
    await db.stock_counts.delete_many({})
    
    # Real items based on the spreadsheet with proper case calculations
    real_items = [
        # Beers (most common items)
        {"name": "Big Chang", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 50, "max_stock": 200, "primary_supplier": "Singha99", "cost_per_unit": 32.0, "cost_per_case": 750.0},
        {"name": "Small Chang", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 50, "max_stock": 200, "primary_supplier": "Singha99", "cost_per_unit": 28.0, "cost_per_case": 650.0},
        {"name": "Big Leo", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 35.0, "cost_per_case": 400.0},
        {"name": "Small Leo", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 30.0, "cost_per_case": 700.0},
        {"name": "Big Singha", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 38.0, "cost_per_case": 440.0},
        {"name": "Small Singha", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 32.0, "cost_per_case": 750.0},
        {"name": "Small Heineken", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 20, "max_stock": 80, "primary_supplier": "Singha99", "cost_per_unit": 42.0, "cost_per_case": 980.0},
        
        # Thai Alcohol
        {"name": "Sangsom (Black)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 8, "max_stock": 30, "primary_supplier": "Singha99", "cost_per_unit": 220.0, "cost_per_case": 2500.0},
        {"name": "Hong Thong", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 8, "max_stock": 30, "primary_supplier": "Singha99", "cost_per_unit": 190.0, "cost_per_case": 2200.0},
        {"name": "Thai Tequila", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 4, "max_stock": 15, "primary_supplier": "Singha99", "cost_per_unit": 280.0},
        {"name": "Fox (Jagermeister)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 1, "min_stock": 3, "max_stock": 12, "primary_supplier": "Singha99", "cost_per_unit": 320.0},
        
        # Import Alcohol (by bottle)
        {"name": "Jack Daniels", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "zBKK", "cost_per_unit": 1200.0},
        {"name": "Bacardi Rum", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 2, "max_stock": 8, "primary_supplier": "zBKK", "cost_per_unit": 850.0},
        {"name": "Grey Goose Vodka", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 2500.0},
        
        # Mixers
        {"name": "Big Coke", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 22.0, "cost_per_case": 250.0},
        {"name": "Big Sprite", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 30, "max_stock": 120, "primary_supplier": "Singha99", "cost_per_unit": 22.0, "cost_per_case": 250.0},
        {"name": "Soda Water", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 40, "max_stock": 150, "primary_supplier": "Singha99", "cost_per_unit": 18.0, "cost_per_case": 400.0},
        {"name": "Tonic Water", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 30, "max_stock": 100, "primary_supplier": "Singha99", "cost_per_unit": 25.0, "cost_per_case": 580.0},
        {"name": "Red Bull", "category": "M", "category_name": "Mixers", "units_per_case": 50, "min_stock": 100, "max_stock": 400, "primary_supplier": "Singha99", "cost_per_unit": 15.0, "cost_per_case": 720.0},
        {"name": "Orange Juice (1L)", "category": "M", "category_name": "Mixers", "units_per_case": 1, "min_stock": 10, "max_stock": 40, "primary_supplier": "Singha99", "cost_per_unit": 55.0},
        
        # Other Bar Supplies  
        {"name": "Limes (bag)", "category": "O", "category_name": "Other Bar", "units_per_case": 1, "min_stock": 5, "max_stock": 20, "primary_supplier": "Local Market", "cost_per_unit": 40.0},
        {"name": "Plastic Cups", "category": "O", "category_name": "Other Bar", "units_per_case": 100, "min_stock": 200, "max_stock": 1000, "primary_supplier": "Makro", "cost_per_unit": 1.2, "cost_per_case": 120.0},
        {"name": "Straws", "category": "O", "category_name": "Other Bar", "units_per_case": 500, "min_stock": 1000, "max_stock": 5000, "primary_supplier": "Makro", "cost_per_unit": 0.17, "cost_per_case": 85.0},
        
        # Makro items
        {"name": "Vodka (Charles House)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 180.0, "cost_per_case": 2000.0},
        {"name": "Gin (Charles House)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 180.0, "cost_per_case": 2000.0},
    ]
    
    # Insert real items
    for item_data in real_items:
        item = Item(**item_data)
        await db.items.insert_one(prepare_for_mongo(item.dict()))
    
    return {"message": "Real data initialized successfully", "items_count": len(real_items)}

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