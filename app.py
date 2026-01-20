import streamlit as st
import os
import shutil
from pathlib import Path
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from dotenv import load_dotenv
import google.genai as genai
from loaders.text_loader import load_text_file
from loaders.pdf_loader import load_pdf_file
from loaders.docx_loader import load_docx_file
from loaders.pptx_loader import load_pptx_file
from loaders.json_loader import load_json_file
from loaders.xml_loader import load_xml_file
from loaders.csv_loader import load_csv_file
from loaders.database_loader import load_database_file
import warnings

warnings.filterwarnings("ignore")
load_dotenv()

# Configuration
DATA_DIR = "data"
VECTOR_DB_DIR = "vector_store/chroma"
api_key = os.getenv("GOOGLE_API_KEY")
MODEL_NAME = "gemini-2.0-flash"
EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

# Initialize Streamlit config
st.set_page_config(
    page_title="RAG System - Document Q&A",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Sidebar styling
st.sidebar.title("RAG Control Panel")

# Initialize session state
if "documents_loaded" not in st.session_state:
    st.session_state.documents_loaded = False
if "query_result" not in st.session_state:
    st.session_state.query_result = None
if "embeddings" not in st.session_state:
    st.session_state.embeddings = None
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []


@st.cache_resource
def get_embeddings():
    """Get embedding model with caching"""
    try:
        embeddings = HuggingFaceEmbeddings(
            model_name=EMBEDDING_MODEL,
            model_kwargs={"trust_remote_code": True},
            encode_kwargs={"normalize_embeddings": False}
        )
        return embeddings
    except Exception as e:
        st.error(f"Error loading embeddings: {e}")
        return None


def get_chroma_db():
    """Get or create Chroma database"""
    try:
        return Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=get_embeddings()
        )
    except Exception as e:
        st.error(f"Error connecting to vector store: {e}")
        return None


def load_all_documents():
    """Load all documents from data directory supporting multiple formats"""
    try:
        docs = []
        if not os.path.exists(DATA_DIR):
            st.warning(f"Data directory '{DATA_DIR}' not found")
            return []
        
        file_count = 0
        for file in os.listdir(DATA_DIR):
            path = os.path.join(DATA_DIR, file)
            
            # Skip directories
            if os.path.isdir(path):
                continue
            
            try:
                if file.endswith(".txt") or file.endswith(".md"):
                    doc = load_text_file(path)
                    docs.append(doc)
                    file_count += 1
                
                elif file.endswith(".pdf"):
                    file_docs = load_pdf_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".docx"):
                    file_docs = load_docx_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".pptx"):
                    file_docs = load_pptx_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".json"):
                    file_docs = load_json_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".xml"):
                    file_docs = load_xml_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".csv"):
                    file_docs = load_csv_file(path)
                    docs.extend(file_docs)
                    file_count += 1
                
                elif file.endswith(".db") or file.endswith(".sqlite") or file.endswith(".sqlite3"):
                    file_docs = load_database_file(path)
                    docs.extend(file_docs)
                    file_count += 1
            
            except Exception as e:
                st.error(f"Error loading {file}: {e}")
                continue
        
        if file_count == 0:
            st.warning("No documents found in data directory")
        
        return docs
    except Exception as e:
        st.error(f"Error loading documents: {e}")
        return []


def save_uploaded_file(uploaded_file):
    """Save uploaded file to data directory"""
    try:
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        
        file_path = os.path.join(DATA_DIR, uploaded_file.name)
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())
        
        return True, file_path
    except Exception as e:
        return False, str(e)


def ingest_documents():
    """Ingest documents into vector store"""
    try:
        st.info("Loading documents...")
        raw_docs = load_all_documents()
        
        if not raw_docs:
            st.warning("No documents to ingest")
            return False
        
        texts = [d["content"] for d in raw_docs]
        metadatas = [d["metadata"] for d in raw_docs]
        
        st.info(f"Splitting {len(texts)} documents into chunks...")
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=500,
            chunk_overlap=100
        )
        chunks = splitter.create_documents(texts, metadatas)
        st.success(f"Created {len(chunks)} chunks")
        
        st.info("Generating embeddings and storing in vector database...")
        embeddings = get_embeddings()
        Chroma.from_documents(
            documents=chunks,
            embedding=embeddings,
            persist_directory=VECTOR_DB_DIR
        )
        
        st.success("Ingestion complete! Vector database ready.")
        st.session_state.documents_loaded = True
        return True
    except Exception as e:
        st.error(f"Ingestion failed: {e}")
        return False


