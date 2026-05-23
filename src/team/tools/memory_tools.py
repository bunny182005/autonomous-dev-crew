from typing import Optional

import chromadb

from chromadb.utils.embedding_functions import (
    SentenceTransformerEmbeddingFunction
)

from crewai.tools import BaseTool

from pydantic import BaseModel, Field

from tools.workspace import PROJECT_DIR


# =========================================================
# LOCAL EMBEDDING MODEL
# =========================================================

embedding_function = SentenceTransformerEmbeddingFunction(
    model_name="all-MiniLM-L6-v2"
)


# =========================================================
# MEMORY SCHEMA
# =========================================================

class MemoryRetrievalSchema(BaseModel):

    query: str = Field(
        ...,
        description="Semantic search query."
    )

    collection_name: str = Field(
        default="project_memory",
        description="Target ChromaDB collection."
    )

    n_results: int = Field(
        default=3,
        description="Number of memories to retrieve."
    )


# =========================================================
# MEMORY TOOL
# =========================================================

class ChromaMemoryRetrievalTool(BaseTool):

    name: str = "project_memory_retrieval"

    description: str = """
    Retrieves semantic project memory using local embeddings.
    """

    args_schema: type[BaseModel] = MemoryRetrievalSchema

    def _run(
        self,
        query: str,
        collection_name: str = "project_memory",
        n_results: int = 3
    ) -> str:

        try:

            # =============================================
            # CHROMA STORAGE INSIDE WORKSPACE
            # =============================================

            chroma_path = PROJECT_DIR / "memory_db"

            client = chromadb.PersistentClient(
                path=str(chroma_path)
            )

            # =============================================
            # GET COLLECTION
            # =============================================

            try:

                collection = client.get_collection(
                    name=collection_name,
                    embedding_function=embedding_function
                )

            except Exception:

                return (
                    f"No memory collection found named "
                    f"'{collection_name}'."
                )

            # =============================================
            # QUERY MEMORY
            # =============================================

            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )

            documents = results.get("documents")

            if not documents or not documents[0]:

                return (
                    f"No relevant memories found for:\n{query}"
                )

            # =============================================
            # FORMAT OUTPUT
            # =============================================

            output = []

            for i, doc in enumerate(documents[0]):

                metadata = (
                    results["metadatas"][0][i]
                    if results.get("metadatas")
                    else {}
                )

                distance = (
                    results["distances"][0][i]
                    if results.get("distances")
                    else "N/A"
                )

                output.append(
                    f"""
MEMORY {i+1}
----------------------------------------
Relevance Score: {distance}

Metadata:
{metadata}

Content:
{doc}
"""
                )

            return "\n".join(output)

        except Exception as e:

            return f"""
Memory retrieval failed.

ERROR:
{str(e)}
"""