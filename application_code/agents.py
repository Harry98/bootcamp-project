from llm import LLM, DEEP_RESEARCH_LLM
from graph_state import RAGState
from prompts import CQL_GENERATION_PROMPT, AgentCqlPrompt, CONFLUENCE_PAGE_SYSTEM_MESSAGE
from agents_helper import get_tools, search_confluence_with_cql_queries, iterator, download_pages, async_knowledgebase, transform_search_result


async def agent_1_generate_cql(state: RAGState):
    print("Starting agent_1_generate_cql")
    cql_generation_chain = CQL_GENERATION_PROMPT | LLM.with_structured_output(AgentCqlPrompt)
    response = await cql_generation_chain.ainvoke(input={
        'user_query': state.get("user_query")
    })
    iterator(response.cql_queries)

    confluence_response = await search_confluence_with_cql_queries(response.cql_queries)
    # iterator(confluence_response)
    return {
        'cql_queries': response.cql_queries,
        'confluence_response': confluence_response
    }


async def agent_2_search_vector_db(state: RAGState):
    print("Starting agent_2_search_vector_db")
    """
    Connect to vector DB and perform semantic search....
    Pass user query as input.
    """
    results = await async_knowledgebase.search_knowledgebase(
                state.get("user_query")
    )
    vector_db_response = []
    for res in results:
        vector_db_response.append(transform_search_result(res))
    return {
        'vector_db_response': vector_db_response
    }


async def agent_3_confluence_filter_pages(state: RAGState):
    print("Starting agent_3_confluence_filter_pages")
    """
      Filter the pages got from confluence based on their usefulness in answering the user query.
      Send LLM tools to download the page content in Markdown format if required.
    """
    iterator(state['confluence_response'])
    tools = await get_tools()
    tools_map = {t.name: t for t in tools}
    filter_pages_lcl = CONFLUENCE_PAGE_SYSTEM_MESSAGE | DEEP_RESEARCH_LLM.bind_tools(tools)
    filtered_pages = await filter_pages_lcl.ainvoke(input={
        'user_query': state['user_query'],
        'confluence_pages_list': state['confluence_response'],
        'tool_outputs': "Right now there is no output. You have to indentify pages for which tool needs to be called."
    })
    # print(f"\n\n Filtered Pages: {filtered_pages}")
    content_map = await download_pages(filtered_pages, tools_map)
    if not content_map or len(content_map) == 0:
        return {
            'filtered_pages': filtered_pages.content
        }
    else:
        tools_response = await filter_pages_lcl.ainvoke(input={
            'user_query': state['user_query'],
            'confluence_pages_list': state['confluence_response'],
            'tool_outputs': content_map
        })
        return {
            'filtered_pages': tools_response.content
        }


async def agent_4_vector_db_filter_records(state: RAGState):
    print("Starting agent_4_vector_db_filter_records")
    """
     Filter the pages got from vector DB based on their usefulness in answering the user query.
    """
    vector_db_response = []  # Set this equal to the response from vector DB
    return {
        'vector_db_response': vector_db_response
    }


async def agent_5_summarize_the_answer(state: RAGState):
    print("Starting agent_5_summarize_the_answer")
    """
    Send LLM user query, filtered_pages, vector_db_response and tools
    (Send LLM tools to download the page content in Markdown format if required.)

    Ask LLM to generate final answer to user query based on the information provided.
    """
    answer = ""  # Set this equal to the response from LLM
    return {
        'answer': answer
    }
