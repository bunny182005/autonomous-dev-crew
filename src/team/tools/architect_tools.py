import os
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class ArchitectureSchema(BaseModel):
    system_name: str = Field(..., description="Name of the system or microservice.")
    architecture_markdown: str = Field(..., description="Complete architecture document text including Mermaid.js diagrams.")

class ArchitectureGeneratorTool(BaseTool):
    name: str = "architecture_generator"
    description: str = "Generates and saves architectural design documents and Mermaid.js diagrams to disk."
    args_schema: type[BaseModel] = ArchitectureSchema

    def _run(self, system_name: str, architecture_markdown: str) -> str:
        try:
            os.makedirs("./docs/architecture", exist_ok=True)
            filename = f"./docs/architecture/{system_name.lower().replace(' ', '_')}_architecture.md"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(architecture_markdown)
            return f"Architecture design document successfully saved to {filename}"
        except Exception as e:
            return f"Failed to save architecture design. Error: {str(e)}"

class DbSchemaInput(BaseModel):
    schema_name: str = Field(..., description="Name of the database schema file.")
    sql_ddl: str = Field(..., description="Raw PostgreSQL DDL SQL script.")

class DatabaseSchemaTool(BaseTool):
    name: str = "database_schema_generator"
    description: str = "Generates and saves production-ready PostgreSQL SQL DDL schema blueprints to disk."
    args_schema: type[BaseModel] = DbSchemaInput

    def _run(self, schema_name: str, sql_ddl: str) -> str:
        try:
            os.makedirs("./docs/database", exist_ok=True)
            filename = f"./docs/database/{schema_name.lower().replace(' ', '_')}.sql"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(sql_ddl)
            return f"Database DDL schema successfully saved to {filename}"
        except Exception as e:
            return f"Failed to save database schema. Error: {str(e)}"

class ApiDesignInput(BaseModel):
    file_name: str = Field(..., description="Name of the API spec file.")
    spec_content: str = Field(..., description="The OpenAPI 3.0 YAML specification or routing table markdown.")

class ApiDesignTool(BaseTool):
    name: str = "api_design_generator"
    description: str = "Generates and saves OpenAPI specification files or API routing maps to disk."
    args_schema: type[BaseModel] = ApiDesignInput

    def _run(self, file_name: str, spec_content: str) -> str:
        try:
            os.makedirs("./docs/api", exist_ok=True)
            ext = "yaml" if "paths:" in spec_content.lower() else "md"
            filename = f"./docs/api/{file_name.lower().replace(' ', '_')}_api.{ext}"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(spec_content)
            return f"API specification successfully saved to {filename}"
        except Exception as e:
            return f"Failed to save API specification. Error: {str(e)}"