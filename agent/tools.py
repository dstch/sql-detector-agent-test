import json
import sys
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).parent.parent))

from skill.get_schema import get_schema
from skill.execute_sql import execute_sql
from agentscope.tool import ToolResponse


def get_db_schema(table_name: str | None = None) -> ToolResponse:
    """Get the database schema including tables, columns, indexes and foreign keys.

    Args:
        table_name: Optional. Specific table name to get schema for. If not provided,
                   returns schema for all tables.

    Returns:
        A ToolResponse containing the database schema in JSON format.
    """
    try:
        schema = get_schema()
        
        if table_name:
            if table_name in schema["tables"]:
                schema = {"tables": {table_name: schema["tables"][table_name]}}
            else:
                return ToolResponse(
                    content=f"Table '{table_name}' not found. Available tables: {list(schema['tables'].keys())}"
                )
        
        return ToolResponse(content=json.dumps(schema, indent=2))
    except Exception as e:
        return ToolResponse(content=f"Error getting schema: {str(e)}")


def run_sql_query(sql: str, limit: int | None = 100) -> ToolResponse:
    """Execute a SQL query and return the results.

    Args:
        sql: The SQL query to execute.
        limit: Maximum number of rows to return (default 100). Set to None for no limit.

    Returns:
        A ToolResponse containing the query results in a formatted table.
    """
    try:
        if limit:
            result = execute_sql(sql, output_format="table", limit=limit)
        else:
            result = execute_sql(sql, output_format="table", limit=None)
        
        formatted = result if isinstance(result, str) else json.dumps(result, indent=2)
        return ToolResponse(content=formatted)
    except Exception as e:
        return ToolResponse(content=f"Error executing SQL: {str(e)}")


def explain_query(sql: str) -> ToolResponse:
    """Execute EXPLAIN on a SQL query to show the query execution plan.

    Args:
        sql: The SQL query to explain.

    Returns:
        A ToolResponse containing the EXPLAIN output showing how the query will be executed.
    """
    try:
        explain_sql = f"EXPLAIN QUERY PLAN {sql}"
        result = execute_sql(explain_sql, output_format="table", limit=None)
        
        formatted = result if isinstance(result, str) else json.dumps(result, indent=2)
        return ToolResponse(content=formatted)
    except Exception as e:
        return ToolResponse(content=f"Error explaining query: {str(e)}")


def get_all_skills(skill_dir: str | None = None) -> ToolResponse:
    """List all available skills in the skill directory.

    Args:
        skill_dir: The directory containing skills. If not provided, uses the default skill directory.

    Returns:
        A ToolResponse containing the list of available skills and their descriptions.
    """
    try:
        if skill_dir is None:
            skill_dir = Path(__file__).parent.parent / "skill"
        else:
            skill_dir = Path(skill_dir)
        
        if not skill_dir.exists():
            return ToolResponse(content=f"Skill directory not found: {skill_dir}")
        
        skills = []
        for item in skill_dir.iterdir():
            if item.is_dir():
                skill_md = item / "SKILL.md"
                if skill_md.exists():
                    desc = skill_md.read_text(encoding="utf-8").split("\n")[0].replace("# ", "")
                    skills.append(f"- {item.name}: {desc}")
                else:
                    skills.append(f"- {item.name}: (no description)")
        
        if not skills:
            return ToolResponse(content="No skills found in the skill directory.")
        
        return ToolResponse(content="Available skills:\n" + "\n".join(skills))
    except Exception as e:
        return ToolResponse(content=f"Error listing skills: {str(e)}")
