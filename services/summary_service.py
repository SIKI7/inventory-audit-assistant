import os
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from groq import Groq
from dotenv import load_dotenv
from services import db_service

def generate_executive_llm_summary():
    """Compiles live warehouse data state and requests a structured text report from the Groq LLM client."""
    load_dotenv()
    
    # 1. Gather all live relational database stats
    total_skus = db_service.get_total_skus()
    discrepancies = db_service.get_total_discrepancies()
    estimated_loss = db_service.get_estimated_loss()
    high_risk_items = db_service.get_high_risk_items(limit=3)
    
    # Format a clean textual snapshot of our high-risk rows for the AI's data injection
    high_risk_text = ""
    for _, row in high_risk_items.iterrows():
        high_risk_text += f"- Item: {row['sku_id']} ({row['name']}) at {row['location']} | Risk Value: ${row['value']:,}\n"
        
    # 2. Structure the data payload message for the LLM
    report_data_payload = (
        f"WAREHOUSE LIVEMETRICS SNAPSHOT:\n"
        f"- Total System SKUs Tracked: {total_skus}\n"
        f"- Active Discrepancies Found: {discrepancies}\n"
        f"- Total Estimated Capital at Risk: ${estimated_loss:,}\n\n"
        f"TOP FINANCIAL RISK EXPOSURE POINTS:\n"
        f"{high_risk_text}"
    )
    
    # 3. Establish strict report framing instructions
    system_instruction = (
        "You are a Senior Corporate Supply Chain Auditor.\n"
        "Your task is to take the provided raw warehouse metrics snapshot and convert it into a highly professional Executive Audit Summary Report.\n"
        "Your output must follow this clean structure:\n"
        "### 📑 EXECUTIVE SUMMARY REPORT\n"
        "**1. Operational Overview**: Briefly summarize the scope.\n"
        "**2. Critical Risk Exposure**: Highlight the total loss metrics and what they mean.\n"
        "**3. Strategic Recommendations**: Provide 3 clear, action-oriented structural steps to mitigate these losses.\n\n"
        "Keep your tone formal, analytical, authoritative, and direct. Do not add casual filler language."
    )
    
    # 4. Fire the pipeline block to Groq API
    try:
        groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
        response = groq_client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": report_data_payload}
            ],
            temperature=0.2
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"❌ Failed to compile AI Executive Report: {e}"

# --- TEST RUNNER ---
if __name__ == "__main__":
    print("🧪 Testing Summary Reporting Engine Compilation...\n")
    report_preview = generate_executive_llm_summary()
    print(report_preview)
    print("\n✅ Report generator service layer test complete!")