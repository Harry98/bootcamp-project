## Python Version
```
Python 3.12.3
```

## Setting Project locally:
```
### Create a Virtual Environment (if not already created):

python3.12 -m venv .venu

### Activate Virtual Environment:

**MAC** source .venu/bin/activate

### Deactivate Virtual Environment:
deactivate

### Run following command to download dependencies:

python3 -m pip install -r requirements.txt
```


## Run Code Locally

```
cd application_code
Then create the .env file and paste all the secrets.
```


### First start the mcp server

```
python3 -m mcp_server
```

Then main file to be executed is graph.py which includes the compiled graph

```
python3 -m graph
```

# Bootcamp Project - File Explanations

### graph_state.py
**Defines the RAGState TypedDict class that manages the state flow between different agents in your LangGraph workflow. 
Contains fields for session_id, user_query, confluence_response, vector_db_response, filtered_pages, and final answer.**

### graph.py
**Contains the main LangGraph workflow definition using StateGraph. Sets up the RAG pipeline with 5 nodes: CQL generation,
vector DB search, Confluence filtering, vector filtering, and answer generation. Implements parallel execution where Confluence and vector DB 
searches run simultaneously before converging at the answer generation stage.**

### agents.py
**Implements the core agent functions for each workflow node. Contains agent_1_generate_cql for creating Confluence queries, agent_2_search_vector_db 
for vector similarity search, agent_3_confluence_filter_pages for filtering relevant Confluence pages, agent_4_vector_db_filter_records 
for filtering vector results, and agent_5_summarize_the_answer for final response generation. Each agent processes the RAGState and updates relevant fields.**

### prompts.py
**Stores all the prompt templates including CQL_GENERATION_PROMPT for creating Confluence queries and CONFLUENCE_PAGE_SYSTEM_MESSAGE for 
filtering page relevance. Contains carefully crafted prompts that instruct LLMs to maintain context, preserve main entities from user queries, 
and make intelligent filtering decisions based on page titles, content excerpts, and match scores.**

### mcp_client.py (or confluence integration file)
**Handles the MCP (Model Context Protocol) client setup and Confluence API interactions. Configures the MultiServerMCPClient with SSE transport,
implements functions like search_confluence_with_cql_queries and page content retrieval. Manages authentication, error handling, and response
parsing for Confluence operations.**