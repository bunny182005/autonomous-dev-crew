"""
tools/database_tools.py

FIX: MigrationTool.ALLOWED_ACTIONS was a plain list on a Pydantic model.
     Pydantic tried to validate it as a field and raised ValidationError on
     import. Added `ClassVar` annotation to match the pattern used correctly
     in backend_tools.py.
"""

import os
import subprocess

from typing import ClassVar

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from tools.workspace import PROJECT_DIR


# =========================================================
# POSTGRES TOOL
# =========================================================

class PostgresCommandSchema(BaseModel):
    sql: str = Field(
        ...,
        description=(
            "A single SQL statement to execute against the database "
            "(e.g., 'SELECT 1', 'SHOW TABLES', 'SELECT count(*) FROM users')."
        ),
    )
    database_url: str = Field(
        default="",
        description=(
            "Optional DATABASE_URL override. If empty, reads from "
            "DATABASE_URL environment variable."
        ),
    )


class PostgresTool(BaseTool):
    name: str = "postgres_executor"
    description: str = (
        "Executes a SQL statement against the PostgreSQL database using psql. "
        "Use for schema validation, health checks, and query testing. "
        "Does NOT run migrations — use migration_tool for that."
    )
    args_schema: type[BaseModel] = PostgresCommandSchema

    def _run(self, sql: str, database_url: str = "") -> str:
        try:
            url = database_url or os.environ.get("DATABASE_URL", "")
            if not url:
                return (
                    "Error: No DATABASE_URL set. "
                    "Set the environment variable or pass database_url explicitly."
                )

            dangerous = ["DROP TABLE", "DROP DATABASE", "TRUNCATE", "DELETE FROM"]
            for stmt in dangerous:
                if stmt.upper() in sql.upper():
                    return (
                        f"Blocked: '{stmt}' is not allowed in PostgresTool. "
                        "Use MigrationTool for schema changes."
                    )

            result = subprocess.run(
                ["psql", url, "-c", sql],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=PROJECT_DIR,
            )
            if result.returncode == 0:
                return f"SUCCESS:\n{result.stdout}"
            return f"ERROR:\n{result.stderr}"
        except FileNotFoundError:
            return (
                "psql not found. The database host may not be running yet. "
                "This is expected during code generation — the schema will be "
                "applied when Docker Compose starts."
            )
        except Exception as e:
            return f"PostgresTool failed: {str(e)}"


# =========================================================
# MIGRATION TOOL
# FIX: ALLOWED_ACTIONS must be ClassVar or Pydantic raises ValidationError
# =========================================================

class MigrationSchema(BaseModel):
    action: str = Field(
        ...,
        description=(
            "Alembic subcommand to run. Examples: "
            "'upgrade head', "
            "'revision --autogenerate -m add_users_table', "
            "'downgrade -1', "
            "'current', "
            "'history --verbose'."
        ),
    )


class MigrationTool(BaseTool):
    name: str = "migration_tool"
    description: str = (
        "Manages Alembic database migrations. Run 'upgrade head' to apply all migrations, "
        "'revision --autogenerate -m <message>' to generate a new migration from model changes, "
        "'downgrade -1' to roll back one step."
    )
    args_schema: type[BaseModel] = MigrationSchema

    # FIX: was a plain list — Pydantic tried to validate it as a model field
    ALLOWED_ACTIONS: ClassVar[list[str]] = [
        "upgrade",
        "downgrade",
        "revision",
        "current",
        "history",
        "heads",
        "branches",
        "show",
        "stamp",
    ]

    def _run(self, action: str) -> str:
        try:
            action = action.strip()
            first_word = action.split()[0].lower()

            if first_word not in self.ALLOWED_ACTIONS:
                return (
                    f"Blocked: '{first_word}' is not a recognized Alembic command. "
                    f"Allowed: {', '.join(self.ALLOWED_ACTIONS)}"
                )

            backend_dir = PROJECT_DIR / "backend"
            if not (backend_dir / "alembic.ini").exists():
                return (
                    "alembic.ini not found in backend/. "
                    "Write alembic.ini and alembic/env.py first before running migrations."
                )

            result = subprocess.run(
                f"alembic {action}",
                shell=True,
                capture_output=True,
                text=True,
                timeout=60,
                cwd=backend_dir,
            )

            output = f"COMMAND: alembic {action}\n\nSTDOUT:\n{result.stdout}"
            if result.stderr:
                output += f"\nSTDERR:\n{result.stderr}"
            return output

        except subprocess.TimeoutExpired:
            return "Migration timed out after 60 seconds."
        except Exception as e:
            return f"MigrationTool failed: {str(e)}"


# =========================================================
# SQL VALIDATOR TOOL
# =========================================================

class SqlValidatorSchema(BaseModel):
    sql: str = Field(
        ...,
        description=(
            "The SQL DDL or DML string to validate for syntax correctness. "
            "Supports PostgreSQL dialect."
        ),
    )


class SqlValidatorTool(BaseTool):
    name: str = "sql_validator"
    description: str = (
        "Validates SQL syntax without executing it against a live database. "
        "Use before writing migration files to catch syntax errors early."
    )
    args_schema: type[BaseModel] = SqlValidatorSchema

    def _run(self, sql: str) -> str:
        try:
            try:
                import sqlparse  # type: ignore

                parsed = sqlparse.parse(sql.strip())
                if not parsed or not parsed[0].tokens:
                    return "SQL Validation FAILED: Empty or unparseable SQL."

                statement_count = len(parsed)
                statement_types = [
                    str(stmt.get_type()) for stmt in parsed if stmt.get_type()
                ]

                return (
                    f"SQL Validation PASSED.\n"
                    f"Statements parsed: {statement_count}\n"
                    f"Statement types: {', '.join(statement_types) or 'mixed/unknown'}"
                )

            except ImportError:
                pass

            sql_upper = sql.upper().strip()
            ddl_keywords = ["CREATE", "ALTER", "DROP", "INSERT", "UPDATE", "DELETE", "SELECT"]
            found = [kw for kw in ddl_keywords if kw in sql_upper]

            if not found:
                return (
                    "SQL Validation WARNING: No recognizable SQL keywords found. "
                    "Install sqlparse for full validation: pip install sqlparse"
                )

            issues = []
            if "VARCHAR" in sql_upper and "VARCHAR(" not in sql_upper:
                issues.append("VARCHAR without length limit — consider VARCHAR(255) or TEXT")
            if "SERIAL" in sql_upper:
                issues.append(
                    "SERIAL is deprecated in PostgreSQL 10+ — prefer "
                    "INTEGER GENERATED ALWAYS AS IDENTITY"
                )

            result = f"SQL Validation PASSED (basic check).\nKeywords found: {', '.join(found)}"
            if issues:
                result += f"\n\nAdvisories:\n" + "\n".join(f"- {i}" for i in issues)
            result += "\n\nTip: pip install sqlparse for full syntax validation."
            return result

        except Exception as e:
            return f"SqlValidatorTool failed: {str(e)}"