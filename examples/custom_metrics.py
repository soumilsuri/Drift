"""
Custom metrics example for Drift-SRE

Shows how to register and monitor custom application metrics.
"""

from drift import DriftMonitor, MetricConfig
import time
import random

# Simulated application state
class ApplicationState:
    def __init__(self):
        self.queue_depth = 0
        self.error_count = 0
        self.request_count = 0
        self.active_connections = 0
    
    def get_queue_depth(self):
        """Simulate queue depth"""
        # Random walk simulation
        change = random.randint(-2, 5)
        self.queue_depth = max(0, self.queue_depth + change)
        return float(self.queue_depth)
    
    def get_error_rate(self):
        """Calculate error rate percentage"""
        self.request_count += random.randint(10, 50)
        if random.random() < 0.1:  # 10% chance of error
            self.error_count += 1
        
        if self.request_count == 0:
            return 0.0
        return (self.error_count / self.request_count) * 100.0
    
    def get_active_connections(self):
        """Simulate active connections"""
        change = random.randint(-1, 3)
        self.active_connections = max(0, self.active_connections + change)
        return float(self.active_connections)

def main():
    # Initialize monitor
    monitor = DriftMonitor(
        discord_webhook=None,  # Set to your webhook URL
        check_interval=5
    )
    
    # Create application state
    app_state = ApplicationState()
    
    # Register custom metrics
    monitor.register_custom_metric(
        name='queue_depth',
        collector=app_state.get_queue_depth,
        config=MetricConfig(
            algorithm='EWMA',
            alpha=0.2,
            threshold_sigma=3.0,
            description='Application queue depth'
        )
    )
    
    monitor.register_custom_metric(
        name='error_rate',
        collector=app_state.get_error_rate,
        config=MetricConfig(
            algorithm='CUMSUM',
            threshold=5.0,
            drift=1.0,
            description='Application error rate percentage'
        )
    )
    
    monitor.register_custom_metric(
        name='active_connections',
        collector=app_state.get_active_connections,
        config=MetricConfig(
            algorithm='EWMA',
            alpha=0.15,
            threshold_sigma=4.0,
            description='Active application connections'
        )
    )
    
    # Start monitoring
    monitor.start()
    
    print("Custom metrics monitoring started!")
    print("Registered metrics: queue_depth, error_rate, active_connections")
    print("Press Ctrl+C to stop.")
    
    try:
        while True:
            # Simulate application activity
            time.sleep(1)
            
            # Periodically show current metrics
            metrics = monitor.get_current_metrics()
            if metrics:
                print(f"\nCurrent metrics:")
                print(f"  Queue Depth: {metrics.get('queue_depth', 'N/A')}")
                print(f"  Error Rate: {metrics.get('error_rate', 'N/A'):.2f}%")
                print(f"  Active Connections: {metrics.get('active_connections', 'N/A')}")
                time.sleep(4)  # Show every 5 seconds
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped.")

if __name__ == "__main__":
    main()

