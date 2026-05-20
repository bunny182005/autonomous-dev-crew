from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from duckduckgo_search import DDGS
from typing import Optional

class DDGSearchSchema(BaseModel):
    query: str = Field(
        ..., 
        description="The search query. Supports DuckDuckGo operators like 'site:competitor.com', 'filetype:pdf', '\"exact phrase\"', and '-exclusion'."
    )
    search_type: str = Field(
        default="text", 
        description="Type of search. Use 'text' for general web search, or 'news' for current market events and PR."
    )
    max_results: int = Field(
        default=5, 
        description="Number of results to fetch (default 5). Keep under 10 to avoid rate limits and save tokens."
    )
    timelimit: Optional[str] = Field(
        default=None, 
        description="Time filter for recent data. Options: 'd' (day), 'w' (week), 'm' (month), 'y' (year). Leave null for all time."
    )

class AdvancedDDGSearchTool(BaseTool):
    name: str = "advanced_market_research_search"
    description: str = (
        "An advanced web search tool using DuckDuckGo. Use this to conduct competitor analysis, "
        "find industry PDF reports, lookup API documentation, and pull the latest product news."
    )
    args_schema: type[BaseModel] = DDGSearchSchema

    def _run(self, query: str, search_type: str = "text", max_results: int = 5, timelimit: Optional[str] = None) -> str:
        try:
            results = []
            # Initialize the DuckDuckGo search client
            with DDGS() as ddgs:
                if search_type.lower() == "news":
                    # Fetch news articles (requires max_results as a keyword argument)
                    search_gen = ddgs.news(query, timelimit=timelimit, max_results=max_results)
                else:
                    # Fetch standard web/text results
                    search_gen = ddgs.text(query, timelimit=timelimit, max_results=max_results)
                
                # Convert the generator to a list
                results = list(search_gen)

            if not results:
                return f"No results found for query: '{query}'."

            # Format the output into clean, token-efficient text for the LLM
            output = []
            for i, res in enumerate(results, 1):
                title = res.get('title', 'No Title')
                link = res.get('href', res.get('url', 'No Link'))
                snippet = res.get('body', res.get('summary', 'No Snippet'))
                
                output.append(f"Result {i}:\nTitle: {title}\nURL: {link}\nSummary: {snippet}\n")

            return "\n".join(output)

        except Exception as e:
            return f"Search failed. Error: {str(e)}. Try reducing max_results or waiting a moment before retrying."