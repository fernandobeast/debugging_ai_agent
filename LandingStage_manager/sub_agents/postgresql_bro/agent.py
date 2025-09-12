from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
from google.adk.tools.mcp_tool import MCPToolset, StdioConnectionParams,StreamableHTTPConnectionParams
from ...prompts.utils_prompt import POSTGRES_BRO_PROMPT
from ...tools.utils_tools import get_current_time

OLLAMA_MODEL = "qwen3:14b"
model = LiteLlm(model=f"openai/{OLLAMA_MODEL}",
                # api_key=os.getenv("OPENAI_API_KEY"),
                api_key="unused",
                temperature=0.0,
                top_p=1.0,
                max_output_tokens=32_000)

postgresql_bro = Agent(
    model=model,
    name="postgresql_bro",
    description=(
         "Read-only PostgreSQL agent that retrieves data with SELECT queries only. "
         "Can inspect tables, columns, data types, counts, and basic statistics. "
         "Delegates all non-PostgreSQL or write-related requests to LandingStage_manager."
        ),

    instruction=POSTGRES_BRO_PROMPT,

#! Created user fernando with all DBs read-only access  
    tools = [
        MCPToolset(
            connection_params=StdioConnectionParams(server_params=
                {"command":"uv",
                "args":["run","postgres-mcp","--access-mode=unrestricted"],
                "env":{"DATABASE_URI": "postgresql://username:password@127.0.0.1:5432/landing_stage"}
                })
            ),
        MCPToolset(
            connection_params=StdioConnectionParams(server_params=
                {"command":"uv",
                "args":["run","postgres-mcp","--access-mode=unrestricted"],
                "env":{"DATABASE_URI": "postgresql://username:password@127.0.0.1:5432/one_min_daily_data"}
                })
            ),
        get_current_time],
)
