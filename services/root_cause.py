import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import db_service

def analyze_discrepancy_root_causes():
    """Applies systemic business logic rules to evaluate the root cause of each inventory anomaly."""
    df = db_service.get_all_inventory()
    
    # Isolate rows that are marked as anomalies
    discrepancy_rows = df[df['status'] == 'Discrepancy'].copy()
    
    analysis_results = []
    
    for index, row in discrepancy_rows.iterrows():
        sys_stock = row['system_stock']
        phys_stock = row['physical_stock']
        
        # Calculate numeric variance metrics
        absolute_variance = abs(sys_stock - phys_stock)
        variance_percentage = (absolute_variance / sys_stock) * 100 if sys_stock > 0 else 0
        
        # Apply deterministic rule logic hierarchy
        if phys_stock == 0 and sys_stock > 0:
            cause = "Phantom Inventory (System reflects stock that physically does not exist)"
            action = "Reconcile system logs to 0; initiate shrinkage investigation."
        elif variance_percentage > 20:
            cause = "Receiving Error (Large discrepancy points to batch logging mistakes during intake)"
            action = "Audit inbound shipment invoices and receiving logs for this batch."
        elif variance_percentage < 10:
            cause = "Counting Error (Minor difference typically caused by manual human miscounts)"
            action = "Schedule a standard cycle recount to verify physical inventory."
        else:
            cause = "Misplacement / Internal Transfer Error"
            action = "Search adjacent warehouse storage racks and check unposted transfer notes."
            
        analysis_results.append({
            "sku_id": row['sku_id'],
            "name": row['name'],
            "location": row['location'],
            "variance_pct": round(variance_percentage, 1),
            "root_cause": cause,
            "recommended_action": action
        })
        
    return pd.DataFrame(analysis_results)

# --- TEST RUNNER ---
if __name__ == "__main__":
    print("🧪 Running Root Cause Analysis Engine Verification...\n")
    try:
        results_df = analyze_discrepancy_root_causes()
        print(f"📋 Analyzed {len(results_df)} anomalies.")
        print("-" * 70)
        print("💡 Sample Root Cause Diagnosis Output:")
        print(results_df[['sku_id', 'variance_pct', 'root_cause']].head(4).to_string(index=False))
        print("-" * 70)
        print("✅ Root Cause Analysis service layer testing complete!")
    except Exception as e:
        print(f"❌ Error during diagnostic execution: {e}")