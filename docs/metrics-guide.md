# Metrics Guide

This guide explains each metric that Drift-SRE monitors and why they're configured the way they are.

## CPU Usage (`cpu_percent`)

**What it measures:** Percentage of CPU time used across all cores.

**Why CUMSUM:** CPU usage typically has a stable baseline. Temporary spikes are normal (e.g., during application startup), but sustained high usage indicates a problem.

**Default configuration:**
- Algorithm: CUMSUM
- Threshold: 25.0 (less sensitive)
- Drift: 5.0 (only significant changes)
- Reference Mean: 30.0%

**Why less sensitive:**
- CPU can spike temporarily during normal operations
- We only want to alert on sustained high usage
- False positives from temporary spikes are annoying

**Tuning tips:**
- If your app normally uses 80% CPU, increase `reference_mean` to 80.0
- If you want to catch smaller sustained increases, decrease `threshold` to 15.0

## RAM Usage (`ram_percent`)

**What it measures:** Percentage of physical RAM in use.

**Why CUMSUM:** RAM usage should be relatively stable. Sudden increases often indicate memory leaks.

**Default configuration:**
- Algorithm: CUMSUM
- Threshold: 10.0 (more sensitive)
- Drift: 2.0 (catches small changes)
- Reference Mean: 50.0%

**Why more sensitive:**
- Memory leaks are critical issues
- RAM doesn't recover automatically (unlike CPU)
- Early detection prevents OOM crashes
- RAM can be volatile, so we want to catch gradual increases

**Tuning tips:**
- If you have memory-intensive workloads, increase `reference_mean`
- For leak detection, keep `threshold` low (5.0-10.0)
- If getting too many alerts, increase `drift` to 5.0

## System Load (`load_avg`)

**What it measures:** 1-minute system load average (Unix) or CPU-based approximation (Windows).

**Why CUMSUM:** Load average should be relatively stable for a given workload.

**Default configuration:**
- Algorithm: CUMSUM
- Threshold: 15.0
- Drift: 1.0
- Reference Mean: 2.0

**Tuning tips:**
- Adjust `reference_mean` based on your typical load
- On multi-core systems, load can be higher (e.g., 4.0 for 4 cores)

## Network Sent (`net_sent_mb`)

**What it measures:** Cumulative megabytes sent over network interfaces.

**Why EWMA:** Network traffic is naturally bursty. EWMA adapts to changing traffic patterns.

**Default configuration:**
- Algorithm: EWMA
- Alpha: 0.1 (smooth, less reactive)
- Threshold Sigma: 5.0 (less sensitive)

**Why EWMA:**
- Network traffic has natural bursts (file uploads, API calls)
- Traffic patterns change throughout the day
- EWMA learns the current "normal" traffic level

**Why less sensitive:**
- Network spikes are often legitimate (backups, deployments)
- We only want to alert on truly unusual patterns

**Tuning tips:**
- For high-traffic servers, increase `threshold_sigma` to 6.0-7.0
- For low-traffic servers, decrease to 4.0 to catch anomalies

## Network Received (`net_recv_mb`)

**What it measures:** Cumulative megabytes received over network interfaces.

**Configuration:** Same as `net_sent_mb` (EWMA, alpha=0.1, threshold_sigma=5.0)

**Same reasoning as network sent.**

## Disk Read (`disk_read_mb`)

**What it measures:** Cumulative megabytes read from disk.

**Why EWMA:** Disk I/O is variable and depends on workload.

**Default configuration:**
- Algorithm: EWMA
- Alpha: 0.15 (moderate reactivity)
- Threshold Sigma: 4.5

**Tuning tips:**
- Database servers will have higher baseline I/O
- Adjust based on your workload patterns

## Disk Write (`disk_write_mb`)

**What it measures:** Cumulative megabytes written to disk.

**Configuration:** Same as `disk_read_mb` (EWMA, alpha=0.15, threshold_sigma=4.5)

**Same reasoning as disk read.**

## Network Connections (`connections`)

**What it measures:** Number of active network connections.

**Why EWMA:** Connection counts vary based on traffic and can have natural bursts.

**Default configuration:**
- Algorithm: EWMA
- Alpha: 0.15
- Threshold Sigma: 5.0

**Tuning tips:**
- Web servers will have higher baseline connections
- Sudden drops might indicate issues (connection pool exhaustion)

## Custom Metrics

You can add your own metrics! See [Advanced Usage](advanced.md) for details.

**Examples of custom metrics:**
- Application-specific metrics (queue depth, request rate)
- Database connection pool size
- Cache hit rate
- Custom business metrics

## Understanding Metric Values

### Cumulative Metrics

Some metrics (`net_sent_mb`, `net_recv_mb`, `disk_read_mb`, `disk_write_mb`) are **cumulative** - they only increase over time. This is why EWMA works well for them - it adapts to the rate of change rather than absolute values.

### Percentage Metrics

`cpu_percent` and `ram_percent` are percentages (0-100). These have clear bounds and stable baselines, making CUMSUM ideal.

### Count Metrics

`connections` and `load_avg` are counts that can vary. EWMA adapts to the current level.

## Best Practices

1. **Monitor what matters:** Don't enable metrics you don't care about
2. **Tune gradually:** Start with defaults, adjust based on false positives/negatives
3. **Consider your workload:** A database server will have different baselines than a web server
4. **Review alerts:** Use anomaly history to understand patterns
5. **Test changes:** Adjust one metric at a time and observe results

