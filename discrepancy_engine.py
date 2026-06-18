import pandas as pd
from sqlalchemy import create_engine

def run_discrepancy_engine():
    # 1. Connect to our SQLite database
    DATABASE_URL = "sqlite:///inventory.db"
    engine = create_engine(DATABASE_URL)
    
    # 2. Load the inventory data directly into a Pandas DataFrame
    print("🤖 Fetching inventory data from SQLite...")
    df = pd.read_sql_table('inventory', con=engine)
    
    # Filter out only the records flagged as having a Discrepancy
    discrepancies = df[df['status'] == 'Discrepancy'].copy()
    print(f"🔍 Found {len(discrepancies)} items marked with discrepancies. Analyzing root causes...\n")
    
    # 3. Define categorization rules based on stock variance
    # Variance = Physical Stock - System Stock
    discrepancies['Variance'] = discrepancies['physical_stock'] - discrepancies['system_stock']
    
    def categorize_error(row):
        variance = row['Variance']
        phys = row['physical_stock']
        sys = row['system_stock']
        
        # Rule A: Phantom Inventory (System shows stock, but physically there is absolutely zero)
        if sys > 0 and phys == 0:
            return "Phantom Inventory (System ghost data)"
        
        # Rule B: Shrinkage / Missing (Physical stock is lower than system stock)
        elif variance < 0:
            # For a small demo nuance: if it's missing exactly a large round number, it might be a location error
            if variance in [-50, -10]:
                return "Location Error (Likely misplaced in another aisle)"
            return "Shrinkage (Theft, Unaccounted Damage, or Expiry)"
            
        # Rule C: Surplus / Overages (Physical stock is higher than system stock)
        elif variance > 0:
            return "Overage (Unscanned receiving or mislabeled SKU)"
            
        return "Unclassified Mismatch"

    # 4. Apply our engine rules to categorize each discrepancy
    discrepancies['Discrepancy Type'] = discrepancies.apply(categorize_error, axis=1)
    
    # 5. Output a summary report to the console
    print("=" * 60)
    print("               INVENTORY AUDIT REPORT                 ")
    print("=" * 60)
    
    summary = discrepancies['Discrepancy Type'].value_counts()
    for error_type, count in summary.items():
        print(f"📍 {error_type}: {count} SKUs affected")
        
    print("-" * 60)
    
    # 6. Show a sneak peek of the flagged items
    print("\n📋 Top 5 Flagged Items Sample:")
    sample_cols = ['sku_id', 'name', 'system_stock', 'physical_stock', 'Variance', 'Discrepancy Type']
    print(discrepancies[sample_cols].head().to_string(index=False))
    
    # 7. Save the analysis to a new CSV file for your upcoming UI or API steps
    discrepancies.to_csv("audit_discrepancies.csv", index=False)
    print("\n💾 Detailed report saved automatically to 'audit_discrepancies.csv'!")

if __name__ == "__main__":
    run_discrepancy_engine()