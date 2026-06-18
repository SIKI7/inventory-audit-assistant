import pandas as pd
import chromadb
from chromadb.utils import embedding_functions

def build_vector_database():
    # 1. Load the discrepancies spreadsheet we generated in Step 7
    try:
        df = pd.read_csv("audit_discrepancies.csv")
    except FileNotFoundError:
        print("❌ Error: 'audit_discrepancies.csv' not found. Please run the discrepancy engine first!")
        return

    print(f"📖 Loaded {len(df)} discrepancies. Generating mock audit notes...")

    # 2. Add some realistic sample text notes to simulate what auditors write
    mock_notes = [
        "Damaged item found behind the pallet during physical count.",
        "Water leakage from the ceiling damaged the outer packaging.",
        "Item likely misplaced in another aisle during weekend re-stocking.",
        "Barcode scanner error during inbound receiving caused a discrepancy.",
        "Product expired; removed from active shelf space but not updated in system.",
        "Inventory count mismatch; potential counting error by the night shift."
    ]
    
    # Assign random text notes to our data rows for demonstration purposes
    import random
    random.seed(42)  # Keeps it consistent
    df['Audit Notes'] = [random.choice(mock_notes) for _ in range(len(df))]

    # 3. Initialize the local ChromaDB client
    # This creates a folder named 'chroma_data' to store the vectors locally
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    
    # Use ChromaDB's default built-in sentence-transformer embedding model
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    
    # Create or fetch a collection named 'inventory_audits'
    collection = chroma_client.get_or_create_collection(
        name="inventory_audits", 
        embedding_function=default_ef
    )

    print("🤖 Generating embeddings and seeding ChromaDB (this may take a moment)...")

    # 4. Prepare data arrays for bulk insertion into ChromaDB
    documents = []
    metadatas = []
    ids = []

    for index, row in df.iterrows():
        # Combine the fields into a rich descriptive sentence for the AI to read
        combined_text = (
            f"SKU ID: {row['sku_id']} | Name: {row['name']} | "
            f"Location: {row['location']} | Discrepancy Type: {row['Discrepancy Type']} | "
            f"Auditor Notes: {row['Audit Notes']}"
        )
        
        documents.append(combined_text)
        ids.append(f"id_{row['sku_id']}")
        
        # Metadata allows you to filter search results later by fields
        metadatas.append({
            "sku_id": str(row['sku_id']),
            "location": str(row['location']),
            "discrepancy_type": str(row['Discrepancy Type'])
        })

    # 5. Insert data into the vector database
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
    )

    print("💾 ChromaDB built and vectors saved successfully inside './chroma_data'!")
    
    # 6. Let's run a quick semantic test query to prove it works!
    print("\n🔍 Testing Semantic Search: Querying for 'damaged packaging due to water'...")
    results = collection.query(
        query_texts=["damaged packaging due to water"],
        n_results=2
    )
    
    print("\n💡 Closest Matches Found by AI Context Match:")
    for doc in results['documents'][0]:
        print(f"👉 {doc}\n")

if __name__ == "__main__":
    build_vector_database()