from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
# from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioServerParameters
# from google.adk.tools.mcp_tool import SseConnectionParams, StreamableHTTPConnectionParams
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams


from ...prompts.utils_prompt import MONGO_BRO_PROMPT
from ...tools.utils_tools import get_current_time

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                # api_key=os.getenv("OPENAI_API_KEY"),
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)

mongodb_bro = Agent(
    model=model,
    name="mongodb_bro",
    description=(
         "Read-only MongoDB agent that retrieves data with find or aggregate (read-only) queries only. "
         "Can inspect collections, fields, data types, counts, and basic statistics."
         "Delegates all non-MongoDB or write-related requests to LandingStage_manager."
        ),

    instruction=MONGO_BRO_PROMPT,
    tools=[

        MCPToolset(connection_params=StdioConnectionParams(
            server_params= {
            "command" : "npx",
            "args" : ["-y", "mongodb-mcp-server","--connectionString",
                      "mongodb://username:password@127.0.0.1:27017/?authSource=admin",
                      "--readOnly"]}, timeout=30
            )),
        get_current_time,],
)


# list ticker names with its spike_date on 2025-08-08 from  tick_data_parquet collection in my tick_data mongo database
