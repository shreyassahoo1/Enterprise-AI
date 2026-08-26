import json
import logging
import re
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import List

# pyrefly: ignore [missing-import]
import streamlit as st

from chatbot.chain import RAGChain, RAGResponse
from config import Config
from utils.embeddings import (
    add_documents_to_store,
    build_vector_store,
    load_vector_store,
    reset_vector_store,
)
from utils.loader import load_documents_from_paths, SUPPORTED_EXTENSIONS
from utils.retriever import RetrievedChunk
from utils.splitter import split_documents
from utils.styles import CUSTOM_CSS, ANIMATED_BG
from utils.history import init_db, save_turn, save_feedback
from utils.auth import require_auth, render_sign_out

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Enterprise Chatbot",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>◈</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS + animated background (must be before auth so login form is styled)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(ANIMATED_BG, unsafe_allow_html=True)

# ── Authentication gate ────────────────────────────────────────────────────────
require_auth()

# ── Initialize history DB ──────────────────────────────────────────────────────
init_db()

# ── Logo Base64 Loader ─────────────────────────────────────────────────────────
import base64

def get_base64_image(image_path: Path) -> str:
    if image_path.exists():
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode("utf-8")
    return ""

logo_b64 = get_base64_image(Config.ASSETS_DIR / "aptus_logo.png")

# ── Session init ───────────────────────────────────────────────────────────────
def init_session_state() -> None:
    if "vector_store" not in st.session_state:
        st.session_state.vector_store = load_vector_store()
    if "conversation" not in st.session_state:
        st.session_state.conversation = []
    if "kb_doc_names" not in st.session_state:
        st.session_state.kb_doc_names = set()
    if "ingesting" not in st.session_state:
        st.session_state.ingesting = False
    if "session_id" not in st.session_state:
        st.session_state["session_id"] = uuid.uuid4().hex[:12]
    if "db_paths" not in st.session_state:
        st.session_state["db_paths"] = {}


init_session_state()

DRAG_DROP_HTML = '<img src="x" onerror="(function(){const doc=window.parent.document;if(!doc||doc.getElementById(\'drag-drop-style\'))return;const style=doc.createElement(\'style\');style.id=\'drag-drop-style\';style.innerHTML=\'#drag-drop-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(28, 61, 46, 0.95); z-index: 99999999; display: flex; flex-direction: column; justify-content: center; align-items: center; opacity: 0; pointer-events: none; transition: opacity 0.25s ease; font-family: Inter, sans-serif; color: #F5F2EC; border: 4px dashed rgba(245, 242, 236, 0.4); box-sizing: border-box; } #drag-drop-overlay.active { opacity: 1; pointer-events: auto; } .overlay-title { font-size: 26px; font-weight: 600; margin-bottom: 12px; text-align: center; } .overlay-subtitle { font-size: 16px; color: rgba(245, 242, 236, 0.7); text-align: center; }\';doc.head.appendChild(style);const overlay=doc.createElement(\'div\');overlay.id=\'drag-drop-overlay\';const title=doc.createElement(\'div\');title.className=\'overlay-title\';title.innerText=\'Drop files to upload to Enterprise Chatbot\';overlay.appendChild(title);const subtitle=doc.createElement(\'div\');subtitle.className=\'overlay-subtitle\';subtitle.innerText=\'Supports PDF, PPTX, TXT, DOCX, CSV, Excel, and SQLite\';overlay.appendChild(subtitle);doc.body.appendChild(overlay);let dragCounter=0;doc.addEventListener(\'dragenter\',(e)=>{e.preventDefault();dragCounter++;overlay.classList.add(\'active\');});doc.addEventListener(\'dragover\',(e)=>{e.preventDefault();});doc.addEventListener(\'dragleave\',(e)=>{e.preventDefault();dragCounter--;if(dragCounter===0){overlay.classList.remove(\'active\');}});doc.addEventListener(\'drop\',(e)=>{e.preventDefault();dragCounter=0;overlay.classList.remove(\'active\');const files=e.dataTransfer.files;if(files&&files.length>0){const fileInput=doc.querySelector(\'div[data-testid=stFileUploader] input[type=file]\');if(fileInput){const dataTransfer=new DataTransfer();for(let i=0;i<files.length;i++){dataTransfer.items.add(files[i]);}fileInput.files=dataTransfer.files;fileInput.dispatchEvent(new Event(\'change\',{bubbles:true}));}}});})();" style="display:none;"/>'
st.markdown(DRAG_DROP_HTML, unsafe_allow_html=True)

