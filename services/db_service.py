import os
import sqlite3
import pandas as pd

# Define the absolute or relative path to your database file
# Since 'inventory.db' sits at the root level, we point up one folder level if run inside services/
DB_PATH = "inventory.db"

def get_db_connection():
    """Helper function to open a clean connection to SQLite."""
    # Check if the database exists at the root path first
    if os.path.exists(DB_PATH):
        return sqlite3.connect(DB_PATH)
    else:
        # Fallback for when running the test directly from inside the services folder
        return sqlite3.connect("../inventory.db")

def get_all_inventory():
    """Fetches all 500 rows from the inventory table as a Pandas DataFrame."""
    conn = get_db_connection()
    df = pd.read_sql_query("SELECT * FROM inventory", conn)
    conn.close()
    return df

def get_total_skus():
    """Returns the total number of unique SKUs tracked in the warehouse."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def get_total_discrepancies():
    """Counts how many items have a flagged discrepancy status."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM inventory WHERE status = 'Discrepancy'")
    total = cursor.fetchone()[0]
    conn.close()
    return total

def get_estimated_loss():
    """Calculates total financial value tied up in discrepancy anomalies."""
    conn = get_db_connection()
    cursor = conn.cursor()
    # Sum up the value of rows marked as discrepancies
    cursor.execute("SELECT SUM(value) FROM inventory WHERE status = 'Discrepancy'")
    loss = cursor.fetchone()[0]
    conn.close()
    return round(loss or 0.0, 2)

def get_high_risk_items(limit=5):
    """Retrieves the top highest-valued inventory items marked with discrepancies."""
    conn = get_db_connection()
    df = pd.read_sql_query(
        "SELECT sku_id, name, location, value, status FROM inventory "
        "WHERE status = 'Discrepancy' "
        "ORDER BY value DESC LIMIT ?", 
        conn, 
        params=[limit]
    )
    conn.close()
    return df

# --- TEST BLOCK RUNNER ---
if __name__ == "__main__":
    print("🧪 Running Database Service Health Verification Check...\n")
    try:
        skus = get_total_skus()
        discrepancies = get_total_discrepancies()
        loss = get_estimated_loss()
        high_risk = get_high_risk_items(3)
        
        print(f"📊 Total Skus Tracked: {skus}")
        print(f"⚠️ Total Flagged Discrepancies: {discrepancies}")
        print(f"💰 Total Financial Value at Risk: ${loss:,}")
        print("\n🔥 Top 3 High-Risk Items Sample:")
        print(high_risk.to_string(index=False))
        print("\n✅ Database Service layer is working perfectly!")
        
    except Exception as e:
        print(f"❌ Error verifying database service layer: {e}")