import asyncio

import html2text
from atlassian import Confluence
import os
from dotenv import load_dotenv
import re
import unicodedata

load_dotenv()

INGESTION_FOLDER = "ingestion_docs"
confluence = Confluence(
    url=os.getenv("CONFLUENCE_URL"),
    username=os.getenv("CONFLUENCE_ACCOUNT"),
    password=os.getenv("CONFLUENCE_TOKEN"),
    cloud=True)


def clean_page_content(content: str) -> str:
    if not content:
        return ""

    # Normalize Unicode to separate emojis/symbols
    content = unicodedata.normalize("NFKD", content)

    # Remove all emojis and symbols (includes flags, emoticons, pictographs, etc.)
    emoji_pattern = re.compile(
        "["
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F680-\U0001F6FF"  # transport & map
        "\U0001F700-\U0001F77F"  # alchemical
        "\U0001F780-\U0001F7FF"  # geometric
        "\U0001F800-\U0001F8FF"
        "\U0001F900-\U0001F9FF"
        "\U0001FA00-\U0001FAFF"
        "\U00002500-\U00002BEF"  # box drawing, arrows, etc.
        "\U00002700-\U000027BF"  # dingbats
        "\U0001F1E6-\U0001F1FF"  # flags
        "\u2600-\u26FF"  # misc symbols
        "\u2700-\u27BF"  # dingbats
        "]+",
        flags=re.UNICODE
    )
    content = emoji_pattern.sub('', content)

    # Remove markdown headers, bold, italic, and list bullets
    content = re.sub(r'^#{1,6}\s*', '', content, flags=re.MULTILINE)  # headers
    content = re.sub(r'\*\*(.*?)\*\*', r'\1', content)  # bold
    content = re.sub(r'\*(.*?)\*', r'\1', content)  # italic
    content = re.sub(r'^[\-\*\•\‣\●\▪\–\—]\s+', '', content, flags=re.MULTILINE)  # bullets

    # Remove horizontal lines and excessive dashes
    content = re.sub(r'^[-=*_]{2,}$', '', content, flags=re.MULTILINE)

    # Remove extra spaces or newlines
    content = re.sub(r'\n{2,}', '\n', content)  # collapse multiple newlines
    content = re.sub(r'[ \t]{2,}', ' ', content)  # collapse multiple spaces
    content = content.strip()

    return content


async def get_page_by_id(page_id: str, title: str = None) -> str:
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


def get_all_spaces():
    spaces = confluence.get_all_spaces()
    for space in spaces['results']:
        print(f"Space key {space['key']}")
        get_all_pages_in_space(space['key'])


async def get_all_pages_in_space(space='SD'):
    pages = confluence.get_all_pages_from_space(space=space)
    print(f"Total no of pages {len(pages)}")
    for page in pages:
        print(page)
        title = page['title']
        page_id = page['id']
        page_content = await get_page_by_id(page_id, title)
        file_name = clean_page_content(f"{page_id}_{title}.txt")
        base_dir = os.path.dirname(__file__)
        with open(f"{base_dir}/{INGESTION_FOLDER}/{file_name}", 'w') as rb:
            rb.write(clean_page_content(page_content))


if __name__ == '__main__':
    print("Starting Ingestion.")
    asyncio.run(get_all_pages_in_space(space='~63e828e8f1475ad42c5e16ef'))