config_problems = Config.validate()

# ── Chunk counts helper ────────────────────────────────────────────────────────
CHUNK_COUNTS_PATH = Config.DATA_DIR / "chunk_counts.json"


def _load_chunk_counts() -> dict:
    if CHUNK_COUNTS_PATH.exists():
        try:
            return json.loads(CHUNK_COUNTS_PATH.read_text())
        except Exception:
            return {}
    return {}


def _save_chunk_counts(counts: dict) -> None:
    Config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    CHUNK_COUNTS_PATH.write_text(json.dumps(counts, indent=2))


# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    if logo_b64:
        st.markdown(
            f"""
            <div style="text-align: left; margin: -25px 0 0 0; padding: 0; width: 100%;">
              <img src="data:image/png;base64,{logo_b64}" style="width: 100%; display: block; margin: 0 0 10px 0;" />
              <h2 style="font-family: 'Lora', serif; font-size: 24px; font-weight: 500; margin: 10px 0 12px 0; color: var(--cream); line-height: 1.2;">Enterprise Chatbot</h2>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.markdown("## Enterprise Chatbot")
    st.markdown("---")

    for problem in config_problems:
        st.error(problem)

    # Knowledge base status
    if st.session_state.vector_store is not None:
        doc_list = sorted(st.session_state.kb_doc_names)
        if doc_list:
            st.caption(f"{len(doc_list)} document(s) uploaded")
            for name in doc_list:
                st.markdown(f"\U0001F4C4 {name}")
        else:
            st.caption("No documents uploaded")
    else:
        st.caption("No documents uploaded")

    # Chat history (last 10 prompts)
    if st.session_state.conversation:
        st.markdown("")
        st.markdown("**Chat History**")
        history_turns = st.session_state.conversation[-10:]
        for i, turn in enumerate(history_turns):
            global_idx = len(st.session_state.conversation) - len(history_turns) + i
            query_text = turn["question"]
            if len(query_text) > 28:
                query_text = query_text[:25] + "..."
            st.markdown(
                f'<a class="sidebar-chat-link" href="#chat-turn-{global_idx}" target="_self">{query_text}</a>',
                unsafe_allow_html=True
            )
        st.markdown("---")

    # Bottom controls pushed specifically to the bottom
    st.markdown('<div class="sidebar-spacer"></div>', unsafe_allow_html=True)

    # New chat button
    if st.button("New chat", use_container_width=True, key="btn_new_chat"):
        st.session_state["session_id"] = uuid.uuid4().hex[:12]
        st.session_state.conversation = []
        st.rerun()

    if st.button("Reset knowledge base", use_container_width=True, key="btn_reset_kb"):
        reset_vector_store()
        st.session_state.vector_store = None
        st.session_state.kb_doc_names = set()
        st.session_state["db_paths"] = {}
        # Clear chunk counts
        _save_chunk_counts({})
        st.rerun()

    if st.button("Clear chat", use_container_width=True, key="btn_clear_chat"):
        st.session_state.conversation = []
        st.rerun()

    with st.expander("Configuration"):
        st.caption(f"Chunk size: {Config.CHUNK_SIZE}")
        st.caption(f"Chunk overlap: {Config.CHUNK_OVERLAP}")
        st.caption(f"Embedding: {Config.EMBEDDING_BACKEND} ({Config.EMBEDDING_MODEL if Config.EMBEDDING_BACKEND == 'openai' else Config.LOCAL_EMBEDDING_MODEL})")
        st.caption(f"LLM: {Config.LLM_MODEL}  |  temp: {Config.LLM_TEMPERATURE}")
        st.caption(f"Top K: {Config.TOP_K}  |  Fetch K: {Config.RETRIEVAL_FETCH_K}")
        st.caption(f"Max file size: {Config.MAX_FILE_SIZE_MB} MB")

    # Sign out (always at the very bottom)
    render_sign_out()


# ── Main area ──────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rag-header">
  <h1>Enterprise Chatbot</h1>
</div>
<p class="rag-tagline">
  Ask anything about your documents. Every answer is grounded in your content — nothing invented.
</p>
""", unsafe_allow_html=True)


