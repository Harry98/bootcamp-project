import os
import asyncio
import json
from collections import Counter
from contextlib import asynccontextmanager
from typing import List, Dict
from langfuse import observe
from langchain_mcp_adapters.client import MultiServerMCPClient
from kb_weaviate import AsyncWeaviateKnowledgeBase, get_weaviate_async_client, _Source
import re

MCP_SERVER_NAME = "Confluence MCP Server"
client = MultiServerMCPClient(
    {
        MCP_SERVER_NAME: {
            "transport": "sse",
            "url": "http://127.0.0.1:8000/sse"
        },
    }
)

CONFLUENCE_URL = os.getenv("CONFLUENCE_URL")


@asynccontextmanager
async def get_weaviate_client():
    async_weaviate_client = get_weaviate_async_client(
        http_host=os.getenv("WEAVIATE_HTTP_HOST"),
        http_port=os.getenv("WEAVIATE_HTTP_PORT"),
        http_secure=os.getenv("WEAVIATE_HTTP_SECURE") == "true",
        grpc_host=os.getenv("WEAVIATE_GRPC_HOST"),
        grpc_port=os.getenv("WEAVIATE_GRPC_PORT"),
        grpc_secure=os.getenv("WEAVIATE_GRPC_SECURE") == "true",
        api_key=os.getenv("WEAVIATE_API_KEY"),
    )

    try:
        yield AsyncWeaviateKnowledgeBase(
            async_weaviate_client,
            collection_name="omers_confluence_dataset",
        )
    finally:
        if async_weaviate_client:
            await async_weaviate_client.close()


def transform_search_result(response: _Source) -> dict:
    return {
        'page_id': extract_id(response.source.title),
        'title': response.source.title,
        'page_content': response.highlight.text[0]
    }


def extract_id(text: str) -> str | None:
    match = re.match(r"(\d+)_", text)
    if match:
        return match.group(1)
    return None


async def get_tools():
    tools = await client.get_tools()
    print(f"Tools available in MCP Server are {tools}")
    return tools


@observe(name="mcp_server_call_search_confluence_with_cql_queries")
async def search_confluence_with_cql_queries(cql_queries: List[str]):
    async with client.session(MCP_SERVER_NAME) as session:
        all_corr = []

        for query in cql_queries:
            all_corr.append(session.call_tool(
                name="search_confluence_based_on_cql_query",
                arguments={
                    "cql": query
                }
            ))

        page_id_set = set()
        parsed_cql_search_list = []
        confluence_response = await asyncio.gather(*all_corr, return_exceptions=True)
        for res in confluence_response:
            for query_resp in res.content:
                result = json.loads(query_resp.text)
                for page in result["results"]:
                    content = page['content']
                    title = content['title']
                    if '.pdf' in title or '.png' in title or '.docx' in title or '.jpeg' in title or '.jpg' in title:
                        continue

                    page_id = content['id']

                    if page_id not in page_id_set:
                        page_id_set.add(page_id)
                        parsed_cql_search_list.append({
                            'page_id': page_id,
                            'title': title,
                            'matched_content': page['excerpt'],
                            'page_url': f"{CONFLUENCE_URL}/wiki{page['url']}",
                            'lastModified': page['lastModified'],
                            'match_score': page['score']
                        })
        parsed_cql_search_list.sort(key=lambda x: x['match_score'], reverse=True)
        return parsed_cql_search_list


def iterator(values):
    for val in values:
        print(val)


@observe(name="mcp_server_call_download_pages_by_page_id_from_confluence")
async def download_pages(filtered_pages, tools_map, confluence_response: Dict, content_map: Dict):
    try:
        if content_map is None:
            content_map = {}

        if hasattr(filtered_pages, 'additional_kwargs') and filtered_pages.additional_kwargs:
            if 'tool_calls' in filtered_pages.additional_kwargs:
                for tool in filtered_pages.additional_kwargs['tool_calls']:
                    input_param = json.loads(tool['function']["arguments"])
                    title = input_param["title"]
                    page_id = input_param["page_id"]
                    tool_name = tool["function"]["name"]

                    if page_id not in content_map:
                        print(f"Need to call function {tool_name} with title {title} and page_id {page_id}.")

                        page_content = await tools_map[tool_name].ainvoke({
                            'page_id': page_id,
                            'title': title
                        })

                        content_map[page_id] = {
                            'page_id': page_id,
                            'title': title,
                            'page_content': page_content,
                            'page_url': confluence_response.get(page_id, {}).get('page_url')
                        }

        return content_map

    except Exception as e:
        return content_map


def merge_maps(map1: Dict[str, int], map2: Dict[str, int]) -> Dict[str, int]:
    return dict(Counter(map1) + Counter(map2))


def convert_llm_response_to_dict(content: str) -> Dict:
    if not content or content.strip() == '':
        return {}
    json_str = re.sub(r"^```json\n|```$", "", content.strip())
    data = json.loads(json_str)
    return data


async def download_page_directly_from_mcp(page_id: str, title: str = ""):
    async with client.session(MCP_SERVER_NAME) as session:
        response = await session.call_tool(
            name="get_page_by_id",
            arguments={
                'page_id': page_id,
                'title': title
            }
        )
        return response.content[0].text


async def create_page_map(parsed_llm_response, content_map: Dict, confluence_response):
    print(parsed_llm_response)
    if isinstance(parsed_llm_response, list):
        download_pages_map = {page['page_id']: {
            'page_id': page['page_id'],
            'title': page['title'],
            'page_content': await download_page_directly_from_mcp(page['page_id'], page['title']),
            'page_url': confluence_response.get(page['page_id'], {}).get('page_url')
        } for page in parsed_llm_response if page['page_id'] not in content_map}
        content_map.update(download_pages_map)
