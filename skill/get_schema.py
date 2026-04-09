import sqlite3
import json
import sys
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "database" / "ecommerce.db"

def get_table_info(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = []
    for col in cursor.fetchall():
        columns.append({
            "cid": col[0],
            "name": col[1],
            "type": col[2],
            "notnull": col[3],
            "dflt_value": col[4],
            "pk": col[5]
        })
    return columns

def get_indexes(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = []
    for idx in cursor.fetchall():
        index_name = idx[1]
        cursor.execute(f"PRAGMA index_info({index_name})")
        columns = [col[2] for col in cursor.fetchall()]
        indexes.append({
            "name": index_name,
            "table": idx[0],
            "unique": bool(idx[2]),
            "columns": columns
        })
    return indexes

def get_foreign_keys(conn, table_name):
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    fks = []
    for fk in cursor.fetchall():
        fks.append({
            "id": fk[0],
            "seq": fk[1],
            "table": fk[2],
            "from": fk[3],
            "to": fk[4]
        })
    return fks

def get_schema(db_path=None):
    if db_path is None:
        db_path = DB_PATH
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]
    
    schema = {
        "database": str(db_path),
        "tables": {}
    }
    
    for table_name in tables:
        schema["tables"][table_name] = {
            "columns": get_table_info(conn, table_name),
            "indexes": get_indexes(conn, table_name),
            "foreign_keys": get_foreign_keys(conn, table_name)
        }
    
    conn.close()
    return schema

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Get database schema")
    parser.add_argument("--db", default=None, help="Database path")
    parser.add_argument("--table", default=None, help="Specific table name")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()
    
    schema = get_schema(args.db)
    
    if args.table:
        if args.table in schema["tables"]:
            schema = {"tables": {args.table: schema["tables"][args.table]}}
        else:
            print(f"Table '{args.table}' not found", file=sys.stderr)
            sys.exit(1)
    
    if args.json:
        print(json.dumps(schema, indent=2))
    else:
        for table_name, info in schema["tables"].items():
            print(f"\n=== Table: {table_name} ===")
            print(f"Columns ({len(info['columns'])}):")
            for col in info["columns"]:
                pk = " PK" if col["pk"] else ""
                print(f"  {col['name']}: {col['type']}{pk}")
            
            if info["indexes"]:
                print(f"Indexes ({len(info['indexes'])}):")
                for idx in info["indexes"]:
                    unique = "UNIQUE " if idx["unique"] else ""
                    print(f"  {idx['name']}: {unique}{idx['columns']}")
            else:
                print("Indexes: None")
            
            if info["foreign_keys"]:
                print(f"Foreign Keys ({len(info['foreign_keys'])}):")
                for fk in info["foreign_keys"]:
                    print(f"  {fk['from']} -> {fk['table']}.{fk['to']}")

if __name__ == "__main__":
    main()
