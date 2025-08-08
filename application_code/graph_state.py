from typing import TypedDict, Dict, List, Any, Annotated


def dict_or_merge(old: Dict, new: Dict) -> Dict:
    return {k: old.get(k) or new.get(k) for k in set(old) | set(new)}


class RAGState(TypedDict):
    session_id: str
    user_query: str
    confluence_response: Dict | None
    filtered_pages: List[str] | None
    vector_db_response: List[Any] | None
    answer: str | None
    cql_queries: List[str] | None
    page_map: Annotated[Dict, dict_or_merge]
