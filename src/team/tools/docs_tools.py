import os
import yaml
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from tools.workspace import PROJECT_DIR

class MarkdownGeneratorSchema(BaseModel):
    filepath: str = Field(..., description="The target path to save the documentation (e.g., 'README.md', 'docs/setup_guide.md').")
    content: str = Field(..., description="The complete, well-formatted Markdown string containing the documentation.")

class MarkdownGeneratorTool(BaseTool):
    name: str = "markdown_generator_tool"
    description: str = "Generates, formats, and saves pristine technical Markdown documentation directly to the local filesystem."
    args_schema: type[BaseModel] = MarkdownGeneratorSchema

    def _run(self, filepath: str, content: str) -> str:
        try:
            full_path = (PROJECT_DIR / filepath).resolve()

            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Outside workspace."
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
                
            return f"Documentation successfully saved to {filepath}"
        except Exception as e:
            return f"Failed to save Markdown document. Error: {str(e)}"

class OpenApiDocSchema(BaseModel):
    filepath: str = Field(..., description="The target path to save the OpenAPI specification (e.g., 'docs/openapi.yaml').")
    spec_content: str = Field(..., description="The complete OpenAPI 3.0 or Swagger specification payload in YAML format.")

class OpenApiDocTool(BaseTool):
    name: str = "openapi_doc_tool"
    description: str = "Generates, structurally validates, and saves OpenAPI 3.0/Swagger YAML specifications to disk."
    args_schema: type[BaseModel] = OpenApiDocSchema

    def _run(self, filepath: str, spec_content: str) -> str:
        try:
            # 1. Structural dry-run: Ensure the LLM didn't hallucinate invalid YAML syntax
            yaml.safe_load(spec_content)
            
            # 2. Save the validated payload
            full_path = (PROJECT_DIR / filepath).resolve()

            if not str(full_path).startswith(str(PROJECT_DIR.resolve())):
                return "Blocked: Outside workspace."
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(spec_content)
                
            return f"Validation Success: OpenAPI spec is structurally valid and saved to {filepath}."
        except yaml.YAMLError as exc:
            return f"Validation Failed: The generated OpenAPI payload contains invalid YAML syntax. Fix the formatting and try again.\nDetails: {str(exc)}"
        except Exception as e:
            return f"Failed to save OpenAPI specification. Error: {str(e)}"