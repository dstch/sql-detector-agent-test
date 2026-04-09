import sqlite3
import json
import sys
import csv
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "ecommerce.db"

def execute_sql(sql, db_path=None, output_format="table", limit=100):
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute(sql)
        
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            rows = cursor.fetchall()
            
            if limit and len(rows) > limit:
                rows = rows[:limit]
                truncated = True
            else:
                truncated = False
            
            if output_format == "json":
                result = {
                    "columns": columns,
                    "rows": [dict(zip(columns, row)) for row in rows],
                    "row_count": len(rows),
                    "truncated": truncated
                }
            elif output_format == "csv":
                result = {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "truncated": truncated
                }
            else:
                result = {
                    "columns": columns,
                    "rows": rows,
                    "row_count": len(rows),
                    "truncated": truncated
                }
        else:
            result = {
                "row_count": cursor.rowcount,
                "message": "Query executed successfully"
            }
            
    except sqlite3.Error as e:
        conn.close()
        raise Exception(f"SQL Error: {e}")
    
    conn.close()
    return result

def format_table(result):
    if "columns" not in result:
        return result.get("message", "Done")
    
    columns = result["columns"]
    rows = result["rows"]
    
    col_widths = [len(str(c)) for c in columns]
    for row in rows:
        for i, val in enumerate(row):
            col_widths[i] = max(col_widths[i], len(str(val)))
    
    header = " | ".join(str(col).ljust(col_widths[i]) for i, col in enumerate(columns))
    separator = "-+-".join("-" * w for w in col_widths)
    
    lines = [header, separator]
    for row in rows:
        lines.append(" | ".join(str(val).ljust(col_widths[i]) for i, val in enumerate(row)))
    
    info = f"{result['row_count']} rows"
    if result.get("truncated"):
        info += " (truncated)"
    
    return "\n".join(lines) + f"\n\n[{info}]"

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Execute SQL query")
    parser.add_argument("--db", default=None, help="Database path")
    parser.add_argument("--sql", "-s", default=None, help="SQL query to execute")
    parser.add_argument("--file", "-f", default=None, help="SQL file to execute")
    parser.add_argument("--format", "-o", choices=["table", "json", "csv"], default="table", help="Output format")
    parser.add_argument("--limit", "-l", type=int, default=100, help="Row limit")
    parser.add_argument("--no-limit", action="store_true", help="No row limit")
    args = parser.parse_args()
    
    if args.no_limit:
        args.limit = None
    
    if args.file:
        sql = Path(args.file).read_text()
    elif args.sql:
        sql = args.sql
    else:
        print("Error: must specify --sql or --file", file=sys.stderr)
        sys.exit(1)
    
    try:
        result = execute_sql(sql, args.db, args.format, args.limit)
        
        if args.format == "json":
            print(json.dumps(result, indent=2, default=str))
        elif args.format == "csv":
            if "columns" in result:
                writer = csv.writer(sys.stdout)
                writer.writerow(result["columns"])
                writer.writerows(result["rows"])
        else:
            print(format_table(result))
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
