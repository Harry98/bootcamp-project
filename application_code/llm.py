import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI

load_dotenv()

GEMINI_FLASH = "gemini-2.5-flash"
GEMINI_PRO = "gemini-2.5-pro"

AGENT_LLM_NAMES = {
    "worker": GEMINI_FLASH,  # less expensive,
    "planner": GEMINI_PRO,  # more expensive, better at reasoning and planning
}

LLM = ChatOpenAI(model_name=AGENT_LLM_NAMES['worker'], openai_api_base=os.getenv("OPENAI_BASE_URL"))

DEEP_RESEARCH_LLM = ChatOpenAI(model_name=AGENT_LLM_NAMES['planner'], openai_api_base=os.getenv("OPENAI_BASE_URL"))

