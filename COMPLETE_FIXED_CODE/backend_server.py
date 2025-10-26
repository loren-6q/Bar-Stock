from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'bar_stock')
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Create the main app
app = FastAPI(title="Bar Stock Management API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Helper functions for MongoDB
def prepare_for_mongo(data):
    if isinstance(data, dict):
        if '_id' in data:
            del data['_id']
        for key, value in data.items():
            if isinstance(value, datetime):
                data[key] = value.isoformat()
    return data

def parse_from_mongo(item):
    if item and '_id' in item:
        del item['_id']
    return item

# Pydantic Models
class Item(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    category: str = "O"  # O=Other, B=Beer, A=Alcohol, M=Mixer, Z=Hostel
    category_name: str = "Other"
    units_per_case: int = 1
    min_stock: int = 0
    max_stock: int = 100
    primary_supplier: str = "Unknown"
    cost_per_unit: float = 0.0
    cost_per_case: Optional[float] = None
    bought_by_case: bool = False

class ItemCreate(BaseModel):
    name: str
    category: str
    category_name: str
    units_per_case: int = 1
    min_stock: int = 0
    max_stock: int = 100
    primary_supplier: str
    cost_per_unit: float = 0.0
    cost_per_case: Optional[float] = None
    bought_by_case: bool = False

class StockCount(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    item_id: str
    main_bar: int = 0
    beer_bar: int = 0
    lobby: int = 0
    storage_room: int = 0
    total_count: int = 0
    count_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StockCountUpdate(BaseModel):
    main_bar: int = 0
    beer_bar: int = 0
    lobby: int = 0
    storage_room: int = 0

class StockSession(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    session_name: str
    session_date: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    session_type: str = "full_count"
    is_active: bool = True
    notes: Optional[str] = None

class StockSessionCreate(BaseModel):
    session_name: str
    session_type: str = "full_count"
    notes: Optional[str] = None

class CaseCalculation(BaseModel):
    total_units: int
    cases_needed: int
    extra_units: int
    display_text: str

class ShoppingItem(BaseModel):
    item_id: str
    item_name: str
    current_stock: int
    max_stock: int
    need_to_buy: int
    case_calculation: CaseCalculation
    estimated_cost: float

# API Routes
@api_router.get("/items", response_model=List[Item])
async def get_items():
    items = await db.items.find().to_list(1000)
    return [Item(**parse_from_mongo(item)) for item in items]

@api_router.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    item_obj = Item(**item.dict())
    await db.items.insert_one(prepare_for_mongo(item_obj.dict()))
    return item_obj

@api_router.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: str, item_update: ItemCreate):
    result = await db.items.update_one(
        {"id": item_id}, 
        {"$set": prepare_for_mongo(item_update.dict())}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    updated_item = await db.items.find_one({"id": item_id})
    return Item(**parse_from_mongo(updated_item))

@api_router.delete("/items/{item_id}")
async def delete_item(item_id: str):
    result = await db.items.delete_one({"id": item_id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Item not found")
    
    # Also delete related stock counts
    await db.stock_counts.delete_many({"item_id": item_id})
    return {"message": "Item deleted successfully"}

@api_router.get("/stock-counts", response_model=List[StockCount])
async def get_stock_counts():
    counts = await db.stock_counts.find().to_list(1000)
    return [StockCount(**parse_from_mongo(count)) for count in counts]

@api_router.put("/stock-counts/{item_id}", response_model=StockCount)
async def update_stock_count(item_id: str, stock_update: StockCountUpdate):
    update_dict = {k: v for k, v in stock_update.dict().items() if v is not None}
    update_dict['total_count'] = sum(v for v in update_dict.values() if isinstance(v, int))
    
    result = await db.stock_counts.update_one({"item_id": item_id}, {"$set": update_dict})
    if result.matched_count == 0:
        # Create new stock count if it doesn't exist
        new_count = StockCount(item_id=item_id, **update_dict)
        await db.stock_counts.insert_one(prepare_for_mongo(new_count.dict()))
        return new_count
    
    updated_count = await db.stock_counts.find_one({"item_id": item_id})
    return StockCount(**parse_from_mongo(updated_count))

@api_router.get("/shopping-list")
async def get_shopping_list():
    # Get all items and their current stock counts
    items = await db.items.find().to_list(1000)
    stock_counts = await db.stock_counts.find().to_list(1000)
    
    # Create a map of item_id to stock count
    stock_map = {count['item_id']: count for count in stock_counts}
    
    # Group by supplier
    suppliers = {}
    
    for item in items:
        current_stock = stock_map.get(item['id'], {}).get('total_count', 0)
        max_stock = item.get('max_stock', 0)
        
        if current_stock < max_stock:
            need_to_buy = max_stock - current_stock
            
            # Calculate cases needed
            units_per_case = item.get('units_per_case', 1)
            cases_needed = need_to_buy // units_per_case if units_per_case > 1 else 0
            extra_units = need_to_buy % units_per_case if units_per_case > 1 else need_to_buy
            
            if units_per_case > 1 and cases_needed > 0:
                if extra_units > 0:
                    display_text = f"{cases_needed} cases + {extra_units} units"
                else:
                    display_text = f"{cases_needed} cases"
            else:
                display_text = f"{need_to_buy} units"
            
            case_calculation = CaseCalculation(
                total_units=need_to_buy,
                cases_needed=cases_needed,
                extra_units=extra_units,
                display_text=display_text
            )
            
            # Calculate estimated cost
            cost_per_unit = item.get('cost_per_unit', 0)
            estimated_cost = need_to_buy * cost_per_unit
            
            supplier = item.get('primary_supplier', 'Unknown')
            
            if supplier not in suppliers:
                suppliers[supplier] = {
                    'supplier': supplier,
                    'items': [],
                    'total_cost': 0
                }
            
            shopping_item = ShoppingItem(
                item_id=item['id'],
                item_name=item['name'],
                current_stock=current_stock,
                max_stock=max_stock,
                need_to_buy=need_to_buy,
                case_calculation=case_calculation,
                estimated_cost=estimated_cost
            )
            
            suppliers[supplier]['items'].append(shopping_item.dict())
            suppliers[supplier]['total_cost'] += estimated_cost
    
    return suppliers

@api_router.post("/stock-sessions", response_model=StockSession)
async def create_stock_session(session: StockSessionCreate):
    # Deactivate any existing active sessions
    await db.stock_sessions.update_many(
        {"is_active": True}, 
        {"$set": {"is_active": False}}
    )
    
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

@api_router.post("/initialize-real-data")
async def initialize_real_data():
    # Clear existing items
    await db.items.delete_many({})
    
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
        {"name": "Red Bull", "category": "M", "category_name": "Mixers", "units_per_case": 50, "min_stock": 100, "max_stock": 300, "primary_supplier": "Singha99", "cost_per_unit": 4.0, "cost_per_case": 200.0, "bought_by_case": True},
        {"name": "Big Coke", "category": "M", "category_name": "Mixers", "units_per_case": 12, "min_stock": 24, "max_stock": 96, "primary_supplier": "Singha99", "cost_per_unit": 12.0, "cost_per_case": 144.0, "bought_by_case": True},
        {"name": "Soda Water", "category": "M", "category_name": "Mixers", "units_per_case": 24, "min_stock": 48, "max_stock": 144, "primary_supplier": "Singha99", "cost_per_unit": 10.0, "cost_per_case": 240.0, "bought_by_case": True},
        {"name": "Sangsom (Black)", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Singha99", "cost_per_unit": 45.0, "cost_per_case": 540.0, "bought_by_case": True},
        {"name": "Charles House Rum", "category": "A", "category_name": "Thai Alcohol", "units_per_case": 12, "min_stock": 6, "max_stock": 24, "primary_supplier": "Makro", "cost_per_unit": 24.0, "cost_per_case": 288.0, "bought_by_case": True},
        {"name": "Jack Daniels", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 6, "primary_supplier": "zBKK", "cost_per_unit": 1200.0, "bought_by_case": False},
        {"name": "Grey Goose Vodka", "category": "A", "category_name": "Import Alcohol", "units_per_case": 1, "min_stock": 1, "max_stock": 4, "primary_supplier": "zBKK", "cost_per_unit": 2500.0, "bought_by_case": False},
        {"name": "Limes (25 pack)", "category": "O", "category_name": "Bar Supplies", "units_per_case": 25, "min_stock": 50, "max_stock": 200, "primary_supplier": "Makro", "cost_per_unit": 0.4, "cost_per_case": 10.0, "bought_by_case": False},
        {"name": "Plastic Cups (16oz)", "category": "O", "category_name": "Bar Supplies", "units_per_case": 50, "min_stock": 100, "max_stock": 500, "primary_supplier": "Makro", "cost_per_unit": 2.18, "cost_per_case": 109.0, "bought_by_case": False}
    ]
    
    # Insert items
    items_to_insert = []
    for item_data in real_items:
        item = Item(**item_data)
        items_to_insert.append(prepare_for_mongo(item.dict()))
    
    await db.items.insert_many(items_to_insert)
    return {"message": "Complete data initialized successfully - ALL items from spreadsheet", "items_count": len(real_items)}

# Include the API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Bar Stock Management API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)