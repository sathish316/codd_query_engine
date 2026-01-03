"""
Example usage of the Metrics Semantic Indexer Job.

This script demonstrates how to use the indexer programmatically
instead of via the CLI.
"""

import logging

import chromadb
import redis

from maverick_jobs.metrics_semantic_indexer_job import MetricsSemanticIndexerJob

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


def main():
    """Example usage of the semantic indexer job."""

    # Configuration
    namespace = "test:example-service"
    promql_url = "http://localhost:9090"
    redis_host = "localhost"
    redis_port = 6380
    chromadb_host = "localhost"
    chromadb_port = 8000
    batch_size = 5
    limit = 20  # Process only 20 metrics for testing

    logger.info("Initializing clients...")

    # Initialize Redis client
    redis_client = redis.Redis(
        host=redis_host,
        port=redis_port,
        db=0,
        decode_responses=True,
    )

    # Test Redis connection
    try:
        redis_client.ping()
        logger.info(f"✓ Connected to Redis at {redis_host}:{redis_port}")
    except redis.ConnectionError as e:
        logger.error(f"✗ Failed to connect to Redis: {e}")
        return

    # Initialize ChromaDB client
    chromadb_client = chromadb.HttpClient(
        host=chromadb_host,
        port=chromadb_port,
    )

    # Test ChromaDB connection
    try:
        chromadb_client.heartbeat()
        logger.info(f"✓ Connected to ChromaDB at {chromadb_host}:{chromadb_port}")
    except Exception as e:
        logger.error(f"✗ Failed to connect to ChromaDB: {e}")
        return

    # Initialize agent managers
    logger.info("Initializing LLM agent managers...")
    config_manager = ConfigManager()
    instructions_manager = InstructionsManager()

    # Create indexer job
    logger.info("Creating semantic indexer job...")
    indexer = MetricsSemanticIndexerJob(
        promql_base_url=promql_url,
        redis_client=redis_client,
        chromadb_client=chromadb_client,
        config_manager=config_manager,
        instructions_manager=instructions_manager,
        batch_size=batch_size,
    )

    # Run the job
    logger.info(f"Starting indexer job for namespace: {namespace}")
    try:
        indexer.run(namespace=namespace, limit=limit)
        logger.info("✓ Job completed successfully!")

    except Exception as e:
        logger.error(f"✗ Job failed: {e}", exc_info=True)


if __name__ == "__main__":
    main()
