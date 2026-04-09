# SQL Performance Detector Agent

基于 AgentScope 框架的 SQL 性能问题检测 Agent。

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                     SqlDetectorAgent                     │
├─────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐  │
│  │   ReActAgent │  │   Toolkit   │  │   Formatter     │  │
│  │  (推理引擎)  │  │  (工具管理)  │  │  (输出格式化)   │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────────┘  │
│         │               │                               │
│         │         ┌─────┴─────┐                         │
│         │         │  Tools    │                         │
│         │         │───────────│                         │
│         │         │get_schema │ ← skill/get_schema.py  │
│         │         │run_sql    │ ← skill/execute_sql.py │
│         │         │explain    │                         │
│         │         │list_skills│                         │
│         │         └───────────┘                         │
│         │               │                               │
│         │         ┌─────┴─────┐                         │
│         │         │  Skills   │                         │
│         │         │───────────│                         │
│         │         │ skill_dir │ (可选)                  │
│         │         └───────────┘                         │
│         │                                               │
│         ▼                                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │                    Model                          │   │
│  │         (OpenAI / Anthropic / Dashscope / Ollama)  │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
```

## 核心组件

### 1. SqlDetectorAgent (`sql_detector.py`)

主入口类，负责：
- 根据配置创建 Model、Toolkit、Formatter
- 初始化 ReActAgent
- 提供 `run()` 方法执行检测

### 2. Tools (`tools.py`)

Agent 可使用的工具函数：

| 工具 | 功能 | 对应 skill |
|------|------|-----------|
| `get_db_schema` | 获取数据库表结构、索引、外键 | `skill/get_schema.py` |
| `run_sql_query` | 执行 SQL 查询并返回结果 | `skill/execute_sql.py` |
| `explain_query` | 执行 EXPLAIN 查看执行计划 | - |
| `get_all_skills` | 列出可用 skills | - |
| `query_knowledge` | 检索知识库获取性能问题解决方法 | `knowledge/` |
| `list_topics` | 列出知识库可用主题 | `knowledge/` |

### 4. Knowledge Tools (`knowledge_tools.py`)

知识库检索工具，按 `## 二级标题` 拆分知识文档，实现最小化 token 检索：

```python
def query_knowledge(
    query: str,           # 查询问题
    topic: str = None,   # 可选：限定主题
    max_segments: int = 3 # 最多返回片段数
) -> ToolResponse
```

Agent 可在检测过程中主动调用 `query_knowledge` 获取相关知识片段。

### 3. Config (`config.py`)

配置类，包含：
- `ModelConfig`: 模型配置（类型、名称、API Key）
- `SkillConfig`: Skill 配置（目录、启用状态）
- `DatabaseConfig`: 数据库路径
- `AgentConfig`: Agent 整体配置

## 设计思路

### 1. Tool 封装

将 `skill/` 目录下的 Python 脚本封装为 Agent 可调用的 Tool：

```python
# skill/execute_sql.py 是独立可执行的脚本
# tools.py 将其封装为 ToolResponse 返回格式

def run_sql_query(sql: str, limit: int | None = 100) -> ToolResponse:
    result = execute_sql(sql, output_format="table", limit=limit)
    return ToolResponse(content=formatted)
```

### 2. Skill 入口

通过 `Toolkit.register_agent_skill()` 注册 skill 目录：

```python
toolkit.register_agent_skill(
    skill_dir=str(skill_dir),
    name=skill_dir.name,
    description=f"Skill directory: {skill_dir.name}",
)
```

注册后，Agent 系统提示词会自动包含 skill 使用说明。

### 3. Model 适配

支持多种 LLM 后端，通过工厂方法创建：

```python
def _create_model(self, model_config: ModelConfig):
    if model_config.model_type == "openai":
        return OpenAIChatModel(...)
    elif model_config.model_type == "anthropic":
        return AnthropicChatModel(...)
    # ...
```

### 4. 配置驱动

所有配置可通过 `config.json` 文件或命令行参数覆盖：

```json
{
    "name": "sql_detector",
    "model": {
        "model_type": "openai",
        "model_name": "gpt-4",
        "api_key": ""
    },
    "skill": {
        "skill_dir": "skill",
        "enabled": true
    },
    "database": {
        "db_path": "database/ecommerce.db"
    }
}
```

## 检测流程

当 Agent 收到 SQL 检测请求时：

1. **理解 Schema**: 调用 `get_db_schema` 了解表结构
2. **分析 SQL**: 理解查询逻辑
3. **执行计划**: 调用 `explain_query` 查看执行计划
4. **识别问题**: 根据执行计划识别性能问题
5. **给出建议**: 提供优化方案和索引创建 SQL

## 使用方法

### 1. 安装依赖

```bash
pip install -r requirements.txt
# 或使用虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate     # Windows
pip install agentscope
```

### 2. 配置模型

编辑 `config.json` 或通过命令行参数：

```bash
# OpenAI 示例
python agent/run.py --model-url https://api.openai.com/v1 --api-key your-key --model-name gpt-4

# 使用 Ollama (本地)
python agent/run.py --model-type ollama --model-url http://localhost:11434 --model-name llama3 --db-path database/ecommerce.db
```

### 3. 运行 Agent

```bash
# 命令行模式 - 检测单条 SQL
python agent/run.py --query "SELECT * FROM users WHERE email = 'test@example.com'"

# 交互模式
python agent/run.py --interactive

# 使用配置文件
python agent/run.py --config agent/config.json --query "SELECT * FROM orders WHERE user_id = 123"
```

### 4. Python API

```python
from agent import SqlDetectorAgent
from agent.config import AgentConfig

# 方式一：默认配置
agent = SqlDetectorAgent()

# 方式二：自定义配置
config = AgentConfig(
    model_type="openai",
    model_url="https://api.openai.com/v1",
    model_name="gpt-4",
    api_key="your-key"
)
agent = SqlDetectorAgent(config)

# 方式三：从文件加载
from agent.sql_detector import create_agent
agent = create_agent(config_path="agent/config.json")

# 执行检测
result = agent.run("SELECT * FROM users WHERE email = 'test@example.com'")
print(result)
```

## Skill 开发

创建新的 Skill：

1. 在 `skill/` 目录创建子目录
2. 添加 `SKILL.md` 描述 skill 用法
3. Skill 会自动被 `get_all_skills` 工具列出

示例结构：

```
skill/
├── my_skill/
│   ├── SKILL.md          # Skill 描述
│   └── script.py         # 实现脚本
└── another_skill/
    ├── SKILL.md
    └── ...
```

## 扩展

### 添加新的 Tool

在 `tools.py` 中添加函数，并用 `@toolkit.register_tool_function` 注册：

```python
def my_new_tool(arg1: str) -> ToolResponse:
    """工具描述"""
    # 实现
    return ToolResponse(content="result")

# 在 _create_toolkit 中注册
toolkit.register_tool_function(my_new_tool, ...)
```

### 添加新的 Model

在 `config.py` 添加新的 model_type，并在 `_create_model` 中实现创建逻辑。
