from fastapi import FastAPI, HTTPException, UploadFile, File
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

@app.post("/match")
def match_items(req: MatchRequest):
    results = {}
    for item in req.items:
        # Use fuzzy search from DB
        matches = manager.db.search(item, limit=1)
        if matches:
            best = matches[0]
            results[item] = {
                "price": best.get('price_material', 0),
                "price_labor": best.get('price_labor', 0),
                "unit": best.get('unit', 'ks'),
                "source": best.get('source'),
                "date": str(best.get('date'))
            }
    return results

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
async def ingest_file(file: UploadFile = File(...)):
    temp_path = f"Input/temp_{file.filename}"
    os.makedirs("Input", exist_ok=True)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    result = manager.process_file(temp_path)
    
    # Cleanup
    if os.path.exists(temp_path):
        os.remove(temp_path)
        
    return result

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
