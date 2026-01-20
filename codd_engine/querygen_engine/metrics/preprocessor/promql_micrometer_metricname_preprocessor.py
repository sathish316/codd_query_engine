from codd_engine.querygen_engine.metrics.preprocessor.metrics_querygen_preprocessor import (
    MetricsQuerygenPreprocessor,
)
from codd_engine.querygen_engine.metrics.structured_inputs import MetricsQueryIntent


class PromQLMicrometerMetricNamePreprocessor(MetricsQuerygenPreprocessor):
    """
    Preprocessor for PromQL MetricsQueryIntent that applies Micrometer Prometheus naming conventions.

    Based on io.micrometer.prometheus.PrometheusNamingConvention rules:
    - Timers: append '_seconds' suffix (unless already ends with '_seconds')
    - Counters: append '_total' suffix (unless already ends with '_total')
    - Distribution Summaries: append base unit if provided (e.g., '_bytes')
    - Gauges: append base unit if provided (e.g., '_bytes')

    Preprocessing Logic is based on micrometer's PrometheusNamingConvention class:
    https://github.com/micrometer-metrics/micrometer/blob/main/implementations/micrometer-registry-prometheus/src/test/java/io/micrometer/prometheusmetrics/PrometheusNamingConventionTest.java
    """

    def preprocess(self, intent: MetricsQueryIntent) -> MetricsQueryIntent:
        """
        Preprocess the intent to transform metric names according to Prometheus conventions.

        Args:
            intent: The raw query intent with metric name and type

        Returns:
            A normalized query intent with Prometheus-compliant metric name
        """
        meter_type = intent.meter_type.lower() if intent.meter_type else ""
        metric_name = intent.metric
        base_unit = (
            intent.filters.get("base_unit", "").lower() if intent.filters else ""
        )

        # Apply type-specific suffix rules
        if meter_type == "timer":
            # Timers get '_seconds' suffix unless already present
            if not metric_name.endswith("_seconds"):
                metric_name = f"{metric_name}_seconds"

        elif meter_type == "counter":
            # Counters get base unit (if provided) + '_total' suffix
            if base_unit and not metric_name.endswith(f"_{base_unit}"):
                metric_name = f"{metric_name}_{base_unit}"
            if not metric_name.endswith("_total"):
                metric_name = f"{metric_name}_total"

        elif meter_type == "distribution_summary" or meter_type == "histogram":
            # Distribution summaries get base unit suffix (if provided)
            if base_unit and not metric_name.endswith(f"_{base_unit}"):
                metric_name = f"{metric_name}_{base_unit}"

        elif meter_type == "gauge":
            # Gauges get base unit suffix (if provided)
            if base_unit and not metric_name.endswith(f"_{base_unit}"):
                metric_name = f"{metric_name}_{base_unit}"

        # Return updated intent if metric name changed
        if metric_name != intent.metric:
            intent = intent.clone_with(metric=metric_name)

        return intent
