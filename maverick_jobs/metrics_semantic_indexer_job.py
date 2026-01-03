"""
Offline job for semantic indexing of metrics metadata.

This job:
1. Queries metric metadata from Prometheus via PromQL client
2. Updates Redis metadata store for exact-match validation
3. Enriches metrics using LLM (OpusAgent) for semantic information
4. Indexes enriched metadata into semantic store (ChromaDB)
5. Processes in batches with progress tracking
"""

import logging
import re
from typing import Optional
from dataclasses import dataclass

import chromadb
import redis

from maverick_dal.metrics.promql_client import PromQLClient
from maverick_dal.metrics.metrics_metadata_store import MetricsMetadataStore
from maverick_dal.metrics.metrics_semantic_metadata_store import (
    MetricsSemanticMetadataStore,
)

from maverick_engine.semantic_engine.agent.metrics_enrichment_agent import (
    MetricsEnrichmentAgent,
    MetricEnrichmentError,
)

from opus_agent_base.config.config_manager import ConfigManager
from opus_agent_base.prompt.instructions_manager import InstructionsManager

logger = logging.getLogger(__name__)


@dataclass
class IndexingStats:
    """Statistics for the indexing job."""

    total_metrics: int = 0
    processed_metrics: int = 0
    enriched_metrics: int = 0
    indexed_metrics: int = 0
    failed_metrics: int = 0
    skipped_metrics: int = 0
    excluded_metrics: int = 0


class MetricsSemanticIndexerJobError(Exception):
    """Exception raised when indexer job encounters an error."""

    pass


