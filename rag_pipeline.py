import os
import chromadb
from chromadb.utils import embedding_functions
from groq import Groq
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    # 1. Connect to the local ChromaDB storage
    chroma_client = chromadb.PersistentClient(path="./chroma_data")
    default_ef = embedding_functions.DefaultEmbeddingFunction()
    
    try:
        collection = chroma_client.get_collection(
            name="inventory_audits", 
            embedding_function=default_ef
        )
    except Exception as e:
        print(f"❌ Could not find ChromaDB collection. Did you run build_vector_db.py? Error: {e}")
        return

    # 2. Initialize the Groq AI Engine Client
    groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    
    # 3. Read system prompt guardrails
    prompt_path = os.path.join("prompts", "system_prompt.txt")
    if os.path.exists(prompt_path):
        with open(prompt_path, "r") as f:
            system_instruction = f.read()
    else:
        system_instruction = "You are a professional warehouse audit assistant."

    print("🤖 Audit-GPT RAG Engine Client Terminal Session Init.")
    print("Type 'exit' or 'quit' to close the pipeline session.\n")
    
    # Start the testing loop
    while True:
        user_question = input("👤 Ask a question: ")
        if user_question.lower() in ['exit', 'quit']:
            print("👋 Closing terminal RAG testing session.")
            break
            
        if not user_question.strip():
            continue
            
        try:
            # Semantic search query against ChromaDB
            results = collection.query(query_texts=[user_question], n_results=3)
            retrieved_context = "\n".join(results['documents'][0])
            
            # Combine local context data with user query
            user_prompt = f"Context:\n{retrieved_context}\n\nQuestion: {user_question}"
            
            # Request response generation from Llama 3
            response = groq_client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1
            )
            
            print(f"\n🤖 Audit-GPT:\n{response.choices[0].message.content}\n")
            print("-" * 50)
            
        except Exception as e:
            print(f"❌ An error occurred during processing: {e}\n")

if __name__ == "__main__":
    main()