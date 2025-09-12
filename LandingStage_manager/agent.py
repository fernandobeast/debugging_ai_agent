from google.adk.agents import Agent,SequentialAgent
from google.adk.models.lite_llm import LiteLlm

from .prompts.utils_prompt import LANDING_STAGE_MANAGER_PROMPT
from .tools.utils_tools import get_current_time
from .sub_agents.postgresql_bro.agent import postgresql_bro
from .sub_agents.mongodb_bro.agent import mongodb_bro
from .sub_agents.debugging_bro.agent import debugging_bro
from .sub_agents.missing_ticker_parser.agent import missing_ticker_parser
from .sub_agents.download_data_bro.agent import download_data_bro


OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                # api_key=os.getenv("OPENAI_API_KEY"),
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)

get_missing_tickers = SequentialAgent(
    name="get_missing_tickers",
    sub_agents=[debugging_bro, missing_ticker_parser, postgresql_bro, download_data_bro],  # order matters
)

root_agent = Agent(
    name="LandingStage_manager",
    model=model,
    description="landing stage manager agent",
    instruction=LANDING_STAGE_MANAGER_PROMPT,
    
    sub_agents=[
                mongodb_bro,
                get_missing_tickers
                ],
    tools=[
        get_current_time
           ],
)