class MetricsSemanticIndexerJob:
    """
    Offline job for semantic indexing of metrics.

    Fetches metrics from Prometheus, enriches them with semantic metadata
    using LLM, and indexes them into both Redis (exact match) and ChromaDB
    (semantic search) stores.
    """

    def __init__(
        self,
        promql_base_url: str,
        redis_client: redis.Redis,
        chromadb_client: chromadb.ClientAPI,
        config_manager: ConfigManager,
        instructions_manager: InstructionsManager,
        batch_size: int = 10,
    ):
        """
        Initialize the semantic indexer job.

        Args:
            promql_base_url: Base URL for Prometheus server
            redis_client: Redis client for metadata store
            chromadb_client: ChromaDB client for semantic store
            config_manager: Configuration manager for LLM agent
            instructions_manager: Instructions manager for LLM agent
            batch_size: Number of metrics to process in each batch
        """
        self.promql_base_url = promql_base_url
        self.batch_size = batch_size

        # Initialize clients and stores
        self.promql_client: Optional[PromQLClient] = None
        self.redis_store = MetricsMetadataStore(redis_client)
        self.semantic_store = MetricsSemanticMetadataStore(chromadb_client)

        # Initialize enrichment agent
        self.enrichment_agent = MetricsEnrichmentAgent(
            config_manager, instructions_manager
        )

        # Statistics
        self.stats = IndexingStats()

        logger.info(
            f"Initialized MetricsSemanticIndexerJob with batch_size={batch_size}",
            extra={"batch_size": batch_size, "promql_url": promql_base_url},
        )

    def run(
        self,
        namespace: str,
        limit: Optional[int] = None,
        exclude_pattern: Optional[str] = None,
        skip_if_present: bool = False,
        dry_run: bool = False,
    ):
        """
        Run the semantic indexing job for a given namespace.

        Args:
            namespace: The namespace to index metrics for (e.g., "tenant:service")
            limit: Optional limit on number of metrics to process (for testing)
            exclude_pattern: Optional regex pattern to exclude metrics
            skip_if_present: If True, skip metrics already present in semantic store
            dry_run: If True, display metrics without performing LLM enrichment or indexing

        Raises:
            MetricsSemanticIndexerJobError: If job execution fails
        """
        logger.info(
            f"Starting semantic indexing job for namespace: {namespace}",
            extra={
                "namespace": namespace,
                "limit": limit,
                "exclude_pattern": exclude_pattern,
                "skip_if_present": skip_if_present,
                "dry_run": dry_run,
            },
        )

        print(f"\n{'=' * 70}")
        print("METRICS SEMANTIC INDEXER JOB" + (" [DRY RUN MODE]" if dry_run else ""))
        print(f"{'=' * 70}")
        print(f"Namespace: {namespace}")
        print(f"Batch Size: {self.batch_size}")
        print(f"Limit: {limit if limit else 'None (all metrics)'}")
        print(f"Exclude Pattern: {exclude_pattern if exclude_pattern else 'None'}")
        print(f"Skip if Present: {skip_if_present}")
        print(f"Dry Run: {dry_run}")
        print(f"{'=' * 70}\n")

        try:
            # Step 1: Fetch metrics from Prometheus
            print("[1/4] Fetching metrics from Prometheus...")
            metrics = self._fetch_metrics_from_prometheus(limit)
            self.stats.total_metrics = len(metrics)
            print(f"      ✓ Found {self.stats.total_metrics} metrics\n")

            # Step 1.5: Filter metrics by exclude pattern if provided
            if exclude_pattern:
                print(
                    f"[1.5/4] Filtering metrics with exclude pattern: {exclude_pattern}"
                )
                metrics = self._filter_metrics_by_pattern(metrics, exclude_pattern)
                print(
                    f"      ✓ Filtered to {len(metrics)} metrics ({self.stats.excluded_metrics} excluded)\n"
                )

            # Step 2: Update Redis metadata store
            if not dry_run:
                print("[2/4] Updating Redis metadata store...")
                self._update_redis_store(namespace, metrics)
                logger.info(
                    "Redis metadata store updated",
                    extra={"namespace": namespace, "count": len(metrics)},
                )
                print(f"      ✓ Redis updated with {len(metrics)} metric names\n")
            else:
                print("[2/4] Updating Redis metadata store... [SKIPPED - DRY RUN]\n")

            # Step 3: Enrich and index metrics in batches
            if not dry_run:
                print(
                    "[3/4] Enriching metrics using LLM and indexing to semantic store..."
                )
            else:
                print(
                    "[3/4] Displaying metrics (no enrichment or indexing in dry run mode)..."
                )
            self._process_metrics_in_batches(
                namespace, metrics, skip_if_present, dry_run
            )
            print(f"      ✓ Processed {self.stats.processed_metrics} metrics\n")

            # Step 4: Print summary
            print("[4/4] Indexing complete!")
            self._print_summary()

            logger.info(
                f"Semantic indexing job completed successfully for namespace: {namespace}",
                extra={
                    "namespace": namespace,
                    "total": self.stats.total_metrics,
                    "processed": self.stats.processed_metrics,
                    "enriched": self.stats.enriched_metrics,
                    "indexed": self.stats.indexed_metrics,
                    "failed": self.stats.failed_metrics,
                },
            )

        except Exception as e:
            logger.error(f"Semantic indexing job failed: {e}", exc_info=True)
            print(f"\n✗ ERROR: {e}\n")
            raise MetricsSemanticIndexerJobError(
                f"Failed to execute semantic indexing job: {e}"
            ) from e

    def _filter_metrics_by_pattern(
        self, metrics: list[dict], exclude_pattern: str
    ) -> list[dict]:
        """
        Filter metrics by excluding those matching the regex pattern.

        Args:
            metrics: List of metric metadata dictionaries
            exclude_pattern: Regex pattern to exclude metrics

        Returns:
            Filtered list of metrics
        """
        try:
            pattern = re.compile(exclude_pattern)
            filtered_metrics = []

            for metric in metrics:
                metric_name = metric.get("metric", "")
                if pattern.match(metric_name):
                    self.stats.excluded_metrics += 1
                    logger.debug(
                        f"Excluded metric: {metric_name} (matches pattern: {exclude_pattern})"
                    )
                else:
                    filtered_metrics.append(metric)

            logger.info(
                f"Filtered metrics by pattern '{exclude_pattern}': {len(filtered_metrics)} remaining, {self.stats.excluded_metrics} excluded",
                extra={
                    "pattern": exclude_pattern,
                    "remaining": len(filtered_metrics),
                    "excluded": self.stats.excluded_metrics,
                },
            )

            return filtered_metrics

        except re.error as e:
            raise MetricsSemanticIndexerJobError(
                f"Invalid regex pattern '{exclude_pattern}': {e}"
            ) from e

    def _fetch_metrics_from_prometheus(self, limit: Optional[int]) -> list[dict]:
        """
        Fetch metric metadata from Prometheus.

        Args:
            limit: Optional limit on number of metrics to fetch

        Returns:
            List of metric metadata dictionaries with 'metric', 'type', 'help' keys
        """
        try:
            with PromQLClient(base_url=self.promql_base_url) as client:
                self.promql_client = client

                # Check health
                if not client.health_check():
                    raise MetricsSemanticIndexerJobError(
                        "Prometheus health check failed"
                    )

                # Fetch all metric metadata
                metadata_dict = client.get_metric_metadata()

                # Convert to list format
                metrics = []
                for metric_name, entries in metadata_dict.items():
                    if entries:
                        # Take first entry if multiple exist
                        entry = entries[0]
                        metrics.append(
                            {
                                "metric": metric_name,
                                "type": entry.get("type", "unknown"),
                                "help": entry.get("help", ""),
                            }
                        )

                    # Apply limit if specified
                    if limit and len(metrics) >= limit:
                        break

                return metrics

        except Exception as e:
            raise MetricsSemanticIndexerJobError(
                f"Failed to fetch metrics from Prometheus: {e}"
            ) from e

    def _update_redis_store(self, namespace: str, metrics: list[dict]):
        """
        Update Redis metadata store with metric names.

        Args:
            namespace: The namespace to update
            metrics: List of metric metadata dictionaries
        """
        try:
            metric_names = {m["metric"] for m in metrics}
            self.redis_store.set_metric_names(namespace, metric_names)

            logger.info(
                f"Updated Redis store with {len(metric_names)} metrics",
                extra={"namespace": namespace, "count": len(metric_names)},
            )

        except Exception as e:
            raise MetricsSemanticIndexerJobError(
                f"Failed to update Redis store: {e}"
            ) from e

    def _process_metrics_in_batches(
        self,
        namespace: str,
        metrics: list[dict],
        skip_if_present: bool = False,
        dry_run: bool = False,
    ):
        """
        Process metrics in batches, enriching with LLM and indexing to semantic store.

        Args:
            namespace: The namespace for indexing
            metrics: List of metric metadata dictionaries
            skip_if_present: If True, skip metrics already present in semantic store
            dry_run: If True, display metrics without performing LLM enrichment or indexing
        """
        total_metrics = len(metrics)
        num_batches = (total_metrics + self.batch_size - 1) // self.batch_size

        print(f"      Processing {total_metrics} metrics in {num_batches} batches...\n")

        for batch_num in range(num_batches):
            start_idx = batch_num * self.batch_size
            end_idx = min(start_idx + self.batch_size, total_metrics)
            batch = metrics[start_idx:end_idx]

            self._process_batch(
                namespace, batch, batch_num + 1, num_batches, skip_if_present, dry_run
            )

    def _process_batch(
        self,
        namespace: str,
        batch: list[dict],
        batch_num: int,
        total_batches: int,
        skip_if_present: bool = False,
        dry_run: bool = False,
    ):
        """
        Process a single batch of metrics.

        Args:
            namespace: The namespace for indexing
            batch: List of metric metadata dictionaries in this batch
            batch_num: Current batch number (1-indexed)
            total_batches: Total number of batches
            skip_if_present: If True, skip metrics already present in semantic store
            dry_run: If True, display metrics without performing LLM enrichment or indexing
        """
        print(f"      Batch {batch_num}/{total_batches} ({len(batch)} metrics):")

        for metric_data in batch:
            metric_name = metric_data["metric"]
            metric_type = metric_data.get("type", "unknown")
            description = metric_data.get("help", "")

            try:
                # Dry run mode: just display the metric
                if dry_run:
                    self.stats.processed_metrics += 1
                    desc_preview = (
                        description[:60] + "..."
                        if len(description) > 60
                        else description
                    )
                    print(
                        f"        → {metric_name} (type: {metric_type}, desc: {desc_preview or 'N/A'})"
                    )
                    continue

                # Check if metric already exists in semantic store
                if skip_if_present and self.semantic_store.metric_exists(
                    namespace, metric_name
                ):
                    self.stats.skipped_metrics += 1
                    print(f"        → Skipping: {metric_name} (already present)")
                    continue

                # Update progress
                self.stats.processed_metrics += 1
                print(f"        → Enriching: {metric_name}", end="", flush=True)

                # Enrich using LLM
                enriched_metadata = self.enrichment_agent.enrich_metric_to_dict(
                    metric_name=metric_name,
                    metric_type=metric_type,
                    description=description if description else None,
                )

                self.stats.enriched_metrics += 1

                # Index into semantic store
                doc_id = self.semantic_store.index_metadata(
                    namespace, enriched_metadata
                )
                self.stats.indexed_metrics += 1

                # Print success
                print(
                    f" ✓ (category: {enriched_metadata.get('category', 'N/A')}, "
                    f"signal: {enriched_metadata.get('golden_signal_type', 'N/A')}, "
                    f"meter_type: {enriched_metadata.get('meter_type', 'N/A')})"
                )

                logger.debug(
                    f"Indexed metric: {metric_name}",
                    extra={
                        "metric_name": metric_name,
                        "doc_id": doc_id,
                        "category": enriched_metadata.get("category"),
                        "golden_signal": enriched_metadata.get("golden_signal_type"),
                    },
                )

            except MetricEnrichmentError as e:
                self.stats.failed_metrics += 1
                print(f" ✗ (enrichment failed: {str(e)[:50]}...)")
                logger.warning(
                    f"Failed to enrich metric: {metric_name}",
                    extra={"metric_name": metric_name, "error": str(e)},
                )

            except Exception as e:
                self.stats.failed_metrics += 1
                print(f" ✗ (error: {str(e)[:50]}...)")
                logger.error(
                    f"Failed to process metric: {metric_name}",
                    extra={"metric_name": metric_name},
                    exc_info=True,
                )

        print()  # Newline after batch

    def _print_summary(self):
        """Print job execution summary."""
        print(f"\n{'=' * 70}")
        print("INDEXING SUMMARY")
        print(f"{'=' * 70}")
        print(f"Total Metrics:      {self.stats.total_metrics}")
        print(f"Excluded:           {self.stats.excluded_metrics}")
        print(f"Processed:          {self.stats.processed_metrics}")
        print(f"Enriched (LLM):     {self.stats.enriched_metrics}")
        print(f"Indexed (Semantic): {self.stats.indexed_metrics}")
        print(f"Failed:             {self.stats.failed_metrics}")
        print(f"Skipped:            {self.stats.skipped_metrics}")
        print(f"{'=' * 70}")

        # Calculate success rate based on non-excluded metrics
        eligible_metrics = self.stats.total_metrics - self.stats.excluded_metrics
        success_rate = (
            (self.stats.indexed_metrics / eligible_metrics * 100)
            if eligible_metrics > 0
            else 0
        )
        print(f"Success Rate:       {success_rate:.1f}% (of eligible metrics)")
        print(f"{'=' * 70}\n")
