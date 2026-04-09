# SQL Detector 测试套件

## 运行测试

```bash
# 运行所有测试
python -m pytest test/ -v

# 运行特定测试类
python -m pytest test/test_sql_detector.py::TestSqlPerformancePatterns -v

# 排除需要 API 的测试
python -m pytest test/ -v -k "not agent_analyze"
```

## 测试结构

```
test/
├── __init__.py
├── conftest.py              # pytest fixtures
├── test_sql_detector.py      # 主测试文件
└── README.md
```

## 测试类说明

### TestSqlDetector
需要 API Key 的完整 Agent 测试：

| 测试方法 | 说明 |
|---------|------|
| `test_01_get_schema` | 获取数据库结构 |
| `test_02_explain_query` | EXPLAIN 全表扫描分析 |
| `test_03_explain_query_with_index` | EXPLAIN 索引查询分析 |
| `test_04_query_knowledge` | 知识库检索 |
| `test_05_agent_analyze_full_scan` | Agent 分析全表扫描 |
| `test_06_agent_analyze_orders_query` | Agent 分析订单查询 |
| `test_07_agent_analyze_select_star` | Agent 分析 SELECT * |

### TestSqlDetectorWithMock
无需 API 的工具测试：

| 测试方法 | 说明 |
|---------|------|
| `test_knowledge_retrieval_comprehensive` | 知识库检索覆盖测试 |
| `test_segment_scoring` | 片段评分逻辑测试 |

### TestSqlPerformancePatterns
SQL 性能问题模式验证：

| 测试方法 | 说明 |
|---------|------|
| `test_all_problem_queries_from_note` | 验证 note.md 中所有问题 SQL 均被检测为全表扫描 |

## Fixtures

`conftest.py` 提供以下 fixtures：

- `db_path`: 数据库路径
- `agent_config`: Agent 配置
- `sql_detector`: SqlDetectorAgent 实例

## 示例：添加新测试

```python
def test_new_pattern(sql_detector):
    """测试新的 SQL 性能问题模式"""
    from agent.tools import explain_query
    
    sql = "SELECT * FROM table WHERE column = 'value'"
    result = explain_query(sql)
    
    assert "SCAN" in result.content
```

## 依赖

```
pytest>=9.0
agentscope
```
