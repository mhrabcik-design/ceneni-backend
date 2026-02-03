import os
import difflib
import re
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
            Column('filename', String),
            Column('vendor', String),
            Column('date_offer', Date),
            Column('offer_number', String),
            Column('file_hash', String, unique=True),
            Column('source_type', String, server_default='SUPPLIER'), # 'SUPPLIER', 'INTERNAL', 'ADMIN'
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
        self._migrate_schema()

    def _migrate_schema(self):
        """Internal helper to ensure column upgrades."""
        with self.engine.connect() as conn:
            try:
                # Check for source_type column using information_schema for more reliability (Postgres)
                if "postgresql" in str(self.engine.url):
                    check_sql = text("SELECT 1 FROM information_schema.columns WHERE table_name='sources' AND column_name='source_type'")
                    exists = conn.execute(check_sql).fetchone()
                    if exists: return
                else:
                    # Generic check for SQLite/others
                    conn.execute(text("SELECT source_type FROM sources LIMIT 1"))
                    return
            except Exception:
                pass

        # If we reach here, column is missing
        print("⚠️ Migrating database: Adding source_type column to sources...")
        try:
            with self.engine.begin() as trans_conn:
                trans_conn.execute(text("ALTER TABLE sources ADD COLUMN source_type VARCHAR DEFAULT 'SUPPLIER'"))
            print("✅ Migration successful.")
        except Exception as e:
            print(f"❌ Migration failed: {e}")

    def get_stats(self):
        with self.engine.connect() as conn:
            try:
                ic = conn.execute(text("SELECT COUNT(*) FROM items")).scalar()
                pc = conn.execute(text("SELECT COUNT(*) FROM prices")).scalar()
                return {"items": ic, "prices": pc, "url": str(self.engine.url)}
            except Exception as e:
                return {"items": 0, "prices": 0, "url": str(self.engine.url), "error": str(e)}

    def reset_all_data(self):
        """Drops all tables and recreates them. Use with caution!"""
        self.metadata.drop_all(self.engine)
        self.metadata.create_all(self.engine)
        return True

    def delete_item(self, item_id):
        return self.delete_items([item_id])

    def delete_items(self, item_ids):
        """Delete multiple items and their prices."""
        if not item_ids: return False
        with self.engine.connect() as conn:
            # Delete prices first
            conn.execute(self.prices.delete().where(self.prices.c.item_id.in_(item_ids)))
            # Delete items
            conn.execute(self.items.delete().where(self.items.c.id.in_(item_ids)))
            conn.commit()
            return True

    def delete_source(self, source_id):
        """Delete a source and all prices linked to it."""
        with self.engine.connect() as conn:
            # Delete prices first (Foreign Key)
            conn.execute(self.prices.delete().where(self.prices.c.source_id == source_id))
            # Delete source
            conn.execute(self.sources.delete().where(self.sources.c.id == source_id))
            conn.commit()
            return True

    def add_custom_item(self, name, price_material, price_labor, unit):
        """Add a user-defined item with custom price."""
        with self.engine.connect() as conn:
            name = self._clean_item_name(name)
            norm_name = name.lower().strip()
            
            # Determine source_type based on which prices are filled (Iron Curtain logic)
            if price_material > 0 and price_labor == 0:
                source_type = 'SUPPLIER'  # Material only -> treated as supplier data
            elif price_labor > 0 and price_material == 0:
                source_type = 'INTERNAL'  # Labor only -> treated as internal budget
            else:
                source_type = 'ADMIN'  # Both or neither -> admin entry
            
            # Check if item already exists
            existing = conn.execute(select(self.items.c.id).where(self.items.c.name == name)).scalar()
            if existing:
                item_id = existing
            else:
                # Create new item
                result = conn.execute(self.items.insert().values(name=name, normalized_name=norm_name))
                item_id = result.inserted_primary_key[0]
            
            # Get or create source with appropriate type
            source_name = f"user_input_{source_type.lower()}"
            source_id = conn.execute(select(self.sources.c.id).where(self.sources.c.filename == source_name)).scalar()
            if not source_id:
                from datetime import date
                result = conn.execute(self.sources.insert().values(
                    filename=source_name,
                    vendor="Uživatel",
                    date_offer=date.today(),
                    source_type=source_type
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

    def check_file_exists(self, file_hash=None, offer_number=None):
        """Check if a file with same hash or offer number exists."""
        with self.engine.connect() as conn:
            if file_hash:
                s = select(self.sources.c.id, self.sources.c.filename, self.sources.c.vendor).where(self.sources.c.file_hash == file_hash)
                row = conn.execute(s).fetchone()
                if row: return {"type": "hash", "filename": row.filename, "vendor": row.vendor, "id": row.id}
            
            if offer_number:
                s = select(self.sources.c.id, self.sources.c.filename, self.sources.c.vendor).where(self.sources.c.offer_number == offer_number)
                row = conn.execute(s).fetchone()
                if row: return {"type": "offer", "filename": row.filename, "vendor": row.vendor, "id": row.id}
        return None

    def add_processed_file(self, filename, vendor, date_offer, items, file_hash=None, offer_number=None, source_type='SUPPLIER'):
        with self.engine.connect() as conn:
            # 1. Add/Get Source
            # Check existence by hash/offer if provided, else filename
            if file_hash:
                s = select(self.sources.c.id).where(self.sources.c.file_hash == file_hash)
            elif offer_number:
                s = select(self.sources.c.id).where(self.sources.c.offer_number == offer_number)
            else:
                s = select(self.sources.c.id).where(self.sources.c.filename == filename)
            
            source_id = conn.execute(s).scalar()
            
            if not source_id:
                stmt = self.sources.insert().values(
                    filename=filename, 
                    vendor=vendor, 
                    date_offer=date_offer,
                    file_hash=file_hash,
                    offer_number=offer_number,
                    source_type=source_type
                )
                result = conn.execute(stmt)
                source_id = result.inserted_primary_key[0]
            else:
                # Update existing source metadata
                stmt = self.sources.update().where(self.sources.c.id == source_id).values(
                    vendor=vendor, 
                    date_offer=date_offer,
                    offer_number=offer_number,
                    source_type=source_type
                )
                conn.execute(stmt)
                
            # 2. Add Items & Prices
            # Prepare data
            for it in items:
                raw_extracted_name = it.get('raw_name') or it.get('item')
                if not raw_extracted_name: continue
                
                name = self._clean_item_name(raw_extracted_name)
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
                self.prices.c.price_labor,
                self.sources.c.source_type
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
                    "price_labor": r.price_labor,
                    "source_type": r.source_type
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

    def get_labor_items(self):
        """Fetch all unique items that have a labor price (to be used for suggestions)."""
        with self.engine.connect() as conn:
            # We want items where price_labor > 0, getting latest price info
            latest_price_sub = select(
                self.prices.c.item_id,
                func.max(self.prices.c.id).label('latest_id')
            ).where(self.prices.c.price_labor > 0).group_by(self.prices.c.item_id).subquery()

            stmt = select(
                self.items.c.id,
                self.items.c.name,
                self.prices.c.price_labor,
                self.prices.c.unit
            ).select_from(
                self.items
                .join(latest_price_sub, self.items.c.id == latest_price_sub.c.item_id)
                .join(self.prices, latest_price_sub.c.latest_id == self.prices.c.id)
            ).order_by(self.items.c.name)

            rows = conn.execute(stmt).fetchall()
            return [
                {
                    "id": r.id,
                    "name": r.name,
                    "price_labor": r.price_labor,
                    "unit": r.unit
                }
                for r in rows
            ]

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

            changes_count = 0
            for it in items_data:
                item_id = it.get('id')
                name = it.get('name')
                price_mat = float(it.get('price_material', 0) or 0)
                price_lab = float(it.get('price_labor', 0) or 0)
                unit = it.get('unit', 'ks')

                if not name: continue

                if item_id:
                    # Update Item Name
                    name = self._clean_item_name(name)
                    conn.execute(self.items.update().where(self.items.c.id == item_id).values(
                        name=name, normalized_name=name.lower().strip()
                    ))
                    
                    # Check if prices actually changed (with tolerance for floats)
                    existing_latest = conn.execute(
                        select(self.prices.c.price_material, self.prices.c.price_labor, self.prices.c.unit)
                        .where(self.prices.c.item_id == item_id)
                        .order_by(self.prices.c.id.desc())
                        .limit(1)
                    ).fetchone()

                    # Compare with tolerance (0.01) to avoid float precision issues
                    def floats_equal(a, b, tol=0.01):
                        return abs((a or 0) - (b or 0)) < tol

                    if not existing_latest or (
                        not floats_equal(existing_latest.price_material, price_mat) or 
                        not floats_equal(existing_latest.price_labor, price_lab) or 
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
                        changes_count += 1
                else:
                    # New Item
                    self.add_custom_item(name, price_mat, price_lab, unit)
                    changes_count += 1
            
            conn.commit()
            return changes_count

    # Legacy V1 search support
    def search(self, query, limit=20, source_type_filter=None):
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
            
            if source_type_filter:
                base_query = base_query.where(self.sources.c.source_type.in_(source_type_filter))
            
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

    def _clean_item_name(self, name):
        """
        Cleans up common noise from PDF/Excel extractions:
        - Removes line breaks, tabs, excessive spaces
        - Removes sequential IDs (1., a), 10., etc.)
        - Removes bullet points
        """
        if not name: return ""
        
        # 1. Remove line breaks and tabs
        name = name.replace('\n', ' ').replace('\r', ' ').replace('\t', ' ')
        
        # 2. Remove sequential IDs at the beginning
        # Pattern A: "1. ", "1.1. ", "a) ", "10) " - with dot or bracket
        name = re.sub(r'^\s*[0-9a-zA-Z]+(\.[0-9a-zA-Z]+)*[.\)]\s*', '', name)
        # Pattern B: "29 ", "100 " - bare number followed by space at start (common in supplier offers)
        name = re.sub(r'^\s*\d{1,3}\s+', '', name)
        
        # 3. Remove bullet points
        name = re.sub(r'^\s*[•\-\*]\s*', '', name)
        
        # 4. Remove excessive spaces
        name = re.sub(r'\s+', ' ', name).strip()
        
        return name
