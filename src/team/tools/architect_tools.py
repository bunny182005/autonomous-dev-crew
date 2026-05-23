from pathlib import Path

from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from tools.workspace import PROJECT_DIR


# =========================================================
# ARCHITECTURE TOOL
# =========================================================

class ArchitectureSchema(BaseModel):

    system_name: str = Field(
        ...,
        description="Name of the system or microservice."
    )

    architecture_markdown: str = Field(
        ...,
        description="Complete architecture document text including Mermaid.js diagrams."
    )


class ArchitectureGeneratorTool(BaseTool):

    name: str = "architecture_generator"

    description: str = """
    Generates architecture design documents safely inside workspace.
    """

    args_schema: type[BaseModel] = ArchitectureSchema

    def _run(
        self,
        system_name: str,
        architecture_markdown: str
    ) -> str:

        try:

            docs_dir = PROJECT_DIR / "docs" / "architecture"

            docs_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                docs_dir /
                f"{system_name.lower().replace(' ', '_')}_architecture.md"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(architecture_markdown)

            return f"""
Architecture document saved successfully.

PATH:
{filename}
"""

        except Exception as e:

            return f"""
Failed to save architecture design.

ERROR:
{str(e)}
"""


# =========================================================
# DATABASE SCHEMA TOOL
# =========================================================

class DbSchemaInput(BaseModel):

    schema_name: str = Field(
        ...,
        description="Name of the database schema file."
    )

    sql_ddl: str = Field(
        ...,
        description="Raw PostgreSQL DDL SQL script."
    )


class DatabaseSchemaTool(BaseTool):

    name: str = "database_schema_generator"

    description: str = """
    Generates database schemas safely inside workspace.
    """

    args_schema: type[BaseModel] = DbSchemaInput

    def _run(
        self,
        schema_name: str,
        sql_ddl: str
    ) -> str:

        try:

            db_dir = PROJECT_DIR / "docs" / "database"

            db_dir.mkdir(parents=True, exist_ok=True)

            filename = (
                db_dir /
                f"{schema_name.lower().replace(' ', '_')}.sql"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(sql_ddl)

            return f"""
Database schema saved successfully.

PATH:
{filename}
"""

        except Exception as e:

            return f"""
Failed to save database schema.

ERROR:
{str(e)}
"""


# =========================================================
# API DESIGN TOOL
# =========================================================

class ApiDesignInput(BaseModel):

    file_name: str = Field(
        ...,
        description="Name of the API spec file."
    )

    spec_content: str = Field(
        ...,
        description="The OpenAPI YAML specification or routing markdown."
    )


class ApiDesignTool(BaseTool):

    name: str = "api_design_generator"

    description: str = """
    Generates API specifications safely inside workspace.
    """

    args_schema: type[BaseModel] = ApiDesignInput

    def _run(
        self,
        file_name: str,
        spec_content: str
    ) -> str:

        try:

            api_dir = PROJECT_DIR / "docs" / "api"

            api_dir.mkdir(parents=True, exist_ok=True)

            ext = (
                "yaml"
                if "paths:" in spec_content.lower()
                else "md"
            )

            filename = (
                api_dir /
                f"{file_name.lower().replace(' ', '_')}_api.{ext}"
            )

            with open(filename, "w", encoding="utf-8") as f:
                f.write(spec_content)

            return f"""
API specification saved successfully.

PATH:
{filename}
"""

        except Exception as e:

            return f"""
Failed to save API specification.

ERROR:
{str(e)}
"""