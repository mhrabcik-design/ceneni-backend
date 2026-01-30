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

    def delete_item(self, item_id):
        """Delete an item and all its prices (blacklist functionality)."""
        with self.engine.connect() as conn:
            # Check if item exists
            check = conn.execute(select(self.items.c.id).where(self.items.c.id == item_id)).scalar()
            if not check:
                return False
            
            # Delete prices first (foreign key)
            conn.execute(self.prices.delete().where(self.prices.c.item_id == item_id))
            # Delete item
            conn.execute(self.items.delete().where(self.items.c.id == item_id))
            conn.commit()
            return True

    def add_custom_item(self, name, price_material, price_labor, unit):
        """Add a user-defined item with custom price."""
        with self.engine.connect() as conn:
            norm_name = name.lower().strip()
            
            # Check if item already exists
            existing = conn.execute(select(self.items.c.id).where(self.items.c.name == name)).scalar()
            if existing:
                item_id = existing
            else:
                # Create new item
                result = conn.execute(self.items.insert().values(name=name, normalized_name=norm_name))
                item_id = result.inserted_primary_key[0]
            
            # Get or create "User Input" source
            source_name = "user_input"
            source_id = conn.execute(select(self.sources.c.id).where(self.sources.c.filename == source_name)).scalar()
            if not source_id:
                from datetime import date
                result = conn.execute(self.sources.insert().values(
                    filename=source_name,
                    vendor="Uživatel",
                    date_offer=date.today()
                ))
                source_id = result.inserted_primary_key[0]
            
            # Add price
            conn.execute(self.prices.insert().values(
                item_id=item_id,
                source_id=source_id,
                price_material=price_material,
                price_labor=price_labor,
                unit=unit,
                quantity=1.0
            ))
            conn.commit()
            return item_id

    def add_processed_file(self, filename, vendor, date_offer, items):
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
            for it in items:
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

    def get_item_details(self, item_id):
        """Get full details for an item including name, all sources, and price history."""
        with self.engine.connect() as conn:
            # Get item name
            item_stmt = select(self.items.c.name).where(self.items.c.id == item_id)
            item_row = conn.execute(item_stmt).fetchone()
            if not item_row:
                return None
            
            # Get all price records from different sources
            sources_stmt = select(
                self.sources.c.vendor,
                self.sources.c.date_offer,
                self.prices.c.price_material,
                self.prices.c.price_labor,
                self.prices.c.unit
            ).select_from(
                self.prices.join(self.sources, self.prices.c.source_id == self.sources.c.id)
            ).where(
                self.prices.c.item_id == item_id
            ).order_by(
                self.sources.c.date_offer.desc()
            )
            
            sources_rows = conn.execute(sources_stmt).fetchall()
            
            sources = [
                {
                    "vendor": r.vendor,
                    "date": str(r.date_offer) if r.date_offer else None,
                    "price_material": r.price_material,
                    "price_labor": r.price_labor,
                    "unit": r.unit
                }
                for r in sources_rows
            ]
            
            # Build price history (unique dates with averaged prices)
            price_history = []
            seen_dates = set()
            for s in sources:
                if s['date'] and s['date'] not in seen_dates:
                    seen_dates.add(s['date'])
                    price_history.append({
                        "date": s['date'],
                        "price_material": s['price_material'],
                        "price_labor": s['price_labor']
                    })
            
            return {
                "name": item_row.name,
                "sources": sources,
                "price_history": price_history
            }

    def get_all_items_admin(self):
        """Fetch all items with their latest prices for administrative editing."""
        with self.engine.connect() as conn:
            # We want the most recent price for each item
            # Subquery to get latest price id per item
            latest_price_sub = select(
                self.prices.c.item_id,
                func.max(self.prices.c.id).label('latest_id')
            ).group_by(self.prices.c.item_id).subquery()

            stmt = select(
                self.items.c.id,
                self.items.c.name,
                self.prices.c.price_material,
                self.prices.c.price_labor,
                self.prices.c.unit,
                self.sources.c.vendor,
                self.sources.c.date_offer
            ).select_from(
                self.items
                .outerjoin(latest_price_sub, self.items.c.id == latest_price_sub.c.item_id)
                .outerjoin(self.prices, latest_price_sub.c.latest_id == self.prices.c.id)
                .outerjoin(self.sources, self.prices.c.source_id == self.sources.c.id)
            ).order_by(self.items.c.name)

            rows = conn.execute(stmt).fetchall()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "price_material": r.price_material or 0,
                    "price_labor": r.price_labor or 0,
                    "unit": r.unit or "ks",
                    "source": r.vendor or "N/A",
                    "date": str(r.date_offer) if r.date_offer else "N/A"
                }
                for r in rows
            ]

    def sync_admin_items(self, items_data):
        """Bulk sync items and prices from admin sheet data."""
        with self.engine.connect() as conn:
            # Get user source
            source_name = "user_input"
            source_id = conn.execute(select(self.sources.c.id).where(self.sources.c.filename == source_name)).scalar()
            if not source_id:
                from datetime import date
                result = conn.execute(self.sources.insert().values(
                    filename=source_name,
                    vendor="Uživatel (Změna)",
                    date_offer=date.today()
                ))
                source_id = result.inserted_primary_key[0]

            for it in items_data:
                item_id = it.get('id')
                name = it.get('name')
                price_mat = float(it.get('price_material', 0))
                price_lab = float(it.get('price_labor', 0))
                unit = it.get('unit', 'ks')

                if not name: continue

                if item_id:
                    # Update Item Name
                    conn.execute(self.items.update().where(self.items.c.id == item_id).values(
                        name=name, normalized_name=name.lower().strip()
                    ))
                    
                    # Update/Add Price
                    # To keep history, we always insert a new record IF prices changed
                    # Or just update if it's from user_input source
                    existing_latest = conn.execute(
                        select(self.prices.c.price_material, self.prices.c.price_labor, self.prices.c.unit)
                        .where(self.prices.c.item_id == item_id)
                        .order_by(self.prices.c.id.desc())
                        .limit(1)
                    ).fetchone()

                    if not existing_latest or (
                        existing_latest.price_material != price_mat or 
                        existing_latest.price_labor != price_lab or 
                        existing_latest.unit != unit
                    ):
                        conn.execute(self.prices.insert().values(
                            item_id=item_id,
                            source_id=source_id,
                            price_material=price_mat,
                            price_labor=price_lab,
                            unit=unit,
                            quantity=1.0
                        ))
                else:
                    # New Item? (Usually admin won't create items without ID, but for robustness)
                    self.add_custom_item(name, price_mat, price_lab, unit)
            
            conn.commit()
            return True

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
                    # Convert row to dict and add match_score
                    d = dict(r._mapping)
                    d['match_score'] = round(seq, 2)  # 0-1 similarity ratio
                    scored.append((score, d))
            
            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:limit]]
