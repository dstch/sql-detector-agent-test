import sys
from pathlib import Path
from typing import Literal
import asyncio

sys.path.insert(0, str(Path(__file__).parent.parent))

import agentscope
from agentscope.agent import ReActAgent
from agentscope.message import Msg
from agentscope.model import OpenAIChatModel, DashScopeChatModel, AnthropicChatModel, OllamaChatModel
from agentscope.tool import Toolkit
from agentscope.formatter import (
    OpenAIChatFormatter,
    DashScopeChatFormatter,
    AnthropicChatFormatter,
    OllamaChatFormatter,
)

from .config import AgentConfig, ModelConfig
from .tools import get_db_schema, run_sql_query, explain_query, get_all_skills
from .knowledge_tools import query_knowledge, list_topics


class SqlDetectorAgent:
    def __init__(self, config: AgentConfig | None = None):
        if config is None:
            config = AgentConfig()
        
        self.config = config
        self.model = self._create_model(config.model)
        self.toolkit = self._create_toolkit(config.skill)
        self.agent = self._create_agent(config, self.model, self.toolkit)

    def _create_model(self, model_config: ModelConfig):
        if model_config.model_type == "openai":
            return OpenAIChatModel(
                model_name=model_config.model_name,
                api_key=model_config.api_key,
                client_kwargs={"base_url": model_config.model_url} if model_config.model_url else None,
            )
        elif model_config.model_type == "anthropic":
            return AnthropicChatModel(
                model_name=model_config.model_name,
                api_key=model_config.api_key,
            )
        elif model_config.model_type == "dashscope":
            return DashScopeChatModel(
                model_name=model_config.model_name,
                api_key=model_config.api_key,
                base_http_api_url=model_config.model_url,
            )
        elif model_config.model_type == "ollama":
            return OllamaChatModel(
                model_name=model_config.model_name,
                host=model_config.model_url,
            )
        else:
            raise ValueError(f"Unknown model type: {model_config.model_type}")

    def _create_toolkit(self, skill_config) -> Toolkit:
        toolkit = Toolkit()
        
        toolkit.register_tool_function(
            get_db_schema,
            func_description="Get the database schema including tables, columns, indexes and foreign keys",
        )
        toolkit.register_tool_function(
            run_sql_query,
            func_description="Execute a SQL query and return the results in a formatted table",
        )
        toolkit.register_tool_function(
            explain_query,
            func_description="Execute EXPLAIN on a SQL query to show the query execution plan",
        )
        toolkit.register_tool_function(
            get_all_skills,
            func_description="List all available skills in the skill directory",
        )
        toolkit.register_tool_function(
            query_knowledge,
            func_description="Query the SQL performance knowledge base for problem patterns and solutions. Use this when you need to look up how to identify or fix specific SQL performance issues like full table scans, missing indexes, slow queries, etc.",
        )
        toolkit.register_tool_function(
            list_topics,
            func_description="List all available topics in the SQL performance knowledge base",
        )

        if skill_config.enabled and skill_config.skill_dir:
            skill_dir = Path(skill_config.skill_dir)
            if skill_dir.exists():
                toolkit.register_agent_skill(skill_dir=str(skill_dir))

        return toolkit

    def _create_formatter(self, model_type: str):
        """根据模型类型创建对应的 formatter"""
        formatters = {
            "openai": OpenAIChatFormatter,
            "anthropic": AnthropicChatFormatter,
            "dashscope": DashScopeChatFormatter,
            "ollama": OllamaChatFormatter,
        }
        formatter_class = formatters.get(model_type, OpenAIChatFormatter)
        return formatter_class()

    def _create_agent(self, config: AgentConfig, model, toolkit) -> ReActAgent:
        return ReActAgent(
            name=config.name,
            sys_prompt=config.sys_prompt,
            model=model,
            formatter=self._create_formatter(config.model.model_type),
            toolkit=toolkit,
            max_iters=config.max_iters,
        )

    def run(self, query: str) -> str:
        """Run the agent to analyze a SQL query for performance issues."""
        agentscope.init(project="sql-detector")
        
        async def _run():
            msg = Msg(name="user", content=query, role="user")
            response = await self.agent.reply(msg)
            return str(response)
        
        return asyncio.run(_run())


def create_agent(config_path: str | None = None, **kwargs) -> SqlDetectorAgent:
    """Create a SqlDetectorAgent with optional config file and overrides.
    
    Args:
        config_path: Path to a JSON config file.
        **kwargs: Override config values.
    
    Returns:
        A configured SqlDetectorAgent instance.
    """
    from .config import load_config, AgentConfig
    
    if config_path:
        config = load_config(config_path)
    else:
        config = AgentConfig()
    
    for key, value in kwargs.items():
        if hasattr(config, key):
            setattr(config, key, value)
        elif hasattr(config.model, key):
            setattr(config.model, key, value)
    
    return SqlDetectorAgent(config)
