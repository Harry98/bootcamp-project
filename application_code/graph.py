import asyncio
import uuid

from langgraph.graph import StateGraph, START, END
from agents import (
    agent_1_generate_cql,
    agent_2_search_vector_db,
    agent_3_confluence_filter_pages,
    agent_4_vector_db_filter_records,
    agent_5_summarize_the_answer
)
from graph_state import RAGState
from langfuse_utils.oai_sdk_setup import setup_langfuse_tracer
from langfuse_utils.shared_client import langfuse_client

# Node constants
NODE_1 = "CQL_GENERATION_AGENT"
NODE_2 = "VECTOR_DB_SEARCH_AGENT"
NODE_3 = "CONFLUENCE_RESPONSE_CHECKER_AGENT"
NODE_4 = "VECTOR_DB_RESPONSE_CHECKER_AGENT"
NODE_5 = "ANSWER_GENERATION_AGENT"


def route_to_start_nodes(state: RAGState):
    """
    Conditional entry point that determines which initial nodes to execute.
    Returns a list of nodes to start with parallel execution.
    """
    # You can add logic here to conditionally choose starting nodes based on state
    # For now, returning both nodes for parallel execution
    return [NODE_1, NODE_2]


# Create the StateGraph
builder = StateGraph(RAGState)

# Add all nodes
builder.add_node(NODE_1, agent_1_generate_cql)
builder.add_node(NODE_2, agent_2_search_vector_db)
builder.add_node(NODE_3, agent_3_confluence_filter_pages)
builder.add_node(NODE_4, agent_4_vector_db_filter_records)
builder.add_node(NODE_5, agent_5_summarize_the_answer, defer=True)

# Conditional entry point for parallel execution
builder.add_conditional_edges(
    START,
    route_to_start_nodes,
    {
        NODE_1: NODE_1,
        NODE_2: NODE_2
    }
)

# Sequential edges within each path
builder.add_edge(NODE_1, NODE_3)  # CQL generation -> Confluence filtering
builder.add_edge(NODE_2, NODE_4)  # Vector search -> Vector filtering

# Both filtered results go to answer generation
builder.add_edge(NODE_3, NODE_5)
builder.add_edge(NODE_4, NODE_5)

# Answer generation goes to end
builder.add_edge(NODE_5, END)

# Compile the workflow
confluence_workflow = builder.compile()


async def execute_user_query(user_query: str):
    print("Graph getting invoked \n\n")

    state = RAGState(
        session_id=str(uuid.uuid4()),
        user_query=user_query,
        confluence_response=[],  # Empty list instead of None
        filtered_pages=[],  # Empty list instead of None
        vector_db_response=[],  # Empty list instead of None
        answer="",
        cql_queries=[]
    )

    # Uncomment this code to run directly....
    """
    response = await confluence_workflow.ainvoke(input=state)
    print(f"Answer to the user query is {response}.")
    """

    async for chunk in confluence_workflow.astream(input=state, stream_mode="updates"):
        print(f"Got update from the state {chunk}.")

    setup_langfuse_tracer()

    with langfuse_client.start_as_current_span(name="Agents-SDK-Trace") as span:
        span.update(input=state)



if __name__ == '__main__':
    test_query = [
        "Tell me about Maple trust bank?",
    ]
    asyncio.run(execute_user_query(test_query[0]))
        