# ── Source rendering ───────────────────────────────────────────────────────────
def render_sources(sources: List[RetrievedChunk], key_suffix: str = "") -> None:
    if not sources:
        return
    with st.expander(f"Sources — {len(sources)} passage(s) retrieved"):
        for i, chunk in enumerate(sources, start=1):
            st.markdown(f"**{i}. {chunk.source}** — page {chunk.page}")
            relevance = max(0.0, min(1.0, 1.0 / (1.0 + chunk.score))) * 100
            st.progress(
                int(relevance),
                text=f"Relevance: {relevance:.0f}%  (distance: {chunk.score:.3f})",
            )
            st.text_area(
                "Passage",
                value=chunk.content,
                height=110,
                key=f"chunk_{i}_{chunk.source}_{chunk.page}_{chunk.chunk_index}_{key_suffix}",
                disabled=True,
            )
            if i < len(sources):
                st.divider()


def render_response_content(answer: str) -> None:
    pattern = r'\s*(\(Source:\s*[^)]+\))\s*$'
    citations = []
    clean_text = answer
    while True:
        match = re.search(pattern, clean_text)
        if match:
            citation = match.group(1)
            citations.insert(0, citation)
            clean_text = clean_text[:match.start()]
        else:
            break

    st.write(clean_text)

    if citations:
        citations_str = " ".join(citations)
        st.markdown(
            f'<div class="rag-source-citation">{citations_str}</div>',
            unsafe_allow_html=True
        )


def render_metrics(response: RAGResponse) -> None:
    cols = st.columns(4)
    cols[0].metric("Response time", f"{response.response_time_seconds:.2f}s")
    cols[1].metric("Passages used", len(response.sources))
    if response.total_tokens is not None:
        cols[2].metric("Total tokens", response.total_tokens)
        cols[3].metric(
            "Prompt / Completion",
            f"{response.prompt_tokens or 0} / {response.completion_tokens or 0}",
        )
    else:
        cols[2].metric("Total tokens", "n/a")
        cols[3].metric("Prompt / Completion", "n/a")


def render_feedback(turn_id, key_suffix: str = "") -> None:
    """Render feedback buttons for a conversation turn."""
    if turn_id is None:
        return
    feedback_key = f"feedback_{turn_id}"
    if st.session_state.get(feedback_key):
        st.markdown(
            '<p style="font-size:12px; color:var(--text-light); margin:4px 0 0 0;">Feedback saved.</p>',
            unsafe_allow_html=True,
        )
        return
    col1, col2, _ = st.columns([1, 1, 6])
    with col1:
        st.markdown('<div class="feedback-btn">', unsafe_allow_html=True)
        if st.button("Helpful", key=f"fb_up_{turn_id}_{key_suffix}"):
            save_feedback(turn_id, "up")
            st.session_state[feedback_key] = "up"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="feedback-btn">', unsafe_allow_html=True)
        if st.button("Not helpful", key=f"fb_down_{turn_id}_{key_suffix}"):
            save_feedback(turn_id, "down")
            st.session_state[feedback_key] = "down"
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)


