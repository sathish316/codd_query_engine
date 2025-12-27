"""
Main entry point for the metrics semantic indexer job.

Usage (Indexing Mode):
    python -m maverick_jobs.metrics_semantic_indexer_main \\
        --namespace "production:order-service" \\
        --promql-url "http://localhost:9090" \\
        --redis-host "localhost" \\
        --redis-port 6379 \\
        --chromadb-host "localhost" \\
        --chromadb-port 8000 \\
        --batch-size 10 \\
        --limit 100

Usage (Indexing with Exclusions):
    python -m maverick_jobs.metrics_semantic_indexer_main \\
        --namespace "production:order-service" \\
        --promql-url "http://localhost:9090" \\
        --exclude-pattern "^(go_|process_|promhttp_)" \\
        --redis-host "localhost" \\
        --redis-port 6379 \\
        --chromadb-host "localhost" \\
        --chromadb-port 8000

Usage (Query Mode):
    python -m maverick_jobs.metrics_semantic_indexer_main \\
        --query "memory usage metrics" \\
        --query-limit 5 \\
        --chromadb-host "localhost" \\
        --chromadb-port 8000
"""

import argparse
import json
import logging
import sys

import chromadb
import redis

from maverick_jobs.metrics_semantic_indexer_job import MetricsSemanticIndexerJob
from maverick_dal.metrics.metrics_semantic_metadata_store import (
    MetricsSemanticMetadataStore,
)

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("metrics_semantic_indexer.log"),
    ],
)

logger = logging.getLogger(__name__)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Metrics Semantic Indexer - Offline job for enriching and indexing metrics metadata"
    )

    parser.add_argument(
        "--namespace",
        type=str,
        required=True,
        help="Namespace for metrics (format: tenant:service, e.g., production:order-service)",
    )

    parser.add_argument(
        "--promql-url",
        type=str,
        default="http://localhost:9090",
        help="Prometheus base URL (default: http://localhost:9090)",
    )

    parser.add_argument(
        "--redis-host",
        type=str,
        default="localhost",
        help="Redis host (default: localhost)",
    )

    parser.add_argument(
        "--redis-port", type=int, default=6379, help="Redis port (default: 6379)"
    )

    parser.add_argument(
        "--redis-db", type=int, default=0, help="Redis database number (default: 0)"
    )

    parser.add_argument(
        "--chromadb-host",
        type=str,
        default="localhost",
        help="ChromaDB host (default: localhost)",
    )

    parser.add_argument(
        "--chromadb-port", type=int, default=8000, help="ChromaDB port (default: 8000)"
    )

    parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of metrics to process in each batch (default: 10)",
    )

    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Limit number of metrics to process (for testing, default: no limit)",
    )

    parser.add_argument(
        "--exclude-pattern",
        type=str,
        default=None,
        help="Regex pattern to exclude metrics (e.g., '^go_.*' to exclude Go runtime metrics)",
    )

    parser.add_argument(
        "--skip-if-present",
        action="store_true",
        help="Skip metrics that are already present in the semantic store (default: False)",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Dry run mode: display metrics without performing LLM enrichment or indexing (default: False)",
    )

    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="Query mode: search for metrics by name or description and display results as JSON (skips indexing)",
    )

    parser.add_argument(
        "--query-limit",
        type=int,
        default=10,
        help="Number of results to return for query mode (default: 10, max: 100)",
    )

    parser.add_argument(
        "--log-level",
        type=str,
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        help="Logging level (default: INFO)",
    )

    return parser.parse_args()


def initialize_clients(args):
    """
    Initialize Redis and ChromaDB clients.

    Args:
        args: Parsed command line arguments

    Returns:
        Tuple of (redis_client, chromadb_client)
    """
    try:
        # Initialize Redis client
        redis_client = redis.Redis(
            host=args.redis_host,
            port=args.redis_port,
            db=args.redis_db,
            decode_responses=True,
        )

        # Test Redis connection
        redis_client.ping()
        logger.info(f"Connected to Redis at {args.redis_host}:{args.redis_port}")

        # Initialize ChromaDB client
        chromadb_client = chromadb.HttpClient(
            host=args.chromadb_host,
            port=args.chromadb_port,
        )

        # Test ChromaDB connection
        chromadb_client.heartbeat()
        logger.info(
            f"Connected to ChromaDB at {args.chromadb_host}:{args.chromadb_port}"
        )

        return redis_client, chromadb_client

    except redis.ConnectionError as e:
        logger.error(f"Failed to connect to Redis: {e}")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to connect to ChromaDB: {e}")
        sys.exit(1)


def initialize_agent_managers():
    """
    Initialize configuration and instructions managers for the LLM agent.

    Returns:
        Tuple of (config_manager, instructions_manager)
    """
    try:
        config_manager = ConfigManager()
        instructions_manager = InstructionsManager()

        logger.info("Initialized agent configuration and instructions managers")

        return config_manager, instructions_manager

    except Exception as e:
        logger.error(f"Failed to initialize agent managers: {e}")
        sys.exit(1)


