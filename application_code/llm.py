import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
load_dotenv()

LLM = ChatOpenAI(model_name=os.getenv("AGENT_LLM_NAME"), openai_api_base=os.getenv("OPENAI_BASE_URL"))