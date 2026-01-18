import os
import json
from modules.github_loader import load_docs
from modules.vectorizer import DocumentVectorizer

def run_brain_surgery():
    print("="*50)
    print("🧠 SELLICA BRAIN BUILDER: GITHUB -> VECTOR")
    print("="*50)

    # 1. Config
    shop_name = "Techwear_shop"  # Your repo name
    data_dir = "./data"
    output_file = os.path.join(data_dir, "vectors.jsonl")

    # 2. Safety First: Make sure 'data' folder exists
    if not os.path.exists(data_dir):
        print(f"[System] Creating {data_dir} directory...")
        os.makedirs(data_dir)

    # 3. Pull from GitHub
    print(f"\n[Step 1/2] Connecting to GitHub: '{shop_name}'...")
    try:
        # This uses your github_loader.py module
        documents = load_docs(shop_name)
        
        if not documents:
            print("❌ Error: No files found in that repo. Check the name!")
            return
            
        print(f"✅ Successfully pulled {len(documents)} documents.")
    except Exception as e:
        print(f"❌ GitHub Pull Failed: {e}")
        return

    # 4. Vectorize and Save
    print(f"\n[Step 2/2] Running Vectorizer (Encoding text to math)...")
    try:
        # This uses your vectorizer.py module
        vectorizer = DocumentVectorizer()
        
        # This will process the docs and save them directly to vectors.jsonl
        vectorized_data = vectorizer.vectorize_documents(
            documents, 
            output_path=output_file
        )
        
        print(f"\n✅ SUCCESS! Brain baked and saved to: {output_file}")
        print(f"Total entries in memory: {len(vectorized_data)}")
        
    except Exception as e:
        print(f"❌ Vectorization Failed: {e}")
        return

    print("\n" + "="*50)
    print("🚀 PROMPT: Now run 'python main.py' to start chatting!")
    print("="*50)

if __name__ == "__main__":
    run_brain_surgery()