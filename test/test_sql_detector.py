import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import unittest
from agent.sql_detector import SqlDetectorAgent
from agent.config import AgentConfig, ModelConfig


class TestSqlDetector(unittest.TestCase):
    """SQL 性能检测 Agent 测试用例"""

    @classmethod
    def setUpClass(cls):
        """初始化测试环境"""
        from agent.config import load_config
        
        cls.db_path = str(Path(__file__).parent.parent / "database" / "ecommerce.db")
        
        config = load_config(str(Path(__file__).parent.parent / "agent" / "config.json"))
        config.name = "sql_detector_test"
        config.database.db_path = cls.db_path
        
        cls.agent = SqlDetectorAgent(config=config)

    def test_01_get_schema(self):
        """测试：获取数据库结构"""
        from agent.tools import get_db_schema

        result = get_db_schema()
        self.assertIsNotNone(result.content)

        import json
        schema = json.loads(result.content)
        self.assertIn("tables", schema)
        self.assertIn("users", schema["tables"])
        self.assertIn("orders", schema["tables"])
        print("\n=== Schema Test Passed ===")

    def test_02_explain_query(self):
        """测试：EXPLAIN 查询分析"""
        from agent.tools import explain_query

        sql = 'SELECT * FROM users WHERE email = "user1@example.com"'
        result = explain_query(sql)
        self.assertIsNotNone(result.content)
        self.assertIn("SCAN", result.content)
        print("\n=== EXPLAIN Test Passed (Full Table Scan Detected) ===")

    def test_03_explain_query_with_index(self):
        """测试：带索引字段的查询分析"""
        from agent.tools import explain_query

        sql = "SELECT * FROM users WHERE id = 1"
        result = explain_query(sql)
        self.assertIsNotNone(result.content)
        print(f"\n=== EXPLAIN for ID query ===\n{result.content}")

    def test_04_query_knowledge(self):
        """测试：知识库检索"""
        from agent.knowledge_tools import query_knowledge, list_topics

        result = query_knowledge("全表扫描识别")
        self.assertIsNotNone(result.content)
        self.assertTrue(len(result.content) > 0)
        print(f"\n=== Knowledge Query Result ===\n{result.content[:300]}...")

        topics = list_topics()
        self.assertIsNotNone(topics.content)
        print(f"\n=== Available Topics ===\n{topics.content}")

    def test_05_agent_analyze_full_scan(self):
        """测试：Agent 分析全表扫描问题"""
        sql = 'SELECT * FROM users WHERE email = "test@example.com"'

        response = self.agent.run(sql)

        self.assertIsNotNone(response)
        print(f"\n=== Agent Analysis Result ===\n{response}")

    def test_06_agent_analyze_orders_query(self):
        """测试：Agent 分析订单查询性能问题"""
        sql = "SELECT * FROM orders WHERE user_id = 123 AND created_at BETWEEN '2024-01-01' AND '2024-12-31'"

        response = self.agent.run(sql)

        self.assertIsNotNone(response)
        print(f"\n=== Agent Orders Query Analysis ===\n{response}")

    def test_07_agent_analyze_select_star(self):
        """测试：Agent 分析 SELECT * 问题"""
        sql = "SELECT * FROM products WHERE category = 'electronics'"

        response = self.agent.run(sql)

        self.assertIsNotNone(response)
        print(f"\n=== Agent SELECT * Analysis ===\n{response}")


class TestSqlDetectorWithMock(unittest.TestCase):
    """使用 Mock Model 的测试（不消耗 API）"""

    def test_knowledge_retrieval_comprehensive(self):
        """测试：知识库检索 - 覆盖多个主题"""
        from agent.knowledge_tools import query_knowledge

        test_cases = [
            ("全表扫描", "full-table-scan"),
            ("索引缺失", "missing-index"),
            ("慢查询", "slow-query"),
            ("SELECT *", "select-star"),
            ("分页", "no-pagination"),
            ("N+1", "n-plus-one"),
            ("EXPLAIN", "explain-plan"),
        ]

        for query, expected_topic in test_cases:
            result = query_knowledge(query)
            self.assertIsNotNone(result.content, f"Failed for query: {query}")
            self.assertTrue(
                len(result.content) > 0,
                f"No content returned for query: {query}"
            )
            print(f"\n=== Query: {query} ===")
            print(result.content[:200])

    def test_segment_scoring(self):
        """测试：片段评分逻辑"""
        from agent.knowledge_tools import KnowledgeSegment

        seg = KnowledgeSegment(
            title="全表扫描识别",
            content="SCAN table_name 表示全表扫描",
            topic="full-table-scan",
            source_file="test.md"
        )

        score1 = seg.match_score(["全表扫描", "识别"])
        score2 = seg.match_score(["索引"])
        score3 = seg.match_score(["SCAN"])

        self.assertGreater(score1, 0)
        self.assertEqual(score2, 0)
        self.assertGreater(score3, 0)
        print(f"\n=== Score Test ===")
        print(f"Score for ['全表扫描', '识别']: {score1}")
        print(f"Score for ['索引']: {score2}")
        print(f"Score for ['SCAN']: {score3}")


class TestSqlPerformancePatterns(unittest.TestCase):
    """SQL 性能问题模式测试"""

    def test_all_problem_queries_from_note(self):
        """测试：验证 note.md 中的所有性能问题 SQL"""
        from agent.tools import explain_query

        problem_queries = [
            ('SELECT * FROM users WHERE email = "user123@example.com"', "邮箱查询全表扫描"),
            ("SELECT * FROM orders WHERE user_id = 123", "用户订单查询全表扫描"),
            ("SELECT * FROM orders WHERE created_at BETWEEN '2024-01-01' AND '2024-12-31'", "日期范围慢查询"),
            ("SELECT * FROM order_items WHERE order_id = 456", "订单详情全表扫描"),
            ("SELECT * FROM products WHERE category = 'electronics'", "缺乏分页全表扫描"),
        ]

        for sql, description in problem_queries:
            result = explain_query(sql)
            print(f"\n=== {description} ===")
            print(f"SQL: {sql}")
            print(f"Plan: {result.content}")
            self.assertIn("SCAN", result.content, f"Expected SCAN for: {description}")


if __name__ == "__main__":
    print("=" * 60)
    print("SQL Detector Agent Test Suite")
    print("=" * 60)

    unittest.main(verbosity=2)
