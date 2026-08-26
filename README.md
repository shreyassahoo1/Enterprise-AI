# 📄 Document RAG Assistant

A production-quality, beginner-friendly **Retrieval-Augmented Generation (RAG)** chatbot that answers questions **strictly from your uploaded PDF documents** — built with LangChain, OpenAI, FAISS, and Streamlit.

If the answer isn't in your documents, the assistant will tell you so instead of guessing. No hallucinations, every answer cited with a source document and page number.

---

## Table of Contents

- [Project Overview](#project-overview)
- [Architecture](#architecture)
- [Features](#features)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [Running the Project](#running-the-project)
- [Example Usage](#example-usage)
- [Configuration](#configuration)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [Future Improvements](#future-improvements)

---

## Project Overview

This project implements a **Document Question Answering System**: upload one or more PDFs, the app chunks and embeds them, stores the embeddings in a local FAISS vector index, and lets you chat with your documents. Every answer is grounded in retrieved chunks — the LLM is explicitly instructed never to use outside knowledge.

It is intentionally **modular and heavily commented** so it doubles as a learning reference for how a real-world RAG pipeline is put together: loading → chunking → embedding → vector storage → retrieval → prompting → generation → citation.

---

## Architecture

```
PDF Documents
       │
       ▼
Document Loader      (utils/loader.py - PyPDFLoader, skips empty pages)
       │
       ▼
Chunking              (utils/splitter.py - RecursiveCharacterTextSplitter)
       │
       ▼
Embeddings             (utils/embeddings.py - text-embedding-3-small)
       │
       ▼
FAISS                  (utils/embeddings.py - local vector store)
       │
       ▼
Retriever              (utils/retriever.py - similarity search, Top K=3)
       │
       ▼
GPT-4o                 (chatbot/llm.py + chatbot/chain.py)
       │
       ▼
Generated Answer       (with source document + page citations)
```

**Module responsibilities at a glance:**

| Module | Responsibility |
|---|---|
| `config.py` | Single source of truth for every setting (chunk size, models, paths, etc.) |
| `utils/loader.py` | Loads PDFs, ignores empty pages, preserves metadata |
| `utils/splitter.py` | Splits documents into overlapping chunks |
| `utils/embeddings.py` | Generates embeddings, builds/loads/extends the FAISS index |
| `utils/retriever.py` | Runs similarity search, formats retrieved context |
| `utils/prompt.py` | The anti-hallucination system prompt |
| `chatbot/llm.py` | Configured GPT-4o client |
| `chatbot/chain.py` | Orchestrates retrieval + prompting + generation, with full error handling |
| `ingest.py` | CLI script to (re)build the knowledge base from `docs/` |
| `app.py` | Streamlit UI |

---

## Features

- 🔍 **Strict, grounded answers** — never hallucinates; explicitly says when an answer isn't in the documents.
- 📚 **Source citations** — every answer shows the source PDF, page number, and the exact retrieved chunk.
- 📊 **Similarity scores** — see how relevant each retrieved chunk was.
- 💬 **Chat interface** with persistent conversation history (within a session).
- ⬇️ **Download chat history** as JSON.
- 📈 **Live metrics** — response time, token usage, number of chunks retrieved.
- 🧱 **Incremental indexing** — add new PDFs without rebuilding the whole index (or force a full rebuild).
- 🗑️ **Reset Knowledge Base** button to start fresh.
- 📁 **Multi-PDF upload** in one go.
- 🛡️ **Robust error handling** for empty PDFs, corrupted files, missing API keys, empty questions, empty vector stores, timeouts, and network failures.
- 🌓 Works well in both light and dark Streamlit themes (uses native `st.chat_message` bubbles).

---

## Folder Structure

```
rag-document-chatbot/
│
├── app.py                  # Streamlit UI (entry point)
├── ingest.py                # CLI ingestion script
├── config.py                 # Central configuration
├── requirements.txt
├── README.md
├── .env                       # Your real secrets (not committed)
├── .env.example               # Template for .env
│
├── docs/                      # Put/upload source PDFs here
├── data/                      # Scratch space for intermediate data
├── vector_store/              # Persisted FAISS index (auto-created)
│
├── utils/
│   ├── loader.py               # Phase 1 - Document loading
│   ├── splitter.py              # Phase 2 - Chunking
│   ├── embeddings.py             # Phase 3 & 4 - Embeddings + FAISS
│   ├── retriever.py               # Phase 5 - Retrieval
│   └── prompt.py                   # Phase 6 - Prompt engineering
│
├── chatbot/
│   ├── llm.py                       # Phase 7 - LLM client
│   └── chain.py                      # End-to-end RAG orchestration
│
└── assets/                            # Screenshots / static assets for docs
```

---

## Installation

### Requirements

- Python 3.11+
- An OpenAI API key with access to `gpt-4o` and `text-embedding-3-small`

### Steps

```bash
# 1. Clone / unzip the project, then move into it
cd rag-document-chatbot

# 2. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure your API key
cp .env.example .env
# then edit .env and set OPENAI_API_KEY=sk-...
```

---

## Running the Project

### Option A — Streamlit UI (recommended)

```bash
streamlit run app.py
```

Then open the URL Streamlit prints (typically `http://localhost:8501`), upload PDFs in the sidebar, click **Build Knowledge Base**, and start asking questions.

### Option B — CLI ingestion (headless)

If you'd rather pre-build the index from PDFs already placed in `docs/`:

```bash
python ingest.py             # build only if no index exists yet
python ingest.py --rebuild   # force a full rebuild
```

Then launch `streamlit run app.py` — it will automatically pick up the existing index.

---

## Example Usage

1. Upload `HR_Policy.pdf` via the sidebar.
2. Click **Build Knowledge Base** and watch the progress bar move through loading → chunking → embedding.
3. Ask: *"What is the leave policy?"*
4. The assistant answers using only the retrieved chunks, and shows:
   - **Answer:** "Employees are entitled to 20 days of paid annual leave per year. (Source: HR_Policy.pdf, Page 1)"
   - **Sources & Retrieved Context** (expandable): the exact chunk text, source file, page number, and similarity score.
   - **Metrics:** response time, chunks retrieved, token usage.

If you ask something not covered by the document (e.g. *"What's the weather today?"*), the assistant responds:

> "I couldn't find information related to your question in the uploaded documents."

*(Screenshots can be added to the `assets/` folder and referenced here, e.g. `![UI overview](assets/ui_overview.png)`.)*

---

## Configuration

Everything tunable lives in `config.py` and can be overridden via environment variables (in `.env`):

| Setting | Default | Description |
|---|---|---|
| `CHUNK_SIZE` | 500 | Characters per chunk |
| `CHUNK_OVERLAP` | 100 | Overlap between consecutive chunks |
| `EMBEDDING_MODEL` | `text-embedding-3-small` | OpenAI embedding model |
| `TOP_K` | 3 | Number of chunks retrieved per query |
| `LLM_MODEL` | `gpt-4o` | Chat model used for answer generation |
| `LLM_TEMPERATURE` | 0 | Lower = more deterministic, factual answers |
| `LLM_MAX_TOKENS` | 1000 | Max tokens in the generated answer |
| `LLM_REQUEST_TIMEOUT` | 60 | Seconds before an API call times out |

---

## Error Handling

The app gracefully handles, with friendly user-facing messages:

- **Empty PDFs** — skipped with a logged warning; the rest of the batch still processes.
- **Corrupted PDFs** — caught during loading, skipped without crashing the app.
- **Missing OpenAI key** — detected on startup (`config.py` validation) and before any embedding/LLM call.
- **Empty question** — rejected with a prompt to enter a question.
- **Empty vector database** — clear message asking the user to build the knowledge base first.
- **API timeout / network failures / rate limits / auth errors** — each caught explicitly with a tailored message (`chatbot/chain.py`).

---

## Troubleshooting

| Problem | Likely Cause | Fix |
|---|---|---|
| "OPENAI_API_KEY is missing" | `.env` not created or empty | Copy `.env.example` to `.env` and add your key |
| "No readable text could be extracted" | Uploaded PDF is scanned/image-only | Use an OCR tool first (OCR support is on the roadmap, see below) |
| App says no knowledge base | Haven't clicked "Build Knowledge Base" yet | Upload PDFs, then click the button |
| Slow first response | Cold-start embedding/model calls | Normal — subsequent queries are faster |
| `DeprecationWarning: langchain-community is being sunset` on startup | Upstream library notice, harmless | Safe to ignore for now; will be addressed when LangChain's standalone FAISS/PDF packages stabilize |
| Authentication error | Invalid or expired API key | Regenerate your key on the OpenAI dashboard |

---

## Future Improvements

These are intentionally **not implemented** in this version, but are natural next steps:

- Hybrid Search (BM25 + Vector Search)
- Re-ranking of retrieved chunks
- OCR for scanned PDFs
- Multilingual support
- Database integration (e.g. persistent chat history across sessions)
- User authentication
- Citation highlighting directly in the source text
- Evaluation using RAGAS
- LangSmith tracing for observability
- Agentic RAG (multi-step reasoning, tool use)
- Support for Word, PowerPoint, and Excel files

---

## License

This is an educational reference project — adapt and reuse it freely for your own learning or production needs.
