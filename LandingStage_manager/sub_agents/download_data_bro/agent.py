from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from ...prompts.utils_prompt import DOWNLOAD_DATA_PROMPT
from ...tools.utils_tools import download_missing_batch

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)

download_data_bro = Agent(
    model=model,
    name="download_data_bro",
    description=("download missing data from session"),
    instruction=DOWNLOAD_DATA_PROMPT,
    tools=[download_missing_batch],
    )

# fix the download_data_tv function tool 