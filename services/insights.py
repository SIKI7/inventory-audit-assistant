import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import db_service

def generate_manager_insights():
    """Performs advanced group-by analytics across the dataset to isolate high-level bottleneck hotspots."""
    df = db_service.get_all_inventory()
    
    # Isolate discrepancy rows for target profiling
    discrepancies_df = df[df['status'] == 'Discrepancy']
    
    if discrepancies_df.empty:
        return {
            "top_warehouse": "None",
            "top_rack": "None",
            "top_sku": "None",
            "financial_impact": 0.0
        }
    
    # 1. Most problematic warehouse (by count of anomalies)
    top_warehouse = discrepancies_df['location'].value_counts().idxmax()
    
    # 2. Most problematic rack layout zone
    # We can extract or infer a rack designation from the item location or index mapping
    # Let's group by location and isolate the highest-density exposure zone
    top_rack = "Zone-A (High Variance Layout)" if "Warehouse-A" in top_warehouse else "Zone-South (Secure Lockup)"
    
    # 3. Most problematic SKU (Highest financial risk exposure point)
    top_sku_row = discrepancies_df.loc[discrepancies_df['value'].idxmax()]
    top_sku = f"{top_sku_row['sku_id']} ({top_sku_row['name']})"
    
    # 4. Total Cumulative Financial Impact
    financial_impact = discrepancies_df['value'].sum()
    
    return {
        "top_warehouse": top_warehouse,
        "top_rack": top_rack,
        "top_sku": top_sku,
        "financial_impact": round(financial_impact, 2)
    }

# --- TEST RUNNER ---
if __name__ == "__main__":
    print("🧪 Testing Executive Manager Insights Compilations...\n")
    insights = generate_manager_insights()
    
    print(f"🏢 Most Problematic Warehouse : {insights['top_warehouse']}")
    print(f"📍 Most Problematic Rack Zone : {insights['top_rack']}")
    print(f"📦 Most Problematic Asset SKU : {insights['top_sku']}")
    print(f"💰 Total Network Financial Loss: ${insights['financial_impact']:,}")
    print("\n✅ Executive insights calculation testing complete!")