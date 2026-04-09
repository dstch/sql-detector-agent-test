from pathlib import Path
from typing import Literal
from pydantic import BaseModel


class ModelConfig(BaseModel):
    model_type: Literal["openai", "anthropic", "dashscope", "ollama"] = "openai"
    model_url: str = "https://api.openai.com/v1"
    api_key: str = ""
    model_name: str = "gpt-4"


class SkillConfig(BaseModel):
    skill_dir: str | None = None
    enabled: bool = True


class DatabaseConfig(BaseModel):
    db_path: str = "database/ecommerce.db"


class AgentConfig(BaseModel):
    name: str = "sql_detector"
    sys_prompt: str = """You are a SQL performance expert. Your task is to analyze SQL queries and identify performance issues.
You have access to tools that can:
1. Get the database schema (tables, indexes, foreign keys)
2. Execute SQL queries

When analyzing SQL for performance issues, you should:
1. First understand the database schema
2. Analyze the SQL query structure
3. Execute EXPLAIN or the query to see the execution plan
4. Check for missing indexes on columns used in WHERE, JOIN, ORDER BY
5. Identify full table scans, SELECT * issues, lack of pagination, etc.

Provide specific recommendations with the SQL to create missing indexes if needed."""

    model: ModelConfig = ModelConfig()
    skill: SkillConfig = SkillConfig()
    database: DatabaseConfig = DatabaseConfig()
    max_iters: int = 10


def load_config(config_path: str | None = None) -> AgentConfig:
    if config_path and Path(config_path).exists():
        import json
        with open(config_path) as f:
            return AgentConfig(**json.load(f))
    return AgentConfig()