# ── Conversation history ───────────────────────────────────────────────────────
for turn_idx, turn in enumerate(st.session_state.conversation):
    st.markdown(f'<div id="chat-turn-{turn_idx}" style="position: relative; top: -80px;"></div>', unsafe_allow_html=True)
    with st.chat_message("user"):
        st.write(turn["question"])
    with st.chat_message("assistant"):
        render_response_content(turn["answer"])
        sources = [RetrievedChunk(**s) for s in turn.get("sources", [])]
        render_sources(sources, key_suffix=f"history_{turn_idx}")
        st.caption(
            f"{turn.get('response_time_seconds', 0):.2f}s  ·  "
            f"{len(sources)} passage(s)  ·  "
            f"{turn.get('total_tokens', 'n/a')} tokens"
        )
        # Feedback buttons for history turns
        render_feedback(turn.get("turn_id"), key_suffix=f"hist_{turn_idx}")


# ── Query bar with Upload Popover ──────────────────────────────────────────────
# Anchor element for absolute positioning of popover
st.markdown('<div id="upload-popover-anchor"></div>', unsafe_allow_html=True)

with st.popover("＋", help="Upload documents to knowledge base"):
    st.markdown("### Upload Documents")
    st.caption("PDF, TXT, PPTX, DOCX, CSV, Excel, SQLite formats supported")
    uploaded_files = st.file_uploader(
        "Upload files",
        type=["pdf", "txt", "pptx", "ppt", "docx", "jpeg", "jpg", "png",
              "csv", "xlsx", "xls", "db"],
        accept_multiple_files=True,
        key="query_file_uploader",
        label_visibility="collapsed",
    )

    # ── Auto-ingest new files ──────────────────────────────────────────────────
    if uploaded_files and not config_problems:
        new_files = [
            f for f in uploaded_files
            if f.name not in st.session_state.kb_doc_names
        ]
        if new_files:
            progress = st.progress(0, text="Reading files...")
            saved_paths = []
            db_files = []
            oversized = []

            for uf in new_files:
                size_mb = len(uf.getvalue()) / (1024 * 1024)
                if size_mb > Config.MAX_FILE_SIZE_MB:
                    oversized.append(uf.name)
                    continue
                dest = Config.DOCS_DIR / uf.name
                try:
                    dest.write_bytes(uf.getvalue())
                    # Route .db files to SQLAgent instead of RAG pipeline
                    if uf.name.lower().endswith(".db"):
                        db_files.append(dest)
                    else:
                        saved_paths.append(dest)
                except Exception as exc:
                    st.warning(f"Could not save {uf.name}: {exc}")

            for name in oversized:
                st.warning(f"{name} exceeds {Config.MAX_FILE_SIZE_MB} MB and was skipped.")

            # Handle .db files — store for SQLAgent
            for db_path in db_files:
                st.session_state["db_paths"][db_path.name] = str(db_path)
                st.session_state.kb_doc_names.add(db_path.name)
                st.success(f"Database '{db_path.name}' loaded for SQL queries.")

            if saved_paths:
                progress.progress(25, text="Extracting text...")
                documents = load_documents_from_paths(saved_paths)

                if documents:
                    progress.progress(50, text="Chunking...")
                    chunks = split_documents(documents)

                    progress.progress(70, text="Building index...")
                    try:
                        if st.session_state.vector_store is None:
                            vs = build_vector_store(chunks)
                        else:
                            vs = add_documents_to_store(st.session_state.vector_store, chunks)
                        st.session_state.vector_store = vs
                        # Update chunk counts
                        chunk_counts = _load_chunk_counts()
                        for p in saved_paths:
                            file_chunks = [c for c in chunks if c.metadata.get("source") == p.name]
                            chunk_counts[p.name] = len(file_chunks)
                            st.session_state.kb_doc_names.add(p.name)
                        _save_chunk_counts(chunk_counts)
                        progress.progress(100, text="Ready")
                        time.sleep(0.4)
                        progress.empty()
                        st.success(
                            f"Indexed {len(chunks)} chunk(s) from "
                            f"{len(saved_paths)} file(s)."
                        )
                        st.rerun()
                    except EnvironmentError as exc:
                        progress.empty()
                        st.error(str(exc))
                    except Exception as exc:
                        progress.empty()
                        logger.exception("Failed to build/update vector store.")
                        st.error(f"Indexing failed: {exc}")
                else:
                    progress.empty()
                    st.error("No readable text found in the uploaded file(s).")
            elif not db_files:
                progress.empty()


