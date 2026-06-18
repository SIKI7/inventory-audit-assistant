import json
from sqlalchemy import create_engine, Column, Integer, String, Float
from sqlalchemy.orm import declarative_base, sessionmaker

# 1. Initialize SQLAlchemy and setup the SQLite database file connection
DATABASE_URL = "sqlite:///inventory.db"
engine = create_engine(DATABASE_URL, echo=True) # echo=True prints out the raw SQL statements being run
Base = declarative_base()

# 2. Define the Inventory table structure (Schema)
class InventoryItem(Base):
    __tablename__ = 'inventory'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    sku_id = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    location = Column(String(100), nullable=False)
    system_stock = Column(Integer, nullable=False)
    physical_stock = Column(Integer, nullable=False)
    value = Column(Float, nullable=False)
    status = Column(String(50), nullable=False)

# 3. Physically create the table structure inside the SQLite database file
print("Creating database table...")
Base.metadata.create_all(engine)

# 4. Open the inventory.json file and load the generated records
print("Loading records from inventory.json...")
with open("inventory.json", "r") as f:
    json_records = json.load(f)

# 5. Open a transactional database session to insert the records
Session = sessionmaker(bind=engine)
session = Session()

try:
    print(f"Migrating {len(json_records)} records to SQLite...")
    for item in json_records:
        # Convert JSON keys to match our SQLAlchemy database Column names
        db_item = InventoryItem(
            sku_id=item["SKU ID"],
            name=item["Name"],
            location=item["Location"],
            system_stock=item["System Stock"],
            physical_stock=item["Physical Stock"],
            value=item["Value"],
            status=item["Status"]
        )
        session.add(db_item)
    
    # Commit the changes to finalize the insertions
    session.commit()
    print("Database built and seeded successfully!")

except Exception as e:
    print(f"An error occurred during migration: {e}")
    session.rollback()

finally:
    session.close()