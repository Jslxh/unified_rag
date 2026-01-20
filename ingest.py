import os
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings

from loaders.text_loader import load_text_file
from loaders.pdf_loader import load_pdf_file
from loaders.docx_loader import load_docx_file
from loaders.pptx_loader import load_pptx_file
from loaders.json_loader import load_json_file
from loaders.xml_loader import load_xml_file
from loaders.csv_loader import load_csv_file
from loaders.database_loader import load_database_file

DATA_DIR = "data"
VECTOR_DB_DIR = "vector_store/chroma"

def load_documents():
    """Load documents from data directory supporting multiple file types"""
    docs = []
    
    if not os.path.exists(DATA_DIR):
        print(f"Data directory '{DATA_DIR}' not found. Creating it...")
        os.makedirs(DATA_DIR)
        return []

    for file in os.listdir(DATA_DIR):
        path = os.path.join(DATA_DIR, file)
        
        # Skip directories
        if os.path.isdir(path):
            continue

        try:
            if file.endswith(".txt") or file.endswith(".md"):
                doc = load_text_file(path)
                docs.append(doc)
                print(f"✓ Loaded: {file}")
            
            elif file.endswith(".pdf"):
                file_docs = load_pdf_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file} ({len(file_docs)} pages)")
            
            elif file.endswith(".docx"):
                file_docs = load_docx_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file}")
            
            elif file.endswith(".pptx"):
                file_docs = load_pptx_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file} ({len(file_docs)} slides)")
            
            elif file.endswith(".json"):
                file_docs = load_json_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file}")
            
            elif file.endswith(".xml"):
                file_docs = load_xml_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file}")
            
            elif file.endswith(".csv"):
                file_docs = load_csv_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file}")
            
            elif file.endswith(".db") or file.endswith(".sqlite") or file.endswith(".sqlite3"):
                file_docs = load_database_file(path)
                docs.extend(file_docs)
                print(f"✓ Loaded: {file} ({len(file_docs)} tables)")
        
        except Exception as e:
            print(f"✗ Error loading {file}: {e}")
            continue

    return docs

def ingest():
    print("\n" + "="*60)
    print("RAG Document Ingestion Pipeline")
    print("="*60 + "\n")
    
    print("Loading documents...")
    raw_docs = load_documents()
    
    if not raw_docs:
        print("No documents found to ingest!")
        return
    
    print(f"\nTotal documents loaded: {len(raw_docs)}")

    texts = [d["content"] for d in raw_docs]
    metadatas = [d["metadata"] for d in raw_docs]

    print("\nChunking documents...")
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=100
    )

    chunks = splitter.create_documents(texts, metadatas)
    print(f"✓ Created {len(chunks)} chunks")

    print("\nGenerating embeddings...")
    embeddings = HuggingFaceEmbeddings(
        model_name="sentence-transformers/all-MiniLM-L6-v2",
        model_kwargs={"trust_remote_code": True},
        encode_kwargs={"normalize_embeddings": False}
    )

    print("Storing in vector database...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=VECTOR_DB_DIR
    )

    print("\n" + "="*60)
    print("✓ Ingestion Complete!")
    print(f"Vector DB ready at: {VECTOR_DB_DIR}")
    print("="*60 + "\n")

if __name__ == "__main__":
    ingest()
