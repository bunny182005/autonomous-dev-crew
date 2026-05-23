"""
tools/memory_writer.py

FIX: The `metadata` parameter was accepted but completely ignored.
     collection.add() always stored {"source": "crew_agent"} regardless
     of what the caller passed. Now parses and merges the JSON string.
"""

import json
import uuid

import chromadb

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

from crewai.tools import BaseTool

from pydantic import BaseModel, Field

from tools.workspace import PROJECT_DIR


# =========================================================
# LOCAL EMBEDDINGS
# =========================================================

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


# =========================================================
# MEMORY WRITE SCHEMA
# =========================================================

class MemoryWriteSchema(BaseModel):

    content: str = Field(
        ...,
        description="Memory content to store."
    )

    collection_name: str = Field(
        default="project_memory",
        description="Target collection."
    )

    metadata: str = Field(
        default="{}",
        description="Optional metadata JSON string, e.g. '{\"agent\": \"auth_engineer\"}'."
    )


# =========================================================
# MEMORY WRITER TOOL
# =========================================================

class ChromaMemoryWriteTool(BaseTool):

    name: str = "project_memory_writer"

    description: str = """
    Stores semantic project memory locally using ChromaDB.
    Pass metadata as a JSON string to tag memories by agent or task.
    """

    args_schema: type[BaseModel] = MemoryWriteSchema

    def _run(
        self,
        content: str,
        collection_name: str = "project_memory",
        metadata: str = "{}"
    ) -> str:

        try:
            # FIX: parse the metadata string the caller actually provided
            try:
                parsed_metadata = json.loads(metadata)
                if not isinstance(parsed_metadata, dict):
                    parsed_metadata = {}
            except (json.JSONDecodeError, TypeError):
                parsed_metadata = {}

            # Always include a source tag alongside whatever the caller sent
            parsed_metadata.setdefault("source", "crew_agent")

            chroma_path = PROJECT_DIR / "memory_db"

            client = chromadb.PersistentClient(
                path=str(chroma_path)
            )

            collection = client.get_or_create_collection(
                name=collection_name,
                embedding_function=embedding_function
            )

            memory_id = str(uuid.uuid4())

            collection.add(
                ids=[memory_id],
                documents=[content],
                metadatas=[parsed_metadata]   # FIX: was always {"source": "crew_agent"}
            )

            return f"""
Memory stored successfully.

ID: {memory_id}
Metadata: {json.dumps(parsed_metadata)}
"""

        except Exception as e:

            return f"""
Memory storage failed.

ERROR:
{str(e)}
"""