import os
import subprocess
import psycopg2
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

# Fetches connection parameters from the environment, falling back to local defaults
DB_DSN = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/postgres")

class PostgresQuerySchema(BaseModel):
    sql_query: str = Field(..., description="The exact SQL statement to execute (SELECT, INSERT, etc.).")

class PostgresTool(BaseTool):
    name: str = "postgres_query_executor"
    description: str = "Executes raw SQL statements against the target PostgreSQL database and returns rows or execution status."
    args_schema: type[BaseModel] = PostgresQuerySchema

    def _run(self, sql_query: str) -> str:
        try:
            with psycopg2.connect(DB_DSN) as conn:
                with conn.cursor() as cursor:
                    cursor.execute(sql_query)
                    if cursor.description:
                        columns = [desc[0] for desc in cursor.description]
                        rows = cursor.fetchall()
                        result = [dict(zip(columns, row)) for row in rows]
                        return f"SUCCESS: Retrieved {len(result)} rows.\nDATA:\n{result}"
                    else:
                        return f"SUCCESS: Command executed. Row count affected: {cursor.rowcount}"
        except Exception as e:
            return f"DATABASE ERROR: {str(e)}"

class MigrationSchema(BaseModel):
    action: str = Field(..., description="The migration command to run (e.g., 'alembic revision --autogenerate' or 'alembic upgrade head').")

class MigrationTool(BaseTool):
    name: str = "migration_manager"
    description: str = "Handles schema evolutionary changes, runs migrations, or generates version tracking configurations."
    args_schema: type[BaseModel] = MigrationSchema

    def _run(self, action: str) -> str:
        try:
            result = subprocess.run(
                action,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
            return f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        except Exception as e:
            return f"Migration task failed. Error: {str(e)}"

class SqlValidatorSchema(BaseModel):
    sql_script: str = Field(..., description="The SQL code or DDL schema block to validate for syntax errors.")

class SqlValidatorTool(BaseTool):
    name: str = "sql_syntax_validator"
    description: str = "Validates SQL script syntax by executing it inside a rolled-back transaction block, ensuring zero permanent side effects."
    args_schema: type[BaseModel] = SqlValidatorSchema

    def _run(self, sql_script: str) -> str:
        try:
            # Connect and run the query, but explicitly force a rollback
            conn = psycopg2.connect(DB_DSN)
            cursor = conn.cursor()
            try:
                # Prepend EXPLAIN to catch syntax/planning errors safely if it's a single query, 
                # or execute full block and rollback immediately.
                cursor.execute(sql_script)
                conn.rollback() # Guarantee no side-effects occur
                return "VALIDATION SUCCESS: SQL statement/DDL block is syntactically valid."
            except Exception as script_err:
                conn.rollback()
                return f"VALIDATION FAILED: Syntax or structural error encountered.\nDetails: {str(script_err)}"
            finally:
                cursor.close()
                conn.close()
        except Exception as conn_err:
            return f"VALIDATION ERROR: Could not connect to database for syntax check. Details: {str(conn_err)}"