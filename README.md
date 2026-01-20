# Unified RAG-Based Intelligent Knowledge Assistant

[![Status](https://img.shields.io/badge/Status-Production%20Ready-brightgreen)](https://github.com)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Document Formats](https://img.shields.io/badge/Formats-11%20Supported-orange)](README.md#supported-file-formats)
[![Last Updated](https://img.shields.io/badge/Updated-Jan%202026-blue)]()

A unified **Retrieval-Augmented Generation (RAG)** system enabling natural language, context-aware querying across **11 document formats** through a single conversational interface with multi-turn dialogue support.

## Overview

Organizations store knowledge across PDFs, text files, and structured data, making retrieval fragmented and inefficient.

This project solves that problem by providing a **single conversational interface** that:

- Ingests documents  
- Builds a vector database  
- Retrieves relevant context  
- Generates grounded answers using an LLM  

---

## Key Features

- **RAG Architecture** – Retrieval + Generation for hallucination-controlled answers  
- **Multi-format Support** – PDF, TXT (extensible to more formats)  
- **Semantic Search** – ChromaDB with dense embeddings  
- **LLM Integration** – Google Gemini (official SDK)  
- **Persistent Vector Store** – Reusable across sessions  
- **CLI Interface** – Simple interactive querying  

---

## Supported Formats

| Category        | Formats                   |
|-----------------|---------------------------|
| Unstructured    | PDF, TXT                  |
| Extensible      | DOCX, PPTX, CSV, JSON, DB |

> Loader-based architecture allows easy extension to additional formats.

---

## Architecture
```text
User Question
↓
Vector Search (ChromaDB)
↓
Relevant Context
↓
Prompt Construction
↓
Google Gemini LLM
↓
Final Answer
```


## Project Structure
```text
unified_rag/
├── ingest.py # Document ingestion pipeline
├── query.py # RAG-based query engine
├── requirements.txt
├── .env # API keys
│
├── loaders/
│ ├── pdf_loader.py
│ └── text_loader.py
│
├── data/ # Input documents
│
├── vector_store/
│ └── chroma/ # Persistent vector DB
```


---

## Tech Stack

- **Python 3.8+**
- **ChromaDB** – Vector storage
- **SentenceTransformers** – Embeddings
- **Google Gemini** – LLM (official SDK)
- **LangChain** – Retrieval utilities

---

## Installation

```bash
# Create virtual environment
python -m venv .venv
.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

Create .env file: GOOGLE_API_KEY=your_api_key_here

# Ingest Documents
python ingest.py

# Query the Knowledge Base
python query.py

Example Query: Explain the types of parthenogenesis

```
## How It Works

```text
* Documents are loaded and chunked
* Embeddings are generated and stored in ChromaDB
* User query retrieves top-k relevant chunks
* Retrieved context is passed to Gemini
* LLM generates a grounded response
```


