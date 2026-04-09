# SQL Performance Detector

> ⚠️ **这是一个练习小项目**：用于学习和实践 AgentScope 框架、SQL 性能检测知识库检索、ReAct Agent 开发。

基于 AgentScope 框架的 SQL 性能问题检测 Agent，支持通过知识库检索和执行计划分析识别常见性能问题。

## 项目结构

```
sql-detector/
├── agent/                    # Agent 实现
│   ├── __init__.py
│   ├── config.py            # 配置类
│   ├── config.json          # 用户配置（不提交）
│   ├── config.template.json # 配置模板
│   ├── knowledge_tools.py   # 知识库检索工具
│   ├── README.md            # Agent 详细文档
│   ├── run.py               # Agent 运行入口
│   ├── sql_detector.py      # 主 Agent 类
│   └── tools.py             # 数据库工具封装
├── database/                # 测试数据库
│   └── ecommerce.db        # SQLite 测试库
├── knowledge/               # 性能问题知识库
│   ├── 00-index.md
│   ├── 01-full-table-scan.md
│   ├── 02-missing-index.md
│   ├── 03-slow-query.md
│   ├── 04-select-star.md
│   ├── 05-no-pagination.md
│   ├── 06-n-plus-one.md
│   └── 07-explain-plan.md
├── skill/                   # Skill 脚本
│   ├── get_schema.py        # 获取数据库结构
│   └── execute_sql.py       # 执行 SQL 查询
├── test/                    # 测试套件
│   ├── conftest.py
│   ├── test_sql_detector.py
│   └── README.md
├── note.md                  # SQL 性能问题记录
├── README.md               # 本文件
└── .gitignore
```

## 快速开始

### 1. 安装依赖

```bash
pip install agentscope pytest
```

### 2. 配置

复制配置模板并编辑：

```bash
cp agent/config.template.json agent/config.json
# 编辑 config.json 填入你的 API Key
```

或使用命令行参数：

```bash
python agent/run.py \
    --model-url https://api.openai.com/v1 \
    --api-key your-api-key \
    --query "SELECT * FROM users WHERE email = 'test@example.com'"
```

### 3. 运行测试

```bash
# 运行所有测试
python -m pytest test/ -v

# 运行不需要 API 的测试
python -m pytest test/ -v -k "not agent_analyze"
```

### 4. 运行 Agent

```bash
# 单条 SQL 分析
python agent/run.py --query "SELECT * FROM orders WHERE user_id = 123"

# 交互模式
python agent/run.py --interactive
```

## 功能特性

### 支持的检测场景

| 问题类型 | 说明 |
|---------|------|
| 全表扫描 | 识别无索引导致的 SCAN |
| 缺失索引 | 检测 WHERE/JOIN/ORDER BY 字段无索引 |
| 慢查询 | 分析查询执行效率 |
| SELECT * | 识别过度查询字段 |
| 缺乏分页 | 检测大结果集无 LIMIT |
| N+1 查询 | 识别循环查询模式 |
| 执行计划分析 | 通过 EXPLAIN QUERY PLAN 分析 |

### 工具函数

| 工具 | 功能 |
|------|------|
| `get_db_schema` | 获取数据库表结构、索引、外键 |
| `run_sql_query` | 执行 SQL 查询 |
| `explain_query` | 执行 EXPLAIN 查看执行计划 |
| `query_knowledge` | 检索知识库获取解决方案 |
| `list_topics` | 列出知识库可用主题 |

## 配置说明

### Model 配置

```json
{
    "model_type": "openai",
    "model_url": "https://api.openai.com/v1",
    "api_key": "",
    "model_name": "gpt-4"
}
```

支持的模型类型：
- `openai` - OpenAI GPT 系列
- `anthropic` - Anthropic Claude 系列
- `dashscope` - 阿里云通义千问
- `ollama` - 本地 Ollama 模型

### 数据库配置

```json
{
    "db_path": "database/ecommerce.db"
}
```

## 测试数据库

位于 `database/ecommerce.db`，包含以下测试表：

| 表名 | 记录数 | 说明 |
|------|-------|------|
| users | 1000 | 用户表（email 无索引） |
| orders | 5000 | 订单表（user_id/created_at 无索引） |
| order_items | 15000 | 订单详情表（order_id 无索引） |
| products | 500 | 产品表（category 无索引） |

## 知识库

位于 `knowledge/` 目录，包含 7 个性能问题场景的详细知识：

1. 全表扫描识别与解决
2. 索引设计原则
3. 慢查询分析与优化
4. SELECT * 问题
5. 缺乏分页处理
6. N+1 查询问题
7. EXPLAIN 执行计划分析

## 开发

### 添加新的 Tool

在 `agent/tools.py` 中添加函数：

```python
from agentscope.tool import ToolResponse

def my_tool(arg1: str) -> ToolResponse:
    """工具描述"""
    return ToolResponse(content="result")
```

在 `sql_detector.py` 的 `_create_toolkit` 中注册：

```python
toolkit.register_tool_function(my_tool, func_description="...")
```

### 添加知识库内容

在 `knowledge/` 目录添加 `.md` 文件，使用 `## 二级标题` 划分知识片段。

## License

MIT