def query_documents(question: str):
    """Query documents with LLM"""
    try:
        db = get_chroma_db()
        if db is None:
            return "Error: Vector store not available. Please ingest documents first."
        
        embeddings = get_embeddings()
        db = Chroma(
            persist_directory=VECTOR_DB_DIR,
            embedding_function=embeddings
        )
        
        docs = db.similarity_search(question, k=4)
        context = "\n\n".join([d.page_content for d in docs])
        
        if not context.strip():
            return "No relevant documents found for this query."
        
        prompt = f"""
You are an academic assistant.
Answer ONLY using the context below.
If the answer is not present, say "Not found in documents".

Context:
{context}

Question:
{question}
"""
        
        try:
            genai.configure(api_key=api_key)
            client = genai.Client(api_key=api_key)
            response = client.models.generate_content(
                model=MODEL_NAME,
                contents=prompt
            )
            
            if hasattr(response, "text") and response.text:
                return response.text
            try:
                return response.candidates[0].content.parts[0].text
            except (AttributeError, IndexError, TypeError):
                return str(response)
        except Exception as e:
            # Fallback to extractive search
            err_summary = f"{e.__class__.__name__}"
            try:
                sentences = [s.strip() for s in context.replace('\n', ' ').split('.') if s.strip()]
                q_words = {w.lower() for w in question.split() if len(w) > 3}
                imperative_verbs = {'write', 'explain', 'define', 'describe', 'discuss', 'list', 'state', 'mention', 'give', 'what', 'how', 'when', 'where', 'why'}
                
                matches = [
                    s for s in sentences 
                    if any(w in s.lower() for w in q_words) 
                    and len(s) > 20
                    and s.lower() != question.lower()
                    and not any(s.lower().startswith(verb) for verb in imperative_verbs)
                ]
                
                if matches:
                    seen = set()
                    unique_matches = []
                    for m in matches:
                        if m not in seen:
                            seen.add(m)
                            unique_matches.append(m)
                    return "[Fallback - Extracted from documents]\n\n" + " ".join(unique_matches[:3])
            except Exception:
                pass
            
            return f"[LLM Error - {err_summary}] Extracted content not available. Please check your API quota."
    
    except Exception as e:
        return f"Query failed: {str(e)}"


def get_document_list():
    """Get document count from vector store"""
    try:
        db = get_chroma_db()
        if db is None:
            return 0
        
        collection = db._collection
        count = collection.count()
        return count
    except Exception as e:
        st.error(f"Error getting document count: {e}")
        return 0


def delete_vector_store():
    """Delete all documents from vector store"""
    try:
        if os.path.exists(VECTOR_DB_DIR):
            shutil.rmtree(VECTOR_DB_DIR)
            st.success("Vector store deleted successfully")
            st.session_state.documents_loaded = False
            return True
        else:
            st.warning("Vector store not found")
            return False
    except Exception as e:
        st.error(f"Error deleting vector store: {e}")
        return False


def reset_all():
    """Reset entire system"""
    try:
        delete_vector_store()
        st.success("System reset successfully")
        st.session_state.documents_loaded = False
    except Exception as e:
        st.error(f"Reset failed: {e}")


def delete_document(filename):
    """Delete a specific document from data directory"""
    try:
        file_path = os.path.join(DATA_DIR, filename)
        if os.path.exists(file_path):
            os.remove(file_path)
            return True, "Document deleted successfully"
        else:
            return False, "File not found"
    except Exception as e:
        return False, str(e)


# ============ MAIN APP ============

st.title("RAG Assistant")
st.markdown("---")

# Tabs for different operations
tab1, tab2, tab3 = st.tabs(["Search", "Upload & Ingest", "Manage"])

