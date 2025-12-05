from langchain_community.tools import TavilySearchResults
from langchain_core.tools import tool
# WebSearch
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import DuckDuckGoSearchRun
from app.shared.security.credential_manager import credential_manager


'''
@tool("web_search", description="Permette di cercare informazioni aggiornate su internet")
def web_search_tool(query: str) -> str:
    """Permette di cercare informazioni aggiornate su internet"""

    tavily_key = credential_manager.get_tavily_api_key()

    if tavily_key:
        # Crea e ESEGUI la ricerca con Tavily
        search_tool = TavilySearchResults(
            max_results=3,
            tavily_api_key=tavily_key
        )
        return search_tool.invoke(query)
    else:
        # Fallback: DuckDuckGo
        print("⚠️ Tavily Key non trovata. Uso DuckDuckGo per la ricerca.")
        search_tool = DuckDuckGoSearchRun()
        return search_tool.invoke(query)
'''


