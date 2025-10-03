from fastapi import FastAPI, APIRouter, HTTPException
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
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

class ShoppingListItem(BaseModel):
    item_name: str
    item_id: str
    current_stock: int
    min_stock: int
    max_stock: int
    need_to_buy: int
    supplier: str
    cost_per_unit: float
    estimated_cost: float

class StockSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str
    session_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    is_active: bool = True
    session_type: str = "full_count"  # full_count or quick_restock

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
    result = await db.items.update_one(
        {"id": item_id}, 
        {"$set": item_update.dict()}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = await db.items.find_one({"id": item_id})
    return Item(**parse_from_mongo(updated_item))

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
        update_data = {}
        total = 0
        
        # Update only provided fields
        for field, value in count_update.dict().items():
            if value is not None:
                update_data[field] = value
        
        # Get current values for total calculation
        current_count = StockCount(**parse_from_mongo(existing_count))
        updated_count = current_count.copy(update=update_data)
        updated_count.total_count = updated_count.main_bar + updated_count.beer_bar + updated_count.lobby + updated_count.storage_room
        
        result = await db.stock_counts.update_one(
            {"item_id": item_id},
            {"$set": prepare_for_mongo(updated_count.dict())}
        )
        return updated_count
    else:
        # Create new count
        count_dict = {"item_id": item_id}
        count_dict.update(count_update.dict())
        total = sum([v for v in count_dict.values() if isinstance(v, int)])
        count_dict['total_count'] = total
        
        count_obj = StockCount(**count_dict)
        await db.stock_counts.insert_one(prepare_for_mongo(count_obj.dict()))
        return count_obj

# Shopping list endpoint
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
            
            shopping_item = ShoppingListItem(
                item_name=item_obj.name,
                item_id=item_obj.id,
                current_stock=current_stock,
                min_stock=item_obj.min_stock,
                max_stock=item_obj.max_stock,
                need_to_buy=need_to_buy,
                supplier=supplier,
                cost_per_unit=item_obj.cost_per_unit,
                estimated_cost=need_to_buy * item_obj.cost_per_unit
            )
            
            shopping_list[supplier].append(shopping_item.dict())
    
    return shopping_list

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

# Initialize with sample data
@api_router.post("/initialize-sample-data")
async def initialize_sample_data():
    # Clear existing data
    await db.items.delete_many({})
    await db.stock_counts.delete_many({})
    
    # Sample items based on the spreadsheet
    sample_items = [
        {"name": "Big Chang", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 50, "max_stock": 200, "primary_supplier": "Makro", "cost_per_unit": 35.0},
        {"name": "Small Chang", "category": "B", "category_name": "Beer", "units_per_case": 24, "min_stock": 30, "max_stock": 120, "primary_supplier": "Makro", "cost_per_unit": 25.0},
        {"name": "Singha Beer", "category": "B", "category_name": "Beer", "units_per_case": 12, "min_stock": 40, "max_stock": 150, "primary_supplier": "Singha99", "cost_per_unit": 38.0},
        {"name": "Thai Whiskey", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 6, "min_stock": 10, "max_stock": 50, "primary_supplier": "Singha99", "cost_per_unit": 450.0},
        {"name": "Vodka", "category": "A", "category_name": "Import Alcohol", "units_per_case": 6, "min_stock": 8, "max_stock": 30, "primary_supplier": "Makro", "cost_per_unit": 800.0},
        {"name": "Coke", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 50, "max_stock": 200, "primary_supplier": "Makro", "cost_per_unit": 18.0},
        {"name": "Orange Juice", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 20, "max_stock": 80, "primary_supplier": "Makro", "cost_per_unit": 25.0},
        {"name": "Limes (bag)", "category": "O", "category_name": "Other Bar", "units_per_case": 1, "min_stock": 5, "max_stock": 20, "primary_supplier": "Local Market", "cost_per_unit": 40.0},
        {"name": "Plastic Cups", "category": "O", "category_name": "Other Bar", "units_per_case": 100, "min_stock": 200, "max_stock": 1000, "primary_supplier": "Makro", "cost_per_unit": 120.0},
        {"name": "Straws", "category": "O", "category_name": "Other Bar", "units_per_case": 500, "min_stock": 1000, "max_stock": 5000, "primary_supplier": "Makro", "cost_per_unit": 85.0},
    ]
    
    # Insert sample items
    for item_data in sample_items:
        item = Item(**item_data)
        await db.items.insert_one(prepare_for_mongo(item.dict()))
    
    return {"message": "Sample data initialized successfully"}

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