# ── Chat input ─────────────────────────────────────────────────────────────────
question = st.chat_input("Ask a question about your documents...")

if question:
    with st.chat_message("user"):
        st.write(question)

    sql_handled = False

    # Try SQL agent first if .db files are available
    if st.session_state.get("db_paths"):
        from utils.sql_agent import SQLAgent

        # Use the most recently uploaded .db file
        db_name = list(st.session_state["db_paths"].keys())[-1]
        db_path = st.session_state["db_paths"][db_name]
        agent = SQLAgent(db_path)

        with st.chat_message("assistant"):
            with st.spinner("Querying database..."):
                sql_result = agent.ask(question)

            if sql_result["rows"] and not sql_result["error"]:
                sql_handled = True
                import pandas as pd

                answer_text = f"Query returned {len(sql_result['rows'])} row(s) from '{db_name}'."
                st.write(answer_text)

                df = pd.DataFrame(sql_result["rows"], columns=sql_result["columns"])
                st.dataframe(df, use_container_width=True)

                with st.expander("Query used"):
                    st.code(sql_result["sql"], language="sql")

                # Save to history
                turn_id = save_turn(
                    session_id=st.session_state["session_id"],
                    question=question,
                    answer=answer_text,
                    sources=[{"source": db_name, "page": 0, "score": 0.0}],
                    response_time=0.0,
                    total_tokens=None,
                )

                st.session_state.conversation.append({
                    "question": question,
                    "answer": answer_text,
                    "sources": [],
                    "response_time_seconds": 0.0,
                    "total_tokens": None,
                    "timestamp": datetime.now().isoformat(timespec="seconds"),
                    "turn_id": turn_id,
                })

                # Feedback for SQL turn
                render_feedback(turn_id, key_suffix="active_sql")

    # Fall through to RAG if SQL didn't handle it
    if not sql_handled:
        with st.chat_message("assistant"):
            with st.spinner("Searching and composing an answer..."):
                chain = RAGChain(st.session_state.vector_store)
                response = chain.ask(question)

            render_response_content(response.answer)
            render_sources(response.sources, key_suffix="active")
            render_metrics(response)

            if response.error:
                logger.info("Turn completed with error: %s", response.error)

            # Save to history
            sources_for_db = [
                {"source": s.source, "page": s.page, "score": s.score}
                for s in response.sources
            ]
            turn_id = save_turn(
                session_id=st.session_state["session_id"],
                question=question,
                answer=response.answer,
                sources=sources_for_db,
                response_time=response.response_time_seconds,
                total_tokens=response.total_tokens,
            )

            st.session_state.conversation.append({
                "question": question,
                "answer": response.answer,
                "sources": [
                    {
                        "content": s.content,
                        "source": s.source,
                        "page": s.page,
                        "chunk_index": s.chunk_index,
                        "score": s.score,
                    }
                    for s in response.sources
                ],
                "response_time_seconds": response.response_time_seconds,
                "total_tokens": response.total_tokens,
                "timestamp": datetime.now().isoformat(timespec="seconds"),
                "turn_id": turn_id,
            })

            # Feedback for RAG turn
            render_feedback(turn_id, key_suffix="active_rag")


# Render the scroll spacer at the very bottom of the page to ensure it is always the last element,
# allowing the page to scroll past the floating chat input bar.
st.markdown('<div style="height: 300px;"></div>', unsafe_allow_html=True)
