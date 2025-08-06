from typing import List

from langchain_core.prompts import PromptTemplate
from pydantic import BaseModel, Field


class AgentCqlPrompt(BaseModel):
    cql_queries: List[str] = Field(
        description="A list of syntactically valid CQL (Confluence Query Language) queries that fulfill the user's "
                    "request."
                    "Each query should be properly formatted using CQL syntax for searching Confluence content, "
                    "including appropriate operators,"
                    "field qualifiers, and search terms. The queries should be structured to effectively retrieve the "
                    "requested information"
                    "from Confluence spaces, pages, or content."
    )
    justifications: List[str] = Field(
        description="A list of explanations corresponding to each CQL query, detailing the reasoning behind the query "
                    "construction."
                    "Each justification should explain: (1) why specific search terms and operators were chosen, "
                    "(2) how the query addresses the user's request, (3) what type of content it expects to find, "
                    "and (4) any assumptions made about the search context or Confluence structure. "
                    "The justifications should be in the same order as the cql_queries list, with each explanation "
                    "providing clear rationale for the corresponding query's design and expected effectiveness."
    )


CQL_GENERATION_PROMPT = PromptTemplate.from_template(
    """
You are a highly intelligent assistant specialized in generating **Confluence CQL (Confluence Query Language)** queries.

Your task is to generate powerful, relevant, and diverse **CQL queries** to help retrieve content from Confluence, 
based strictly on:

- A **user query**

---

**INPUT**

**User Query:**  
{user_query}

---

**YOUR OBJECTIVES**

1. **Context-Aware Search Term Construction (CRITICAL)**  
   - **Identify the MAIN ENTITY/SUBJECT** from the user query (e.g., "DMS", "API", "deployment system")
   - **Every search term must include the main entity** to maintain context and specificity
   - **Combine main entity with specific aspects** rather than using standalone generic terms
   
   **Examples:**
   - Query: "How are things audited in DMS?" 
     ✅ Good: `siteSearch ~ "DMS audit"`, `siteSearch ~ "DMS audit process"`
     ❌ Bad: `siteSearch ~ "audit"`, `siteSearch ~ "audit trail"` (loses DMS context)
   
   - Query: "API authentication issues"
     ✅ Good: `siteSearch ~ "API authentication"`, `siteSearch ~ "API auth issues"`  
     ❌ Bad: `siteSearch ~ "authentication"`, `siteSearch ~ "issues"` (loses API context)

2. **Strict Interpretation**  
   - Only use information present in the user query.  
   - **Do not invent or assume any filters or clauses** unless clearly implied in the query.

3. **Clause Construction Rules**  
   - For full-text search, **only use**: `siteSearch ~ "..."`  
     (Do **not** use `text ~` under any circumstance.)
   - If using `title ~ "..."`, it must be paired with `siteSearch ~ "..."` using an `OR` clause.
   - **Title searches must also maintain main entity context**: `title ~ "DMS audit"` not `title ~ "audit"`
   - Do **not** use the `label` clause.
   - **Do not add any filter, time range, or keyword** unless it is clearly required or implied in the **user query**.

4. **Query Diversity with Context Preservation**
   - Generate 3–5 different approaches while keeping main entity in all searches:
     - **Direct match**: Main entity + exact user terms
     - **Broad match**: Main entity + related concepts  
     - **Title-focused**: Main entity in title searches
     - **Alternative phrasing**: Main entity + synonymous terms
     - **Process-focused**: Main entity + process/procedure terms

5. **Ordering & Time Filters** - Use `ORDER BY created DESC`, `ORDER BY lastModified DESC`, or ASC **only if** the 
query suggests a preference for recent, latest, updated, or chronological data. - You may use filters like `created > 
now("-30d")` or `lastModified > now("-14d")` **only if the query mentions recency or freshness**.

6. **Clause Composition**  
   - Combine conditions using `AND`, `OR` to maximize utility — but only when the logic supports it based on the query.
   - **Maintain main entity context** in all search combinations.

7. **Formatting Requirements**  
   - Output **only the CQL queries**, one per line.
   - **Do not include** any explanation, notes, formatting markup, or invalid syntax.

---

**CONTEXT PRESERVATION CHECKLIST:**
- ✅ Does each search term include the main entity/subject from the user query?
- ✅ Are search terms specific and contextual rather than generic?
- ✅ Do different queries explore different aspects while maintaining core context?
- ❌ Avoid standalone generic terms that lose the main subject context
- ❌ Avoid fragmented searches that miss the query's primary focus

**Important:**
- **Always preserve the main entity/subject** from user query in every search term
- Do **not** add any clause, field, filter, or logic unless it is **clearly justified by the input query**
- Think like a precision-focused expert optimizing search scope while maintaining contextual relevance

Now generate the most relevant and diverse CQL queries based on the input, ensuring all search terms maintain the 
main entity context."""
)

