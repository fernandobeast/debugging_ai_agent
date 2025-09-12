from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from ...prompts.utils_prompt import MISSING_TICKER_PARSER
from typing import List
from pydantic import BaseModel, Field

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)


# # Debug prints to confirm pathing
# print("cwd:", Path.cwd())
# print("error_path:", _ERROR_PATH, "exists:", _ERROR_PATH.exists())
# print("repo root contents:", list(Path('.').resolve().iterdir()))

class TickersCol(BaseModel):
    ticker: str = Field(description="UPPERCASE ticker")
    date: str = Field(description="date in YYYY-MM-DD")

class MissingTickers(BaseModel):
    missing_tickers: List[TickersCol]


missing_ticker_parser = Agent(
    model=model,
    name="missing_ticker_parser",
    description=("Read raw error-log text and output structured JSON."),         
    instruction=MISSING_TICKER_PARSER,
    output_schema=MissingTickers,
    output_key="todays_missing_tickers",
    disallow_transfer_to_parent=True,
    disallow_transfer_to_peers=True,
    )