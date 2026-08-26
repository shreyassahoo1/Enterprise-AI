"""
utils/sql_agent.py
------------------
Text-to-SQL agent for answering questions about uploaded SQLite databases.
Generates read-only SELECT queries via GPT-4o and executes them safely.
"""

import logging
import re
import sqlite3
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# SQL keywords that are NOT allowed in generated queries
_FORBIDDEN_KEYWORDS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|ATTACH)\b",
    re.IGNORECASE,
)


class SQLAgent:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self._schema_cache: Optional[str] = None

    def get_schema(self) -> str:
        """Return CREATE TABLE statements for all tables as a string."""
        if self._schema_cache is not None:
            return self._schema_cache
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.execute(
                "SELECT sql FROM sqlite_master WHERE type='table' AND sql IS NOT NULL"
            )
            statements = [row[0] for row in cursor.fetchall()]
            conn.close()
            self._schema_cache = "\n\n".join(statements)
            return self._schema_cache
        except Exception as exc:
            logger.error("Failed to read schema from '%s': %s", self.db_path, exc)
            return ""

    def _validate_sql(self, sql: str) -> Optional[str]:
        """
        Validate that the SQL is a safe, read-only SELECT statement.
        Returns an error message if invalid, None if valid.
        """
        cleaned = sql.strip().rstrip(";").strip()
        if not cleaned:
            return "Empty SQL query."

        # Check for forbidden keywords
        match = _FORBIDDEN_KEYWORDS.search(cleaned)
        if match:
            return f"Forbidden SQL keyword detected: {match.group(0)}"

        # Check for multiple statements (semicolons in the middle)
        # Remove string literals first to avoid false positives
        no_strings = re.sub(r"'[^']*'", "", cleaned)
        no_strings = re.sub(r'"[^"]*"', "", no_strings)
        if ";" in no_strings:
            return "Multiple SQL statements are not allowed."

        return None

    def ask(self, question: str) -> Dict[str, Any]:
        """
        Generate and execute a read-only SQL query for the given question.

        Returns:
            {"sql": str, "rows": list, "columns": list, "error": str|None}
        """
        schema = self.get_schema()
        if not schema:
            return {
                "sql": "",
                "rows": [],
                "columns": [],
                "error": "Could not read the database schema.",
            }

        # Build prompt for GPT-4o
        prompt_text = (
            "You are a SQL expert. Given the following SQLite database schema, "
            "generate a single read-only SELECT SQL query that answers the "
            "user's question. Return ONLY the SQL query, nothing else. "
            "Do not include any explanation, markdown formatting, or code fences.\n\n"
            f"Schema:\n{schema}\n\n"
            f"Question: {question}\n\n"
            "SQL:"
        )

        # Generate SQL using the project's LLM
        try:
            from chatbot.llm import get_llm
            from langchain_core.messages import HumanMessage

            llm = get_llm()
            result = llm.invoke([HumanMessage(content=prompt_text)])
            sql = result.content.strip()
            # Clean up markdown code fences if present
            if sql.startswith("```"):
                sql = re.sub(r"^```(?:sql)?\s*", "", sql)
                sql = re.sub(r"\s*```$", "", sql)
            sql = sql.strip()
        except Exception as exc:
            logger.error("Failed to generate SQL: %s", exc)
            return {
                "sql": "",
                "rows": [],
                "columns": [],
                "error": f"Failed to generate SQL: {exc}",
            }

        # Validate the generated SQL
        validation_error = self._validate_sql(sql)
        if validation_error:
            logger.warning("SQL validation failed: %s — query: %s", validation_error, sql)
            return {
                "sql": sql,
                "rows": [],
                "columns": [],
                "error": validation_error,
            }

        # Execute the query with a 10-second timeout
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            conn.execute("PRAGMA query_only = ON")
            cursor = conn.execute(sql)
            columns = [desc[0] for desc in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            conn.close()
            logger.info("SQL query executed successfully: %d row(s) returned", len(rows))
            return {
                "sql": sql,
                "rows": [list(r) for r in rows],
                "columns": columns,
                "error": None,
            }
        except Exception as exc:
            logger.error("SQL execution failed: %s — query: %s", exc, sql)
            return {
                "sql": sql,
                "rows": [],
                "columns": [],
                "error": f"Query execution failed: {exc}",
            }