def run_query_mode(query: str, limit: int, chromadb_client: chromadb.ClientAPI):
    """
    Run query mode to search for metrics and display results.

    Args:
        query: Search query string
        limit: Maximum number of results to return
        chromadb_client: ChromaDB client instance
    """
    print(f"\n{'=' * 70}")
    print("METRICS SEMANTIC SEARCH")
    print(f"{'=' * 70}")
    print(f"Query: {query}")
    print(f"Limit: {limit}")
    print(f"{'=' * 70}\n")

    try:
        # Initialize semantic store
        semantic_store = MetricsSemanticMetadataStore(chromadb_client)

        # Perform search
        print(f"Searching for metrics matching: '{query}'...\n")
        results = semantic_store.search_metadata(query, n_results=limit)

        if not results:
            print("No results found.\n")
            return

        print(f"Found {len(results)} result(s):\n")
        print(f"{'=' * 70}\n")

        # Display results as pretty-printed JSON
        for i, result in enumerate(results, 1):
            print(f"Result #{i}:")
            print(f"{'-' * 70}")
            print(json.dumps(result, indent=2, ensure_ascii=False))
            print(f"{'-' * 70}\n")

        # Summary
        print(f"{'=' * 70}")
        print(f"Total Results: {len(results)}")
        print(f"{'=' * 70}\n")

        logger.info(f"Query completed successfully, found {len(results)} results")

    except Exception as e:
        logger.error(f"Query failed: {e}", exc_info=True)
        print(f"\n✗ ERROR: {e}\n")
        raise


def main():
    """Main entry point for the indexer job."""
    args = parse_args()

    # Set log level
    logging.getLogger().setLevel(args.log_level)

    # Query mode: search and display results
    if args.query:
        logger.info("=" * 70)
        logger.info("Metrics Semantic Search Query Mode")
        logger.info("=" * 70)
        logger.info(f"Query: {args.query}")
        logger.info(f"Limit: {args.query_limit}")
        logger.info(f"ChromaDB: {args.chromadb_host}:{args.chromadb_port}")
        logger.info("=" * 70)

        try:
            # Initialize ChromaDB client only
            chromadb_client = chromadb.HttpClient(
                host=args.chromadb_host,
                port=args.chromadb_port,
            )
            chromadb_client.heartbeat()
            logger.info(
                f"Connected to ChromaDB at {args.chromadb_host}:{args.chromadb_port}"
            )

            # Run query
            run_query_mode(args.query, args.query_limit, chromadb_client)
            sys.exit(0)

        except Exception as e:
            logger.error(f"Query failed: {e}", exc_info=True)
            sys.exit(1)

    # Normal indexing mode
    logger.info("=" * 70)
    logger.info("Starting Metrics Semantic Indexer Job")
    logger.info("=" * 70)
    logger.info(f"Namespace: {args.namespace}")
    logger.info(f"Prometheus URL: {args.promql_url}")
    logger.info(f"Redis: {args.redis_host}:{args.redis_port}/{args.redis_db}")
    logger.info(f"ChromaDB: {args.chromadb_host}:{args.chromadb_port}")
    logger.info(f"Batch Size: {args.batch_size}")
    logger.info(f"Limit: {args.limit if args.limit else 'None (all metrics)'}")
    logger.info(
        f"Exclude Pattern: {args.exclude_pattern if args.exclude_pattern else 'None'}"
    )
    logger.info(f"Skip if Present: {args.skip_if_present}")
    logger.info(f"Dry Run: {args.dry_run}")
    logger.info("=" * 70)

    try:
        # Initialize clients
        redis_client, chromadb_client = initialize_clients(args)

        # Initialize agent managers
        config_manager, instructions_manager = initialize_agent_managers()

        # Create indexer job
        indexer = MetricsSemanticIndexerJob(
            promql_base_url=args.promql_url,
            redis_client=redis_client,
            chromadb_client=chromadb_client,
            config_manager=config_manager,
            instructions_manager=instructions_manager,
            batch_size=args.batch_size,
        )

        # Run the job
        indexer.run(
            namespace=args.namespace,
            limit=args.limit,
            exclude_pattern=args.exclude_pattern,
            skip_if_present=args.skip_if_present,
            dry_run=args.dry_run,
        )

        logger.info("Metrics semantic indexer job completed successfully")
        sys.exit(0)

    except KeyboardInterrupt:
        logger.warning("Job interrupted by user")
        sys.exit(130)

    except Exception as e:
        logger.error(f"Job failed with error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    # To run the job in indexing mode
    # uv run -m maverick_jobs.metrics_semantic_indexer_main --namespace "default:beer-service" --promql-url "http://localhost:9090" --redis-host "localhost" --redis-port 6380 --chromadb-host "localhost" --chromadb-port 8000 --batch-size 10 --limit 400 --skip-if-present --exclude-pattern "^(go|prometheus)"
    # To run the job in query mode
    # uv run -m maverick_jobs.metrics_semantic_indexer_main --namespace "default:beer-service" --promql-url "http://localhost:9090" --redis-host "localhost" --redis-port 6380 --chromadb-host "localhost" --chromadb-port 8000 --query beer --query-limit 5
    main()
