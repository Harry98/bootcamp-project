import asyncio
from llm import LLM


async def test_connection_with_llm():
    resp = await LLM.ainvoke(input="ping")
    print(f"Response from LLM is: {resp.content}")





if __name__ == '__main__':
    print("Starting OMERS Team Project\n\n")
    asyncio.run(test_connection_with_llm())
