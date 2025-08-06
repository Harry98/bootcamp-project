import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

AGENT_LLM_NAMES = {
    "worker": "gemini-2.5-flash",  # less expensive,
    "planner": "gemini-2.5-pro",  # more expensive, better at reasoning and planning
}

LLM = ChatOpenAI(model_name=AGENT_LLM_NAMES['worker'], openai_api_base=os.getenv("OPENAI_BASE_URL"))

DEEP_RESEARCH_LLM = ChatOpenAI(model_name=AGENT_LLM_NAMES['planner'], openai_api_base=os.getenv("OPENAI_BASE_URL"))
