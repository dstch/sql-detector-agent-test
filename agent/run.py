import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.sql_detector import create_agent
from agent.config import AgentConfig


def main():
    parser = argparse.ArgumentParser(description="SQL Performance Detector Agent")
    parser.add_argument("--config", "-c", type=str, help="Path to config file")
    parser.add_argument("--query", "-q", type=str, help="SQL query to analyze")
    parser.add_argument("--model-type", "-m", type=str, choices=["openai", "anthropic", "dashscope", "ollama"],
                        help="Model type")
    parser.add_argument("--model-url", "-u", type=str, help="Model API URL (e.g., https://api.openai.com/v1)")
    parser.add_argument("--model-name", "-n", type=str, help="Model name")
    parser.add_argument("--api-key", "-k", type=str, help="API key")
    parser.add_argument("--db-path", "-d", type=str, help="Database path")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    
    args = parser.parse_args()
    
    config_overrides = {}
    if args.model_type:
        config_overrides["model_type"] = args.model_type
    if args.model_url:
        config_overrides["model_url"] = args.model_url
    if args.model_name:
        config_overrides["model_name"] = args.model_name
    if args.api_key:
        config_overrides["api_key"] = args.api_key
    if args.db_path:
        config_overrides["db_path"] = args.db_path
    
    agent = create_agent(config_path=args.config, **config_overrides)
    
    if args.interactive:
        print("SQL Performance Detector Agent (type 'exit' to quit)")
        print("-" * 50)
        while True:
            query = input("\nEnter SQL query to analyze: ")
            if query.lower() in ["exit", "quit"]:
                break
            print("\n" + "=" * 50)
            result = agent.run(query)
            print(result)
    elif args.query:
        result = agent.run(args.query)
        print(result)
    else:
        print("Error: Please provide --query or use --interactive mode")
        sys.exit(1)


if __name__ == "__main__":
    main()
