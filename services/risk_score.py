import pandas as pd
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from services import db_service

def calculate_inventory_risk_scores():
    """Evaluates multi-factor data streams to assign a normalized risk index (0-100) to every discrepancy."""
    df = db_service.get_all_inventory()
    
    # Isolate active discrepancies to evaluate
    discrepancy_rows = df[df['status'] == 'Discrepancy'].copy()
    
    risk_results = []
    
    for index, row in discrepancy_rows.iterrows():
        sys_stock = row['system_stock']
        phys_stock = row['physical_stock']
        item_value = row['value']
        
        # Factor 1: Variance Percentage Weight (capped contribution to max out at 40 points)
        abs_variance = abs(sys_stock - phys_stock)
        variance_pct = (abs_variance / sys_stock) * 100 if sys_stock > 0 else 0
        variance_score = min((variance_pct / 100) * 40, 40)
        
        # Factor 2: Financial Value Weight (capped contribution to max out at 45 points)
        # Assuming our highest items sit near $50,000
        value_score = min((item_value / 50000) * 45, 45)
        
        # Factor 3: Historical Repeat Incidents Weight (contribution up to 15 points)
        # Simulating recurring problem tracking flags based on item indexing numbers
        historical_incidents = 3 if int(row['sku_id'].split('-')[1]) % 3 == 0 else 1
        incident_score = 15 if historical_incidents > 2 else 5
        
        # Sum total scores and cap at 100
        final_risk_score = min(int(variance_score + value_score + incident_score), 100)
        
        risk_results.append({
            "sku_id": row['sku_id'],
            "name": row['name'],
            "location": row['location'],
            "value": item_value,
            "variance_pct": round(variance_pct, 1),
            "risk_score": final_risk_score
        })
        
    # Compile and sort with highest risk factors first
    risk_df = pd.DataFrame(risk_results)
    if not risk_df.empty:
        return risk_df.sort_values(by="risk_score", ascending=False).reset_index(drop=True)
    return risk_df

# --- TEST RUNNER ---
if __name__ == "__main__":
    print("🧪 Testing Inventory Risk Scoring Matrix Execution...\n")
    try:
        scored_df = calculate_inventory_risk_scores()
        print(f"🎯 Successfully evaluated risk parameters across {len(scored_df)} anomalies.")
        print("-" * 75)
        print("🔥 HIGHEST OPERATIONAL RISK MATRIX EXPOSURE POINTS:")
        print(scored_df[['sku_id', 'variance_pct', 'value', 'risk_score']].head(5).to_string(index=False))
        print("-" * 75)
        print("✅ Risk Engine module testing complete!")
    except Exception as e:
        print(f"❌ Critical error executing risk analysis: {e}")