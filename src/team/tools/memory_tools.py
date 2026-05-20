import chromadb
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Optional

class MemoryRetrievalSchema(BaseModel):
    query: str = Field(
        ..., 
        description="The semantic search query to find relevant past project context, meeting notes, or user requirements."
    )
    collection_name: str = Field(
        default="project_memory",
        description="The ChromaDB collection to search in. E.g., 'user_interviews', 'past_prds', 'architecture_decisions'."
    )
    n_results: int = Field(
        default=3,
        description="Number of relevant documents to retrieve. Keep low (1-3) to save tokens."
    )

class ChromaMemoryRetrievalTool(BaseTool):
    name: str = "project_memory_retrieval"
    description: str = (
        "Semantic search tool to retrieve past project decisions, user feedback, meeting notes, "
        "and previous PRDs from the local vector database."
    )
    args_schema: type[BaseModel] = MemoryRetrievalSchema

    def _run(self, query: str, collection_name: str = "project_memory", n_results: int = 3) -> str:
        try:
            client = chromadb.PersistentClient(path="./chroma_db")
            
            try:
                collection = client.get_collection(name=collection_name)
            except ValueError:
                return f"No memory collection found named '{collection_name}'."

            results = collection.query(
                query_texts=[query],
                n_results=n_results
            )

            if not results.get('documents') or not results['documents'][0]:
                return f"No relevant memories found for query: '{query}'."

            output = []
            for i, doc in enumerate(results['documents'][0]):
                meta = results['metadatas'][0][i] if results.get('metadatas') else "No Metadata"
                distance = results['distances'][0][i] if results.get('distances') else "N/A"
                
                output.append(f"--- Memory {i+1} (Relevance Score: {distance}) ---\nMetadata: {meta}\nContent: {doc}\n")

            return "\n".join(output)

        except Exception as e:
            return f"Memory retrieval failed. Error: {str(e)}"