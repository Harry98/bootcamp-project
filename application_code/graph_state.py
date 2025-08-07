import operator
from typing import TypedDict, Dict, List, Any, Annotated


class RAGState(TypedDict):
    session_id: str
    user_query: str
    confluence_response: List[Dict] | None
    filtered_pages: List[str] | None
    vector_db_response: List[Any] | None
    answer: str | None
    cql_queries: List[str] | None
    token_usage: Any | None
