from typing import Dict

from mcp.server.fastmcp import FastMCP
from atlassian import Confluence
import html2text

mcp = FastMCP(name="Confluence MCP Server")

confluence = Confluence(
    url='https://omerspensions.atlassian.net',
    username='hagrewal@omers.com',
    password='ATATT3xFfGF0A8sk2CVuXuwoVz51zrJIyD9r_wLAVlUwQ-fAtO4JPFW10RSAyg2_NhzBcpZesHR5b0u2YIb2QGp0rpfC-ZbPTjBBXtZed_I2LKDlRyJ_BL2MVlkliHZ60bi1kPTILdwJte04SjN0M90dpVlBaL3w-tDGDKnW6lQXNcbepiMdZ0c=49EE561D',
    cloud=True)


@mcp.tool()
def search_confluence_based_on_cql_query(cql: str) -> Dict:
    """
    Search Confluence pages using Confluence Query Language (CQL) for advanced content discovery.

    This tool enables powerful searching across your Confluence instance using CQL syntax,
    which provides much more flexibility than basic text searches. CQL allows you to search
    by content, metadata, page properties, spaces, creators, dates, and much more.

    The tool is particularly useful for:
    - Finding pages across multiple spaces
    - Locating content by specific authors or contributors
    - Filtering results by creation/modification dates
    - Searching within specific content types (pages, blog posts, etc.)
    - Complex queries combining multiple criteria
    - Content auditing and discovery workflows

    Args:
        cql (str): A Confluence Query Language (CQL) query string. This can range from
                  simple text searches to complex queries with multiple operators.

                  Common CQL examples:
                  - Simple text: "project requirements"
                  - By space: "space = 'PROJ' and text ~ 'requirements'"
                  - By creator: "creator = 'john.doe' and type = 'page'"
                  - By date: "created >= '2024-01-01' and text ~ 'meeting'"
                  - Combined: "space in ('PROJ', 'DOC') and creator = 'jane.smith'"

                  Note: The 'siteSearch' operator mentioned in the original description
                  is just one of many available CQL operators. This tool accepts any
                  valid CQL syntax for maximum flexibility.

    Returns:
        Dict: A comprehensive dictionary containing search results with the following structure:
              - 'results': List of up to 51 matching Confluence pages/content
              - Each result includes:
                * 'id': Unique page identifier (can be used with get_page_by_id)
                * 'title': Page title
                * 'type': Content type (page, blogpost, etc.)
                * 'space': Information about the containing space
                * '_links': URLs and navigation links
                * 'excerpt': Brief content preview/snippet
                * Additional metadata depending on content type
              - 'start': Starting index of results (pagination info)
              - 'limit': Maximum number of results returned (51)
              - 'size': Actual number of results in this response
              - '_links': Pagination and navigation links

              The results can be used to:
              - Get page IDs for detailed content retrieval
              - Understand content distribution across spaces
              - Identify relevant pages for further processing
              - Build content inventories and reports
    """
    return confluence.cql(cql, start=0, limit=25)


@mcp.tool()
def get_page_by_id(page_id: str, title: str = None) -> str:
    """
    Retrieve a Confluence page's content by ID and convert it to Markdown format.

    This tool fetches a specific Confluence page using its unique identifier and converts
    the HTML content to clean, readable Markdown. It also extracts metadata including
    the page creator and last editor information, which can be useful for tracking
    employee contributions and page ownership.

    Args:
        page_id (str): The unique identifier of the Confluence page to retrieve.
                      This is typically found in the page URL or can be obtained
                      through Confluence API search endpoints.
        title (str, optional): An optional title to include in the output formatting.
                              If provided, the response will be prefixed with this title
                              for better context and readability. Defaults to None.

    Returns:
        str: A formatted string containing:
             - Page title (if title parameter is provided)
             - Page creation and modification metadata (creator and last editor names)
             - The complete page content converted to Markdown format

             The Markdown conversion makes the content more suitable for LLM processing
             and human readability compared to raw HTML. This includes proper formatting
             of headers, lists, links, tables, and other content elements.

             The metadata can be used for:
             - Tracking employee work and contributions
             - Understanding page ownership and responsibility
             - Content auditing and review processes

    Example:
        # Basic usage
        content = get_page_by_id("123456789")

        # With custom title
        content = get_page_by_id("123456789", title="Project Requirements")
    """
    response = confluence.get_page_by_id(
        page_id, expand="body.storage,version,history"
    )

    html_content = response["body"]["storage"]["value"]
    markdown_text = html2text.html2text(html_content)

    creator = response.get("history", {}).get("createdBy", {}).get("displayName", "Unknown")
    editor = response.get("version", {}).get("by", {}).get("displayName", "Unknown")

    extra_info = f"\n\n Page Created by: {creator}\n Page Last edited by: {editor}\n"

    if title:
        return f"Title of the page is {title} \n {extra_info} and markdown of the page is \n\n {markdown_text}"
    return extra_info + markdown_text


if __name__ == "__main__":
    # Initialize and run the server
    mcp.run(transport='sse')
