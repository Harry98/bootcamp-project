from langchain_community.callbacks import get_openai_callback
from llm import LLM, DEEP_RESEARCH_LLM, GEMINI_PRO
from graph_state import RAGState
from prompts import CQL_GENERATION_PROMPT, AgentCqlPrompt, CONFLUENCE_PAGE_SYSTEM_MESSAGE
from agents_helper import get_tools, search_confluence_with_cql_queries, iterator, download_pages, merge_maps
from langfuse import observe
from tracking import track_llm_generation


async def run_langchain_expression(lcl_expression, expression_input):
    with get_openai_callback() as cb:
        result = await lcl_expression.ainvoke(input=expression_input)

    return {
        'result': result,
        'token_usage': {
            'total_tokens': cb.total_tokens,
            'input_tokens': cb.prompt_tokens,
            'output_tokens': cb.completion_tokens,
            'total_cost': cb.total_cost
        }
    }


@track_llm_generation(name="agent_1_generate_cql")
async def agent_1_generate_cql(state: RAGState):
    print("Starting agent_1_generate_cql")
    cql_generation_chain = CQL_GENERATION_PROMPT | LLM.with_structured_output(AgentCqlPrompt)
    response = await run_langchain_expression(cql_generation_chain, {
        'user_query': state.get("user_query")
    })

    iterator(response['result'].cql_queries)

    confluence_response = await search_confluence_with_cql_queries(response['result'].cql_queries)
    # iterator(confluence_response)
    return {
        'cql_queries': response['result'],
        'confluence_response': confluence_response,
        'agent_1_generate_cql_token_usage': response['token_usage']
    }


@observe(name="agent_2_search_vector_db")
async def agent_2_search_vector_db(state: RAGState):
    print("Starting agent_2_search_vector_db")
    """
    Connect to vector DB and perform semantic search....
    Pass user query as input.
    """
    vector_db_response = []  # Set this equal to the response from vector DB
    return {
        'vector_db_response': vector_db_response
    }


@track_llm_generation(name="agent_3_confluence_filter_pages", model_name=GEMINI_PRO)
async def agent_3_confluence_filter_pages(state: RAGState):
    print("Starting agent_3_confluence_filter_pages")
    """
      Filter the pages got from confluence based on their usefulness in answering the user query.
      Send LLM tools to download the page content in Markdown format if required.
    """

    # Fetching tools from MCP Server and making first call to LLM.
    tools = await get_tools()
    tools_map = {t.name: t for t in tools}
    filter_pages_lcl = CONFLUENCE_PAGE_SYSTEM_MESSAGE | DEEP_RESEARCH_LLM.bind_tools(tools)
    filtered_response = await run_langchain_expression(filter_pages_lcl, {
        'user_query': state['user_query'],
        'confluence_pages_list': state['confluence_response'],
        'tool_outputs': "Right now there is no output. You have to indentify pages for which tool needs to be called."
    })
    filtered_pages = filtered_response['result']
    print(f"Filtered pages llm response 1st try {filtered_pages}.")

    # Downloading pages from the confluence.
    content_map = await download_pages(filtered_pages, tools_map)

    if not content_map or len(content_map) == 0:
        return {
            'filtered_pages': filtered_pages.content,
            'agent_3_confluence_filter_pages_token_usage': filtered_response['token_usage']
        }
    else:
        tools_response = await run_langchain_expression(filter_pages_lcl, {
            'user_query': state['user_query'],
            'confluence_pages_list': state['confluence_response'],
            'tool_outputs': content_map
        })
        print(f"Filtered pages llm response 2st try {tools_response['result']}.")
        return {
            'filtered_pages': tools_response['result'].content,
            'agent_3_confluence_filter_pages_token_usage': merge_maps(tools_response['token_usage'], filtered_response['token_usage'])
        }


@track_llm_generation(name="agent_4_vector_db_filter_records")
async def agent_4_vector_db_filter_records(state: RAGState):
    print("Starting agent_4_vector_db_filter_records")
    """
     Filter the pages got from vector DB based on their usefulness in answering the user query.
    """
    vector_db_response = []  # Set this equal to the response from vector DB
    return {
        'vector_db_response': vector_db_response,
        'agent_4_vector_db_filter_records_token_usage': {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0
        }
    }


@track_llm_generation(name="agent_5_summarize_the_answer")
async def agent_5_summarize_the_answer(state: RAGState):
    print("Starting agent_5_summarize_the_answer")
    """
    Send LLM user query, filtered_pages, vector_db_response and tools
    (Send LLM tools to download the page content in Markdown format if required.)

    Ask LLM to generate final answer to user query based on the information provided.
    """
    answer = ""  # Set this equal to the response from LLM
    return {
        'answer': answer,
        'agent_5_summarize_the_answer_token_usage': {
            'total_tokens': 0,
            'input_tokens': 0,
            'output_tokens': 0,
            'total_cost': 0
        }
    }
