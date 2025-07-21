import re
import requests
from urllib.parse import quote

PROMETHEUS_URL = "http://localhost:9090"  # Replace with your Prometheus/VictoriaMetrics endpoint
DEFAULT_LOOKBEHIND = "1h"
DEFAULT_TIMERANGE = "24h"

def extract_metric_and_range(query):
    pattern = re.compile(r'(\w+)\[(\d+[smhdw])\]')
    matches = pattern.findall(query)
    return matches if matches else []

def evaluate_helper_query(metric, window, func):
    query = f'{func}({metric}[{window}])'
    url = f'{PROMETHEUS_URL}/api/v1/query?query={quote(query)}'
    print(f"→ Executing: {query}")
    resp = requests.get(url).json()
    if resp["status"] == "success":
        return float(resp["data"]["result"][0]["value"][1]) if resp["data"]["result"] else 0
    else:
        raise RuntimeError(f"Query failed: {resp}")

def optimize_promql(query):
    print(f"🔍 Analyzing query: {query}")
    metric_ranges = extract_metric_and_range(query)

    for metric, window in metric_ranges:
        print(f"\n📊 Metric: {metric} | Window: {window}")

        try:
            ts_count = evaluate_helper_query("last_over_time(" + metric, window + ")", "count")
            sample_count = evaluate_helper_query("count_over_time(" + metric, window + ")", "sum")

            print(f"🧠 Estimated time series matched: {int(ts_count)}")
            print(f"📦 Estimated raw samples scanned: {int(sample_count)}")

            # Optimization hints
            if ts_count > 10000:
                print("⚠️ Too many time series! Try narrowing with label filters.")
            if sample_count > 1e8:
                print("⚠️ Too many samples! Consider reducing the window or increasing Grafana resolution.")

        except Exception as e:
            print(f"Error analyzing {metric}: {e}")

if __name__ == "__main__":
    test_query = 'avg(rate(http_requests_total[5m])) by (job)'
    optimize_promql(test_query)
