# Memory tracking

TimeSeriesFlow tracks process memory and runtime using `psutil` with minimal overhead.

## Quick start

```python
from timeseriesflow.memory import track_memory

@track_memory
def process_batch():
    return build_dataframe()

process_batch()
print(process_batch.last_metrics.to_dict())
```

Output:

```python
{
    "runtime_seconds": 1.2,
    "memory_before_mb": 100.0,
    "memory_after_mb": 120.0,
    "memory_delta_mb": 20.0,
    "peak_memory_mb": 125.0,
}
```

## MemoryTracker

Programmatic API for scoped or continuous tracking.

### Scoped measurement

```python
from timeseriesflow.memory import MemoryTracker

tracker = MemoryTracker(warning_threshold_mb=50.0)

with tracker.measure():
    run_entity_processing()

metrics = tracker.last_metrics
print(metrics.to_dict())
```

Or explicit start/finish:

```python
tracker = MemoryTracker()
tracker.start()
do_work()
metrics = tracker.finish()
```

### Peak sampling

For long runs (EntityRunner, Flow engine), call `sample()` periodically:

```python
tracker = MemoryTracker()
tracker.sample()  # updates tracker.peak_rss_mb
```

## track_memory decorator

```python
from timeseriesflow.memory import track_memory

@track_memory(warning_threshold_mb=100.0)
def heavy_job():
    ...

heavy_job()
metrics = heavy_job.last_metrics
```

Options:

| Parameter | Description |
|-----------|-------------|
| `warning_threshold_mb` | Warn when memory delta exceeds threshold |
| `logger` | Custom logger (default: `timeseriesflow.memory`) |
| `enabled` | Set False to skip psutil calls |

Supports bare and parameterized forms:

```python
@track_memory
def foo(): ...

@track_memory(warning_threshold_mb=50)
def bar(): ...
```

## MemoryMetrics fields

| Field | Description |
|-------|-------------|
| `runtime_seconds` | Wall-clock duration |
| `memory_before_mb` | RSS before execution |
| `memory_after_mb` | RSS after execution |
| `memory_delta_mb` | Non-negative RSS increase |
| `peak_memory_mb` | Peak RSS during measurement |

Use `metrics.to_dict()` for the exact output shape shown above (plus `peak_memory_mb`).

## Logger integration

- DEBUG: routine metrics after each scoped measurement
- WARNING: emitted when `memory_delta_mb >= warning_threshold_mb`

Loggers use the `timeseriesflow.memory` namespace.

## Minimal overhead

- Disabled tracker skips psutil calls in scoped mode
- One psutil read at start and one at end for scoped measurements
- `sample()` performs a single read per call for peak tracking
- Uses `time.perf_counter()` for runtime

## Integration

EntityRunner and the legacy Flow engine use `MemoryTracker.sample()` for peak RSS across entity loops. Entity flows use scoped snapshots per entity. Use `@track_memory` for ad-hoc function profiling.