# ============ TAB 1: SEARCH ============
with tab1:
    st.header("Search Your Documents")
    
    if not st.session_state.documents_loaded:
        st.warning("No documents loaded. Please upload and ingest documents first.")
    
    question = st.text_area(
        "Enter your question:",
        placeholder="e.g., What is parthenogenesis?",
        height=100
    )
    
    col1, col2 = st.columns([1, 3])
    with col1:
        search_button = st.button("Search", use_container_width=True)
    
    if search_button and question:
        with st.spinner("Searching..."):
            result = query_documents(question)
            st.session_state.query_result = result
    
    if st.session_state.query_result:
        st.markdown("### Answer:")
        st.info(st.session_state.query_result)


# ============ TAB 2: UPLOAD & INGEST ============
with tab2:
    st.header("Upload Documents")
    
    uploaded_files = st.file_uploader(
        "Choose files to upload (PDF, Word, PPT, TXT, JSON, XML, CSV, SQLite)",
        type=["txt", "md", "pdf", "docx", "pptx", "json", "xml", "csv", "db", "sqlite", "sqlite3"],
        accept_multiple_files=True
    )
    
    if uploaded_files:
        st.markdown("### Files to upload:")
        for file in uploaded_files:
            col1, col2 = st.columns([3, 1])
            with col1:
                st.text(f"• {file.name} ({file.size / 1024:.1f} KB)")
            with col2:
                if st.button("Upload", key=f"upload_{file.name}"):
                    success, message = save_uploaded_file(file)
                    if success:
                        st.success(f"Uploaded: {file.name}")
                    else:
                        st.error(f"Failed: {message}")
    
    st.markdown("---")
    st.header("Ingest Documents")
    
    st.info("This will process all files in the 'data/' directory and create embeddings.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Start Ingestion", use_container_width=True):
            with st.spinner("Processing documents..."):
                ingest_documents()
    
    with col2:
        if st.button("Reload", use_container_width=True):
            st.rerun()
    
    st.markdown("---")
    st.subheader("Files in data/ directory:")
    if os.path.exists(DATA_DIR):
        files = os.listdir(DATA_DIR)
        if files:
            for f in files:
                if f.endswith(('.txt', '.md', '.pdf', '.docx', '.pptx', '.json', '.xml', '.csv', '.db', '.sqlite', '.sqlite3')):
                    size = os.path.getsize(os.path.join(DATA_DIR, f)) / 1024
                    col1, col2, col3 = st.columns([2, 1, 1])
                    with col1:
                        st.text(f"✓ {f} ({size:.1f} KB)")
                    with col2:
                        pass
                    with col3:
                        if st.button("Delete", key=f"delete_{f}", use_container_width=True):
                            success, message = delete_document(f)
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(f"Failed to delete: {message}")
        else:
            st.info("No files in data/ directory yet")
    else:
        st.error("data/ directory not found")


# ============ TAB 3: MANAGE ============
with tab3:
    st.header("Manage Vector Store")
    
    st.subheader("Current Status:")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if os.path.exists(VECTOR_DB_DIR):
            st.metric("Vector Store", "Ready")
        else:
            st.metric("Vector Store", "Empty")
    
    with col2:
        doc_count = get_document_list()
        st.metric("Chunks Stored", f"{doc_count}")
    
    with col3:
        if st.session_state.documents_loaded:
            st.metric("Status", "Loaded")
        else:
            st.metric("Status", "Waiting")
    
    st.markdown("---")
    st.subheader("Delete Operations:")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Delete Vector Store", use_container_width=True):
            with st.spinner("Deleting..."):
                delete_vector_store()
                st.rerun()
    
    with col2:
        if st.button("Reset All", use_container_width=True):
            with st.spinner("Resetting..."):
                reset_all()
                st.rerun()
    
    st.warning("These operations are irreversible!")


# ============ SIDEBAR ============
with st.sidebar:
    st.markdown("---")
    
    st.subheader("Status")
    if os.path.exists(VECTOR_DB_DIR):
        st.success("Vector Store Ready")
    else:
        st.error("Vector Store Empty")
    
    doc_count = get_document_list()
    st.metric("Chunks Stored", doc_count)
    
    st.markdown("---")
    
    if st.button("Refresh Page", use_container_width=True):
        st.rerun()
    
    st.markdown("---")
    st.caption("RAG System v1.0")
