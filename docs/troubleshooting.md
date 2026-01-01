# Troubleshooting

Common issues and solutions when using Drift-SRE.

## No Discord Notifications

**Problem:** Anomalies are detected but Discord notifications aren't sent.

**Solutions:**
1. **Check webhook URL:** Verify the webhook URL is correct and active
   ```python
   # Test webhook manually
   import requests
   requests.post(webhook_url, json={"content": "test"})
   ```

2. **Check rate limiting:** You may be hitting the 10 alerts/hour limit
   - Check logs for "Rate limited" messages
   - Increase `rate_limit_per_hour` in DiscordNotifier if needed

3. **Check webhook permissions:** Ensure the webhook has permission to post in the channel

4. **Check logs:** Enable logging to see notification errors
   ```python
   import logging
   logging.basicConfig(level=logging.INFO)
   ```

## Too Many False Positives

**Problem:** Getting alerts for normal behavior.

**Solutions:**

1. **Increase thresholds:**
   ```python
   # For CUMSUM
   monitor.configure_metric('cpu_percent', threshold=35.0, drift=10.0)
   
   # For EWMA
   monitor.configure_metric('net_sent_mb', threshold_sigma=6.0)
   ```

2. **Increase min_anomaly_duration:**
   ```python
   monitor = DriftMonitor(
       min_anomaly_duration=5  # Require 5 consecutive anomalies
   )
   ```

3. **Adjust reference_mean for CUMSUM:**
   ```python
   # If your baseline is different
   monitor.configure_metric(
       'cpu_percent',
       reference_mean=50.0  # Your actual baseline
   )
   ```

4. **Use EWMA for variable metrics:**
   ```python
   # Switch from CUMSUM to EWMA for bursty metrics
   monitor.configure_metric(
       'net_sent_mb',
       algorithm='EWMA',
       alpha=0.1,  # Less reactive
       threshold_sigma=6.0
   )
   ```

## Missing Real Anomalies

**Problem:** Anomalies occur but aren't detected.

**Solutions:**

1. **Decrease thresholds:**
   ```python
   # For CUMSUM
   monitor.configure_metric('ram_percent', threshold=5.0, drift=1.0)
   
   # For EWMA
   monitor.configure_metric('cpu_percent', threshold_sigma=2.5)
   ```

2. **Decrease min_anomaly_duration:**
   ```python
   monitor = DriftMonitor(min_anomaly_duration=2)
   ```

3. **Check if metric is enabled:**
   ```python
   config = monitor.get_config('cpu_percent')
   if not config.enabled:
       monitor.configure_metric('cpu_percent', enabled=True)
   ```

4. **Review anomaly history:**
   ```python
   history = monitor.get_anomaly_history()
   # Check if anomalies were detected but not sustained
   ```

## High CPU Usage

**Problem:** Drift-SRE is using too much CPU.

**Solutions:**

1. **Increase check_interval:**
   ```python
   monitor = DriftMonitor(check_interval=10)  # Check every 10s instead of 5s
   ```

2. **Disable unused metrics:**
   ```python
   monitor.configure_metric('net_sent_mb', enabled=False)
   monitor.configure_metric('net_recv_mb', enabled=False)
   ```

3. **Reduce number of custom metrics:**
   - Each metric adds overhead
   - Only register metrics you actually need

## Memory Leaks

**Problem:** Memory usage grows over time.

**Solutions:**

1. **Check anomaly history size:**
   - History is limited to 100 entries automatically
   - If you're seeing growth, check for custom collectors holding references

2. **Review custom metrics:**
   - Ensure custom collector functions don't hold large objects
   - Don't store state in collector functions

3. **Reset periodically:**
   ```python
   # Reset every 24 hours
   import threading
   def periodic_reset():
       while True:
           time.sleep(86400)  # 24 hours
           monitor.reset()
   
   threading.Thread(target=periodic_reset, daemon=True).start()
   ```

## Metrics Not Updating

**Problem:** Metrics show the same values or aren't being collected.

**Solutions:**

1. **Check if monitoring is active:**
   ```python
   # Check status (you'll need to add this to monitor)
   print(monitor.monitoring_active)
   ```

2. **Manually collect metrics:**
   ```python
   from drift.collectors.system import SystemMetricsCollector
   collector = SystemMetricsCollector()
   metrics = collector.collect()
   print(metrics)
   ```

3. **Check for errors in logs:**
   - Enable logging to see collection errors
   - Some metrics may fail on certain systems (e.g., load_avg on Windows)

4. **Verify psutil is working:**
   ```python
   import psutil
   print(psutil.cpu_percent())
   print(psutil.virtual_memory().percent)
   ```

## Discord Rate Limiting

**Problem:** Hitting Discord's rate limits (not the library's).

**Solutions:**

1. **Reduce notification frequency:**
   - Increase `min_anomaly_duration` to reduce alerts
   - Increase thresholds to reduce false positives

2. **Use multiple webhooks:**
   - Split metrics across different webhooks
   - Use different channels for different severity levels

3. **Implement your own rate limiting:**
   - Add delays between notifications
   - Batch multiple anomalies into one message

## Custom Metrics Not Working

**Problem:** Custom metrics aren't being collected or detected.

**Solutions:**

1. **Check collector function:**
   ```python
   # Test collector directly
   value = your_collector_function()
   print(f"Value: {value}, Type: {type(value)}")
   # Must return a float
   ```

2. **Check if metric is registered:**
   ```python
   config = monitor.get_config('your_metric')
   if config is None:
       print("Metric not registered")
   ```

3. **Check for exceptions:**
   - Enable logging to see collector errors
   - Wrap collector in try/except

4. **Verify configuration:**
   ```python
   config = monitor.get_config('your_metric')
   print(config.enabled)  # Should be True
   print(config.algorithm)  # Should be set
   ```

## Thread Safety Issues

**Problem:** Errors when accessing monitor from multiple threads.

**Solutions:**

1. **All operations are thread-safe by default**
   - Use the provided methods
   - Don't access internal attributes directly

2. **If you need custom thread safety:**
   ```python
   with monitor.lock:  # If you need to access internals
       # Your code
       pass
   ```

## Windows-Specific Issues

**Problem:** Some metrics don't work on Windows.

**Solutions:**

1. **load_avg:** Automatically uses CPU-based approximation on Windows
2. **net_connections:** May require admin privileges
   - Run as administrator, or
   - Disable this metric: `monitor.configure_metric('connections', enabled=False)`

## Debugging Tips

1. **Enable logging:**
   ```python
   import logging
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )
   ```

2. **Check current metrics:**
   ```python
   metrics = monitor.get_current_metrics()
   print(metrics)
   ```

3. **Check anomaly history:**
   ```python
   history = monitor.get_anomaly_history()
   for entry in history:
       print(entry)
   ```

4. **Manual anomaly check:**
   ```python
   result = monitor.check_metrics()
   print(result)
   ```

5. **Test with known values:**
   ```python
   # Simulate high CPU
   test_metrics = {'cpu_percent': 95.0, 'ram_percent': 50.0, ...}
   result = monitor.check_metrics(test_metrics)
   print(result['has_anomalies'])
   ```

## Getting Help

If you're still having issues:

1. Check the [API Reference](api-reference.md) for correct usage
2. Review [Configuration Guide](configuration.md) for tuning tips
3. Check GitHub issues for similar problems
4. Enable debug logging and review error messages
5. Test with minimal configuration to isolate the issue

