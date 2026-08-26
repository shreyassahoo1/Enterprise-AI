"""
pages/admin.py
--------------
Admin panel: Document Library, Index Statistics, Query Analytics, Session Browser.
Accessible only to users with the "admin" role.
"""

import json
import logging
from datetime import datetime
from pathlib import Path

import streamlit as st

from config import Config
from utils.styles import CUSTOM_CSS, ANIMATED_BG
from utils.auth import require_auth, render_sign_out
from utils.history import (
    get_all_sessions,
    get_recent_queries,
    get_session_history,
    get_total_questions,
    delete_session,
)
from utils.embeddings import (
    build_vector_store,
    index_exists,
    load_vector_store,
    reset_vector_store,
)
from utils.loader import load_documents_from_directory
from utils.splitter import split_documents

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Admin Panel — Enterprise Chatbot",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90'>◈</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject CSS + animated background
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.markdown(ANIMATED_BG, unsafe_allow_html=True)

# ── Authentication gate (admin only) ──────────────────────────────────────────
require_auth(allowed_roles=("admin",))

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
    st.markdown("## Admin Panel")
    st.markdown("---")
    render_sign_out()
    st.page_link("app.py", label="Back to chat")

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="rag-header">
  <h1>Admin Panel</h1>
</div>
<p class="rag-tagline">
  Manage documents, monitor queries, and browse sessions.
</p>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 1 — Document Library
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="admin-section">', unsafe_allow_html=True)
st.markdown("### Document Library")

docs_dir = Config.DOCS_DIR
chunk_counts = _load_chunk_counts()

if docs_dir.exists():
    files = sorted(f for f in docs_dir.iterdir() if f.is_file())
else:
    files = []

if files:
    import pandas as pd

    rows = []
    for f in files:
        stat = f.stat()
        size_kb = stat.st_size / 1024
        mtime = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        chunks = chunk_counts.get(f.name, "—")
        rows.append({
            "Filename": f.name,
            "Type": f.suffix.lower(),
            "Size (KB)": f"{size_kb:.1f}",
            "Uploaded": mtime,
            "Chunks": chunks,
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Per-file delete buttons
    st.markdown("")
    delete_col1, delete_col2 = st.columns([3, 1])
    with delete_col1:
        file_to_delete = st.selectbox(
            "Select file to delete",
            options=[f.name for f in files],
            key="admin_delete_select",
            label_visibility="collapsed",
            placeholder="Select a file to delete...",
        )
    with delete_col2:
        if st.button("Delete file", key="btn_admin_delete", use_container_width=True):
            if file_to_delete:
                # 1. Remove file
                target = docs_dir / file_to_delete
                if target.exists():
                    target.unlink()
                    logger.info("Deleted file: %s", file_to_delete)

                # 2. Update chunk counts
                if file_to_delete in chunk_counts:
                    del chunk_counts[file_to_delete]
                    _save_chunk_counts(chunk_counts)

                # 3. Reset and re-index remaining files
                reset_vector_store()
                remaining = [f for f in docs_dir.iterdir() if f.is_file() and f.suffix.lower() != ".db"]
                if remaining:
                    with st.spinner("Re-indexing remaining documents..."):
                        documents = load_documents_from_directory(docs_dir)
                        if documents:
                            chunks_list = split_documents(documents)
                            vs = build_vector_store(chunks_list)
                            st.session_state.vector_store = vs
                            # Rebuild chunk counts
                            new_counts = {}
                            for r in remaining:
                                file_chunks = [c for c in chunks_list if c.metadata.get("source") == r.name]
                                new_counts[r.name] = len(file_chunks)
                            _save_chunk_counts(new_counts)
                        else:
                            st.session_state.vector_store = None
                else:
                    st.session_state.vector_store = None
                    _save_chunk_counts({})

                # 4. Update kb_doc_names
                if "kb_doc_names" in st.session_state:
                    st.session_state.kb_doc_names.discard(file_to_delete)

                st.success(f"Deleted '{file_to_delete}' and re-indexed.")
                st.rerun()
else:
    st.caption("No documents in the library.")

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 2 — Index Statistics
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="admin-section">', unsafe_allow_html=True)
st.markdown("### Index Statistics")

total_docs = len(files)
total_chunks = sum(v for v in chunk_counts.values() if isinstance(v, int))
idx_exists = index_exists()

cols = st.columns(3)
cols[0].metric("Documents loaded", total_docs)
cols[1].metric("Chunks indexed", total_chunks)
with cols[2]:
    if idx_exists:
        st.markdown(
            '<span class="admin-badge-ready">Ready</span>',
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            '<span class="admin-badge-pending">Not indexed</span>',
            unsafe_allow_html=True,
        )

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 3 — Query Analytics
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="admin-section">', unsafe_allow_html=True)
st.markdown("### Query Analytics")

total_q = get_total_questions()
st.metric("Total questions asked", total_q)

recent = get_recent_queries(limit=20)
if recent:
    import pandas as pd

    rows = []
    for r in recent:
        rows.append({
            "Timestamp": r["timestamp"],
            "Session": r["session_id"][:8] + "...",
            "Question": (r["question"][:80] + "...") if len(r["question"]) > 80 else r["question"],
            "Response (s)": f"{r['response_time_seconds']:.2f}" if r["response_time_seconds"] else "—",
            "Feedback": r.get("feedback") or "—",
        })

    df = pd.DataFrame(rows)
    st.dataframe(df, use_container_width=True, hide_index=True)
else:
    st.caption("No queries recorded yet.")

st.markdown("</div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# Section 4 — Session Browser
# ══════════════════════════════════════════════════════════════════════════════
st.markdown('<div class="admin-section">', unsafe_allow_html=True)
st.markdown("### Session Browser")

sessions = get_all_sessions()
if sessions:
    import pandas as pd

    session_rows = []
    session_ids = []
    for s in sessions:
        session_ids.append(s["session_id"])
        session_rows.append({
            "Session ID": s["session_id"],
            "Turns": s["turn_count"],
            "Last active": s["last_timestamp"],
        })

    df = pd.DataFrame(session_rows)
    st.dataframe(df, use_container_width=True, hide_index=True)

    # Session detail viewer
    selected = st.selectbox(
        "View session details",
        options=session_ids,
        key="admin_session_select",
        placeholder="Select a session...",
    )

    if selected:
        history = get_session_history(selected)
        if history:
            for h in history:
                st.markdown(f"**Q:** {h['question']}")
                st.markdown(f"**A:** {h['answer'][:200]}{'...' if len(h['answer']) > 200 else ''}")
                feedback = h.get("feedback") or "none"
                st.caption(
                    f"{h['timestamp']}  ·  "
                    f"{h.get('response_time_seconds', 0):.2f}s  ·  "
                    f"feedback: {feedback}"
                )
                st.divider()

        if st.button("Delete this session", key="btn_delete_session"):
            delete_session(selected)
            st.success(f"Session '{selected}' deleted.")
            st.rerun()
else:
    st.caption("No sessions recorded yet.")

st.markdown("</div>", unsafe_allow_html=True)
