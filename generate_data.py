import json
import random
import pandas as pd

# 1. Setup basic structural blocks for random generation
locations = ["Warehouse-A", "Warehouse-B", "Hub-North", "Hub-South", "Main-Store"]
categories = ["Electronics", "Apparel", "Home-Goods", "Automotive", "Office-Supplies"]
items = ["Widget", "Gadget", "Device", "Module", "Component", "Pack"]

data = []

# 2. Loop to generate 500 distinct SKUs
for i in range(1, 501):
    sku_id = f"SKU-{10000 + i}"
    name = f"{random.choice(categories)} {random.choice(items)} {random.randint(10, 99)}"
    location = random.choice(locations)
    
    # Generate system stock
    system_stock = random.randint(10, 1000)
    
    # Introduce deliberate discrepancies for roughly 15% of items
    if random.random() < 0.15:  
        # Discrepancy found! Physical stock doesn't match system stock
        physical_stock = system_stock + random.choice([-50, -10, -5, 5, 12, 25])
        # Ensure physical stock never drops below 0 due to the math
        physical_stock = max(0, physical_stock)
        status = "Discrepancy"
    else:
        # Perfectly matched inventory
        physical_stock = system_stock
        status = "Matched"
        
    # Calculate approximate monetary value per unit
    unit_value = round(random.uniform(5.0, 500.0), 2)
    total_value = round(physical_stock * unit_value, 2)

    # Build the row dictionary
    record = {
        "SKU ID": sku_id,
        "Name": name,
        "Location": location,
        "System Stock": system_stock,
        "Physical Stock": physical_stock,
        "Value": total_value,
        "Status": status
    }
    data.append(record)

# 3. Export the records directly into an organized JSON array file
with open("inventory.json", "w") as f:
    json.dump(data, f, indent=4)

print("Successfully generated inventory.json with 500 records and random anomalies!")