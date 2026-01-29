from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Date, Text
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

Base = declarative_base()

class SourceFile(Base):
    """Represents a PDF or Excel file that was processed."""
    __tablename__ = 'sources'

    id = Column(Integer, primary_key=True)
    filename = Column(String, unique=True, nullable=False)
    vendor = Column(String, nullable=True)
    date_of_offer = Column(Date, nullable=True)
    processed_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationship to PriceEntry (Source -> Entries)
    entries = relationship("PriceEntry", back_populates="source", cascade="all, delete-orphan")

class PriceItem(Base):
    """Represents a unique, normalized item (e.g., 'Sadrokarton GKB 12.5')."""
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    normalized_name = Column(String, unique=True, index=True, nullable=False)
    
    # Relationship to PriceEntry (Item -> Entries)
    entries = relationship("PriceEntry", back_populates="item")

class PriceEntry(Base):
    """Represents a specific price point found in a source file."""
    __tablename__ = 'price_entries'

    id = Column(Integer, primary_key=True)
    
    source_id = Column(Integer, ForeignKey('sources.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    
    raw_name = Column(String, nullable=False) # The name exactly as it appeared in the PDF
    price_material = Column(Float, default=0.0)
    price_labor = Column(Float, default=0.0)
    unit = Column(String, default='ks')
    quantity = Column(Float, nullable=True) # If available in the source (e.g. valid quantity)
    
    # Relationships
    source = relationship("SourceFile", back_populates="entries")
    item = relationship("PriceItem", back_populates="entries")

# Database Connection Helper
class DatabaseManager:
    def __init__(self, db_url="sqlite:///Input/04_Databaze/prices_v2.db"):
        self.engine = create_engine(db_url)
        self.Session = sessionmaker(bind=self.engine)
    
    def init_db(self):
        Base.metadata.create_all(self.engine)
        
    def get_session(self):
        return self.Session()
