import asyncio
import json
from typing import List

from langchain_mcp_adapters.client import MultiServerMCPClient

MCP_SERVER_NAME = "Confluence MCP Server"
client = MultiServerMCPClient(
    {
        MCP_SERVER_NAME: {
            "transport": "sse",
            "url": "http://0.0.0.0:8000/sse"
        },
    }
)


async def get_tools():
    tools = await client.get_tools()
    print(f"Tools available in MCP Server are {tools}")
    return tools


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
                            'page_url': page['url'],
                            'lastModified': page['lastModified'],
                            'match_score': page['score']
                        })
        parsed_cql_search_list.sort(key=lambda x: x['match_score'], reverse=True)
        return parsed_cql_search_list


def iterator(values):
    for val in values:
        print(val)


async def download_pages(filtered_pages, tools_map):
    try:
        content_map = []
        if hasattr(filtered_pages, 'additional_kwargs') and filtered_pages.additional_kwargs:
            if 'tool_calls' in filtered_pages.additional_kwargs:
                for tool in filtered_pages.additional_kwargs['tool_calls']:
                    input_param = json.loads(tool['function']["arguments"])
                    title = input_param["title"]
                    page_id = input_param["page_id"]
                    tool_name = tool["function"]["name"]

                    print(f"Need to call function {tool_name} with title {title} and page_id {page_id}.")
                    page_content = await tools_map[tool_name].ainvoke({
                        'page_id': page_id,
                        'title': title
                    })

                    content_map.append({
                        'page_id': page_id,
                        'title': title,
                        'page_content': page_content
                    })

        return content_map

    except Exception as e:
        return []
