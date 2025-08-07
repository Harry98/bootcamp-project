import os

from atlassian import Confluence

from graph_state import RAGState
from agents import agent_3_confluence_filter_pages, agent_1_generate_cql, agent_2_search_vector_db
import asyncio
from dotenv import load_dotenv
from agents_helper import search_confluence_with_cql_queries, get_tools

load_dotenv()

confluence = Confluence(
    url=os.getenv("CONFLUENCE_URL"),
    username=os.getenv("CONFLUENCE_ACCOUNT"),
    password=os.getenv("CONFLUENCE_TOKEN"),
    cloud=True)


def test_search_confluence():
    query = 'siteSearch ~ "Maple trust bank"'
    result = confluence.cql(query)
    print(result)


def test_agent_4_confluence_review_agent():
    dummy_state = RAGState(
        session_id="testing",
        user_query="What is DMS?",
        confluence_response=[
            {'page_id': '3014164585', 'title': 'DMS Core Service',
             'matched_content': 'Allowed File Extensions for Document Upload\nOnly following document extension types are allowed in @@@hl@@@DMS@@@endhl@@@ Core to be uploaded.\n    PDF(&quot;.pdf&quot;, &quot;application/pdf&quot;),\n    DOCX(&quot;.docx...-officedocument.presentationml.presentation&quot;);\n@@@hl@@@DMS@@@endhl@@@ Request-Response\nPOST Request - Upload Document By Streaming - /v1/shareping/blob/stream\nRequest\nRequest Structure!--https',
             'page_url': '/spaces/SA/pages/3014164585/DMS+Core+Service', 'lastModified': '2025-05-09T13:11:04.000Z',
             'match_score': 35.939236},
            {'page_id': '3199762434', 'title': 'DMS - Audit',
             'matched_content': 'Overview\nThe Orbit document migration project involves migrating documents from an existing document management system (Orbit) to a new custom solution (@@@hl@@@DMS@@@endhl@@@) and Sharepoint Sites... includes:\nDocument types and formats to be migrated.\nSource and target systems [ @@@hl@@@DMS@@@endhl@@@ &amp; Sharepoint ].\nRoles and responsibilities of stakeholders involved in the migration.\nDuration',
             'page_url': '/spaces/SA/pages/3199762434/DMS+-+Audit', 'lastModified': '2024-05-10T15:44:23.000Z',
             'match_score': 33.439625},
            {'page_id': '3776315396', 'title': 'SharePoint Service to DMS',
             'matched_content': ', and the corresponding files in SharePoint will be deleted.\nAll APIs will be provided through @@@hl@@@DMS@@@endhl@@@, and the SharePoint service will be decommissioned.\nFollow-up documents are generated...-SVC@omers.onmicrosoft.com\nCurrent flow with sharepoint-service\nNew flow with @@@hl@@@dms@@@endhl@@@-core-service\nDocument transfer process\nMetadata',
             'page_url': '/spaces/SA/pages/3776315396/SharePoint+Service+to+DMS',
             'lastModified': '2025-05-29T22:44:02.000Z', 'match_score': 33.315857},
            {'page_id': '3206774822', 'title': 'DMS - Sharepoint',
             'matched_content': 'Overview\n@@@hl@@@DMS@@@endhl@@@ Core service exposes endpoint for Sharepoint Online integration. These endpoints can be used in following ways\nTo upload documents into Sharepoint site, with metadata...)\nThis use case is their for uploading file into Sharepoint for Donna S&amp;D service. @@@hl@@@DMS@@@endhl@@@ will be updated with this feature in coming months.\nSharepoint Upload Without Metadata\nCurrently',
             'page_url': '/spaces/SA/pages/3206774822/DMS+-+Sharepoint', 'lastModified': '2024-05-01T01:11:22.000Z',
             'match_score': 33.285553}
        ],
        filtered_pages=[],
        vector_db_response=[],
        answer="",
        cql_queries=[]
    )
    print(asyncio.run(agent_3_confluence_filter_pages(state=dummy_state)))


def test_agent_1_generate_cql():
    dummy_state = RAGState(
        session_id="testing",
        user_query="Tell me about Maple trust bank?",
        confluence_response=[],
        filtered_pages=[],
        vector_db_response=[],
        answer="",
        cql_queries=[]
    )
    print(asyncio.run(agent_1_generate_cql(state=dummy_state)))


def test_agent_2_search_vector_db():
    dummy_state = RAGState(
        session_id="testing",
        user_query="Tell me about Maple trust bank?",
        confluence_response=[],
        filtered_pages=[],
        vector_db_response=[],
        answer="",
        cql_queries=[]
    )
    print(asyncio.run(agent_2_search_vector_db(state=dummy_state)))


if __name__ == '__main__':
    test_agent_2_search_vector_db()
    #print("Starting code to be tested.")
    # test_agent_4_confluence_review_agent()
    # test_agent_1_generate_cql()
    #test_search_confluence()
    #asyncio.run(search_confluence_with_cql_queries(['siteSearch ~ "Maple trust bank"']))
    #asyncio.run(get_tools())
