from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from pydantic import BaseModel
from typing import List, Optional
import sys
import os
import shutil
from dotenv import load_dotenv

load_dotenv()

# Add root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from fastapi.middleware.cors import CORSMiddleware
from services.data_manager import DataManager

app = FastAPI(title="AI Pricing Assistant API v2")

# Enable CORS for Excel Add-in
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

manager = DataManager()

class ItemSearchResponse(BaseModel):
    id: int
    name: str

class MatchRequest(BaseModel):
    items: List[str]
    type: Optional[str] = "material"  # "material" or "labor"

@app.post("/match")
def match_items(req: MatchRequest):
    results = {}
    price_field = 'price_labor' if req.type == 'labor' else 'price_material'
    
    for item in req.items:
        # Use fuzzy search from DB
        matches = manager.db.search(item, limit=1)
        if matches:
            best = matches[0]
            results[item] = {
                "price": best.get(price_field, 0),
                "unit": best.get('unit', 'ks'),
                "source": best.get('source'),
                "date": str(best.get('date')),
                "item_id": best.get('id'),
                "original_name": best.get('item'),
                "match_score": best.get('match_score', 0)
            }
    return results

class SuggestionRequest(BaseModel):
    material_name: str

@app.post("/match/labor-suggestions")
def suggest_labor(req: SuggestionRequest):
    """Suggest best labor items from DB based on material name."""
    # 1. Fetch all labor items from DB
    labor_catalog = manager.db.get_labor_items()
    if not labor_catalog:
        return []
    
    # 2. Use AI to find best matches within the internal catalog
    suggestions = manager.ai.suggest_labor(req.material_name, labor_catalog)
    return suggestions

class HistoryPoint(BaseModel):
    date: str
    vendor: str
    price_material: float
    price_labor: float

@app.get("/")
def read_root():
    return {"message": "AI Pricing Assistant v2 is online"}

@app.get("/search", response_model=List[ItemSearchResponse])
def search_items(q: str):
    return manager.db.search_items(q)

@app.get("/items/{item_id}/history", response_model=List[HistoryPoint])
def get_item_history(item_id: int):
    results = manager.db.get_price_history(item_id)
    # Convert date objects to string for JSON serialization
    for r in results:
        r['date'] = str(r['date'])
    return results

@app.get("/items/{item_id}/details")
def get_item_details(item_id: int):
    """Get full details for an item including all sources and price history."""
    details = manager.db.get_item_details(item_id)
    if not details:
        raise HTTPException(status_code=404, detail="Item not found")
    return details

@app.delete("/items/{item_id}")
def delete_item(item_id: int):
    """Delete an item and all its prices (blacklist)."""
    success = manager.db.delete_item(item_id)
    if not success:
        raise HTTPException(status_code=404, detail="Item not found")
    return {"status": "deleted", "item_id": item_id}

class AddPriceRequest(BaseModel):
    name: str
    price_material: float = 0.0
    price_labor: float = 0.0
    unit: str = "ks"

@app.post("/items/add")
def add_custom_item(req: AddPriceRequest):
    """Add a user-defined item with custom price."""
    item_id = manager.db.add_custom_item(
        name=req.name,
        price_material=req.price_material,
        price_labor=req.price_labor,
        unit=req.unit
    )
    return {"status": "added", "item_id": item_id, "name": req.name}

@app.get("/status")
def get_status():
    try:
        stats = manager.db.get_stats()
        return {
            "status": "online", 
            "total_items": stats['items'], 
            "total_prices": stats['prices'],
            "database_path": stats['url']
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/ingest/upload")
async def ingest_file(file: UploadFile = File(...), file_type: Optional[str] = Form(None)):
    temp_path = f"Input/temp_{file.filename}"
    os.makedirs("Input", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = manager.process_file(temp_path, file_type_override=file_type)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return result
    
@app.get("/admin/items")
def get_admin_items():
    """Get all items with latest prices for the admin sync sheet."""
    return manager.db.get_all_items_admin()

class AdminSyncItem(BaseModel):
    id: Optional[int]
    name: str
    price_material: float
    price_labor: float
    unit: str

@app.post("/admin/batch-delete")
def batch_delete_items(item_ids: List[int]):
    """Delete multiple items from the database."""
    success = manager.db.delete_items(item_ids)
    return {"status": "success", "deleted_count": len(item_ids)}

@app.post("/admin/sync")
def sync_admin_data(items: List[AdminSyncItem]):
    """Sync changes from the admin sheet to the database."""
    # Convert Pydantic models to dicts
    data = [it.dict() for it in items]
    success = manager.db.sync_admin_items(data)
    return {"status": "success", "synced_count": len(data)}

@app.post("/admin/reset-database")
def reset_database():
    """Emergency: Wipes all data from the database."""
    success = manager.db.reset_all_data()
    return {"status": "success", "message": "Database has been completely reset."}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