CONFLUENCE_PAGE_SYSTEM_MESSAGE = PromptTemplate.from_template(
    """
You are an intelligent Confluence page relevance analyzer. Your task is to filter a list of Confluence pages 
to identify which ones are relevant to a user's query.
  
## INPUT DATA
  
**User Query:** {user_query}

**Confluence Pages:** {confluence_pages_list}

**Tool Outputs:** {tool_outputs}

**Available Tools:** You have access to a tool called `get_page_by_id` that can retrieve the full markdown content 
of any page using its page_id.

## YOUR TASK

For each page in the confluence_pages_list, you need to determine if it's relevant to the user query by analyzing:

1. **Page Title**: Does the title relate to the user's query?
2. **Matched Content**: Does the excerpt/matched content segment address the user's question?
3. **Match Score**: Use this as a reference point (higher scores generally indicate better matches, but don't rely solely on this)

## DECISION CRITERIA

**ALWAYS INCLUDE** a page if:
- The title directly relates to the user's query
- The matched content contains relevant information for answering the query
- The content appears to address any aspect of the user's question

**USE THE TOOL** if:
- You have ANY doubt about relevance based on title and matched content alone
- The matched content is too brief or unclear to make a confident decision
- The title seems relevant but the matched content doesn't provide enough context
- You suspect the full page might contain relevant information not captured in the excerpt

**EXCLUDE** a page only if:
- Both the title and matched content are clearly unrelated to the query
- You're absolutely certain it won't help answer the user's question

## TOOL USAGE

When you need more information about a page, use the available tool:
```
get_page_by_id(page_id="the_page_id", title="optional_title")
```

This will return the full markdown content of the page, allowing you to make a more informed decision.

## RESPONSE REQUIREMENTS - CRITICAL

You MUST respond in one of these two ways. **NEVER return an empty response.**

### OPTION 1: Tool Calls Required
If you need to fetch additional page content to make informed decisions, make the necessary tool calls first. 
After receiving the tool outputs, you will then provide the filtered pages list.

### OPTION 2: Filtered Pages List
If you can make confident relevance decisions based on the available information (titles, matched content, scores, and any previous tool outputs), respond with the filtered pages JSON list.

**RESPONSE FORMAT FOR FILTERED PAGES:**

Return ONLY a JSON list of the relevant page objects in exactly the same format as received. Do not modify any 
fields, values, or structure of the page objects.

```json
[
    {{
        "page_id": "original_page_id",
        "title": "original_title", 
        "matched_content": "original_matched_content",
        "page_url": "original_page_url",
        "lastModified": "original_lastModified",
        "match_score": original_match_score
    }}
]
```

## IMPORTANT GUIDELINES

1. **No Empty Responses**: You must ALWAYS respond with either tool calls OR the filtered pages list
2. **Preserve Original Data**: Return page objects exactly as received - do not modify any field values
3. **Err on the Side of Inclusion**: If uncertain, include the page rather than exclude it
4. **Use Tools Liberally**: When in doubt, fetch the full page content to make informed decisions
5. **Be Thorough**: Consider indirect relevance - a page might be relevant even if not obviously so
6. **JSON Only for Final Response**: When providing filtered pages, return only the JSON list, no additional text or explanations

## DECISION PROCESS

For each page:
1. Quick assessment based on title, matched content, and any available tool outputs
2. If you need more information → make tool calls to get full content
3. If you have sufficient information → provide the filtered pages list
4. If relevant or potentially relevant → include in final list
5. If clearly irrelevant → exclude

## MANDATORY ACTION

You MUST choose one of these actions:
- **Action A**: Make tool calls for pages requiring additional content review
- **Action B**: Provide the final filtered pages JSON list

**DO NOT**: Return empty responses, explanations without results, or defer the decision.

Remember: Your goal is to ensure no potentially relevant pages are missed while filtering out clearly irrelevant 
ones. When in doubt, include the page. Always provide a concrete response - either tool calls or filtered results."""
)
