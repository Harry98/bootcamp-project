from langchain_community.callbacks import get_openai_callback
from llm import LLM, DEEP_RESEARCH_LLM, GEMINI_PRO
from graph_state import RAGState
from prompts import CQL_GENERATION_PROMPT, AgentCqlPrompt, CONFLUENCE_PAGE_SYSTEM_MESSAGE
from agents_helper import get_tools, search_confluence_with_cql_queries, iterator, download_pages, merge_maps, \
    get_weaviate_client, transform_search_result, convert_llm_response_to_dict, create_page_map
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

    confluence_response = await search_confluence_with_cql_queries(response['result'].cql_queries)

    """
    # Iterating response.
    iterator(response['result'].cql_queries)
    iterator(confluence_response)
    """
    return {
        'cql_queries': response['result'],
        'confluence_response': {page['page_id']: page for page in confluence_response},
        'agent_1_generate_cql_token_usage': response['token_usage']
    }


@observe(name="agent_2_search_vector_db")
async def agent_2_search_vector_db(state: RAGState):
    print("Starting agent_2_search_vector_db")
    async with get_weaviate_client() as async_knowledgebase:
        results = await async_knowledgebase.search_knowledgebase(
            state.get("user_query")
        ) or []
    # iterator(results)
    vector_db_response = [transform_search_result(res) for res in results]

    return {'vector_db_response': vector_db_response}


@track_llm_generation(name="agent_3_confluence_filter_pages", model_name=GEMINI_PRO)
async def agent_3_confluence_filter_pages(state: RAGState):
    print("Starting agent_3_confluence_filter_pages")
    """
      Filter the pages from Confluence based on their usefulness in answering the user query.
      Optionally download page content in Markdown format if needed.
    """

    # Fetch LLM tools from MCP Server
    tools = await get_tools()
    tools_map = {t.name: t for t in tools}  # Map tool name -> tool object

    # Create the LangChain pipeline for filtering pages
    filter_pages_lcl = CONFLUENCE_PAGE_SYSTEM_MESSAGE | DEEP_RESEARCH_LLM.bind_tools(tools)
    # Store downloaded page content
    content_map = {}
    # Track token usage for debugging/monitoring
    token_usage = {}
    no_of_tries = 0
    continue_calling = True

    while continue_calling:
        no_of_tries += 1

        # Run the LLM to decide which pages are useful and whether any need downloading
        filtered_response = await run_langchain_expression(filter_pages_lcl, {
            'user_query': state['user_query'],
            'confluence_pages_list': list(state['confluence_response'].values()),
            'tool_outputs': (
                "Right now there is no output. You have to indentify pages for which tool needs to be called."
                if len(content_map) == 0 else content_map
            )
        })

        filtered_pages = filtered_response['result']
        # Download any pages the LLM identified as needed
        content_map = await download_pages(
            filtered_pages,
            tools_map,
            state['confluence_response'],
            content_map
        )

        print(f"Filtered pages llm response [Try Count: {no_of_tries}] {content_map.keys()} LLM: {filtered_pages}.")
        # Merge token usage for monitoring
        token_usage = merge_maps(token_usage, filtered_response['token_usage'])

        # Continue loop if the LLM returned empty content
        continue_calling = filtered_pages.content.strip() == ''
        print(
            f"Filtered pages token usage [Continue calling {continue_calling}] [Try Count: {no_of_tries}] {token_usage}.")

        if not continue_calling:
            # Parse the final LLM output into a dictionary
            parsed_llm_response = convert_llm_response_to_dict(filtered_pages.content)
            await create_page_map(parsed_llm_response, content_map, state['confluence_response'])

            return {
                'filtered_pages': parsed_llm_response,
                'agent_3_confluence_filter_pages_token_usage': token_usage,
                'page_map': content_map
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
