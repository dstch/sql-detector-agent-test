import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import pytest


@pytest.fixture(scope="session")
def db_path():
    """数据库路径 fixture"""
    return str(Path(__file__).parent.parent / "database" / "ecommerce.db")


@pytest.fixture(scope="session")
def agent_config(db_path):
    """Agent 配置 fixture"""
    from agent.config import AgentConfig, ModelConfig
    return AgentConfig(
        name="sql_detector_test",
        model=ModelConfig(
            model_type="openai",
            model_name="gpt-4",
            api_key="test-key-for-mock",
        ),
        database={"db_path": db_path},
    )


@pytest.fixture
def sql_detector(agent_config):
    """SqlDetectorAgent fixture"""
    from agent.sql_detector import SqlDetectorAgent
    return SqlDetectorAgent(config=agent_config)
