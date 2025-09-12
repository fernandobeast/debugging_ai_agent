from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from ...prompts.utils_prompt import DEBUGGING_BRO_PROMPT
from ...tools.utils_tools import get_error_text,get_current_time

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)

debugging_bro = Agent(
    model=model,
    name="debugging_bro",
    description=("Debugging agent that analyzes error logs to extract relevant details and identify issues."
                 "Can detect critical TradingView data errors, coordinate with postgresql_bro to verify missing data,"
                 "and escalate to download_data_bro via LandingStage_manager to restore missing records." 
                 "Delegates all non-log tasks to LandingStage_manager."),
    instruction=DEBUGGING_BRO_PROMPT,
    tools=[get_current_time,get_error_text],
    )

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)
