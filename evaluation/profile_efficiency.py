Use:
import os
import statistics
import time
import psutil
def profile_call(function, *args, **kwargs):
process = psutil.Process(os.getpid())
memory_before = process.memory_info().rss
start = time.perf_counter()
result = function(*args, **kwargs)
elapsed = time.perf_counter() - start
memory_after = process.memory_info().rss
return {
"result": result,
"latency_ms": elapsed * 1000,
"rss_before_mb":
memory_before / (1024 ** 2),
"rss_after_mb":
memory_after / (1024 ** 2),
"rss_delta_mb":
(memory_after - memory_before)
/ (1024 ** 2),
}
Measure:
Cold start
process start
model loading
first prediction
Warm inference
Discard initial warm-up runs:
for _ in range(10):
detector.identify(sample_text)
Then measure at least 100 runs:
latencies = []
for _ in range(100):
start = time.perf_counter()
detector.identify(sample_text)
latencies.append(
(time.perf_counter() - start) * 1000
)
Report:
summary = {
"mean_ms": statistics.mean(latencies),
"median_ms": statistics.median(latencies),
"min_ms": min(latencies),
"max_ms": max(latencies),
"p95_ms": sorted(latencies)[
int(len(latencies) * 0.95) - 1
],
}
Profile at least three input lengths:
Short: 5 to 10 tokens
Medium: 25 to 50 tokens
Long: 100 to 200 tokens
