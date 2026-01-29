import os
import difflib
from datetime import datetime
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, Date, DateTime, ForeignKey, func, select, or_, text

class PriceDatabase:
    def __init__(self, db_url=None):
        if not db_url:
            # Default to local SQLite if not provided (and not in env)
            db_url = os.getenv("DATABASE_URL", "sqlite:///Input/04_Databaze/prices_v2.db")
        
        # Ensure local dir exists if sqlite
        if db_url.startswith("sqlite"):
            path = db_url.replace("sqlite:///", "")
            os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

        self.engine = create_engine(db_url)
        self.metadata = MetaData()
        
        # Table Definitions
        self.sources = Table('sources', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('filename', String, unique=True),
            Column('vendor', String),
            Column('date_offer', Date),
            Column('created_at', DateTime, server_default=func.now())
        )
        
        self.items = Table('items', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('name', String, unique=True),
            Column('normalized_name', String) # Indexed usually
        )
        
        self.prices = Table('prices', self.metadata,
            Column('id', Integer, primary_key=True),
            Column('item_id', Integer, ForeignKey('items.id')),
            Column('source_id', Integer, ForeignKey('sources.id')),
            Column('price_material', Float),
            Column('price_labor', Float),
            Column('unit', String),
            Column('quantity', Float)
        )
        
        self.metadata.create_all(self.engine)

    def get_stats(self):
        with self.engine.connect() as conn:
            try:
                ic = conn.execute(text("SELECT COUNT(*) FROM items")).scalar()
                pc = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
                return {"items": ic, "prices": pc, "url": str(self.engine.url)}
            except Exception as e:
                return {"items": 0, "prices": 0, "url": str(self.engine.url), "error": str(e)}

    def add_processed_file(self, filename, vendor, date_offer, items_list):
        with self.engine.connect() as conn:
            # 1. Add/Get Source
            # Check existence
            s = select(self.sources.c.id).where(self.sources.c.filename == filename)
            source_id = conn.execute(s).scalar()
            
            if not source_id:
                stmt = self.sources.insert().values(
                    filename=filename, 
                    vendor=vendor, 
                    date_offer=date_offer
                )
                result = conn.execute(stmt)
                source_id = result.inserted_primary_key[0]
            else:
                # Update existing source? For now, keep as is or update date.
                # Assuming overwrite logic:
                stmt = self.sources.update().where(self.sources.c.id == source_id).values(
                    vendor=vendor, date_offer=date_offer
                )
                conn.execute(stmt)
                
            # 2. Add Items & Prices
            # Prepare data
            for it in items_list:
                name = it.get('raw_name') or it.get('item')
                if not name: continue
                norm_name = name.lower().strip()
                
                # Check Item
                s_item = select(self.items.c.id).where(self.items.c.name == name)
                item_id = conn.execute(s_item).scalar()
                
                if not item_id:
                    stmt = self.items.insert().values(name=name, normalized_name=norm_name)
                    item_id = conn.execute(stmt).inserted_primary_key[0]
                
                # Insert Price
                conn.execute(self.prices.insert().values(
                    item_id=item_id,
                    source_id=source_id,
                    price_material=it.get('price_material', 0),
                    price_labor=it.get('price_labor', 0),
                    unit=it.get('unit', 'ks'),
                    quantity=it.get('quantity', 1.0)
                ))
                
            conn.commit()
            return source_id

    def search_items(self, query, limit=20):
        # Using fuzzy logic (Python side for consistency across DBs)
        # 1. Fetch Candidates (token intersection)
        q_norm = query.lower().strip()
        tokens = [t for t in q_norm.split() if len(t) > 2]
        
        with self.engine.connect() as conn:
            if not tokens:
                # Simple LIKE
                stmt = select(self.items.c.id, self.items.c.name).where(
                    self.items.c.normalized_name.ilike(f'%{q_norm}%')
                ).limit(limit)
                rows = conn.execute(stmt).fetchall()
                return [{"id": r.id, "name": r.name} for r in rows]
            
            # OR conditions
            conditions = [self.items.c.normalized_name.ilike(f'%{t}%') for t in tokens]
            stmt = select(self.items.c.id, self.items.c.name, self.items.c.normalized_name).where(
                or_(*conditions)
            )
            rows = conn.execute(stmt).fetchall()
            
            # Python Scoring
            scored = []
            for r in rows:
                item_tokens = set(r.normalized_name.split())
                query_tokens = set(tokens)
                overlap = len(item_tokens.intersection(query_tokens))
                seq = difflib.SequenceMatcher(None, q_norm, r.normalized_name).ratio()
                
                if overlap > 0:
                    score = (overlap * 2) + seq
                    scored.append((score, {"id": r.id, "name": r.name}))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:limit]]

    def get_price_history(self, item_id):
        with self.engine.connect() as conn:
            stmt = select(
                self.sources.c.date_offer, 
                self.sources.c.vendor, 
                self.prices.c.price_material, 
                self.prices.c.price_labor
            ).select_from(
                self.prices.join(self.sources, self.prices.c.source_id == self.sources.c.id)
            ).where(
                self.prices.c.item_id == item_id
            ).order_by(
                self.sources.c.date_offer.desc()
            )
            
            rows = conn.execute(stmt).fetchall()
            return [
                {
                    "date": r.date_offer, 
                    "vendor": r.vendor, 
                    "price_material": r.price_material, 
                    "price_labor": r.price_labor
                } 
                for r in rows
            ]

    # Legacy V1 search support
    def search(self, query, limit=20):
        # Similar logic to search_items but returns full details
        q_norm = query.lower().strip()
        tokens = [t for t in q_norm.split() if len(t) > 2]
        
        with self.engine.connect() as conn:
            # Join items, prices, sources
            j = self.prices.join(self.items).join(self.sources)
            base_query = select(
                self.items.c.id,
                self.items.c.name.label('item'),
                self.items.c.normalized_name,
                self.prices.c.price_material,
                self.prices.c.price_labor,
                self.prices.c.unit,
                self.sources.c.vendor.label('source'),
                self.sources.c.date_offer.label('date')
            ).select_from(j).order_by(self.sources.c.date_offer.desc())
            
            if not tokens:
                stmt = base_query.where(self.items.c.normalized_name.ilike(f'%{q_norm}%')).limit(limit)
                rows = conn.execute(stmt).fetchall()
                return [dict(r._mapping) for r in rows]
            
            conditions = [self.items.c.normalized_name.ilike(f'%{t}%') for t in tokens]
            stmt = base_query.where(or_(*conditions))
            
            rows = conn.execute(stmt).fetchall()
            
            scored = []
            seen_ids = set()
            for r in rows:
                if r.id in seen_ids: continue
                seen_ids.add(r.id)
                
                item_tokens = set(r.normalized_name.split())
                query_tokens = set(tokens)
                overlap = len(item_tokens.intersection(query_tokens))
                seq = difflib.SequenceMatcher(None, q_norm, r.normalized_name).ratio()
                
                if overlap > 0:
                    score = (overlap * 2) + seq
                    # Convert row to dict
                    d = dict(r._mapping)
                    scored.append((score, d))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:limit]]
