"""
Basic usage example for Drift-SRE

This demonstrates the simplest way to use Drift-SRE with default configurations.
"""

from drift import DriftMonitor

# Replace with your Discord webhook URL
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN"

def main():
    # Initialize monitor with Discord webhook
    monitor = DriftMonitor(
        discord_webhook=DISCORD_WEBHOOK,
        check_interval=5  # Check metrics every 5 seconds
    )
    
    # Start monitoring in background
    monitor.start()
    
    print("Monitoring started! Press Ctrl+C to stop.")
    print("Anomalies will be sent to Discord.")
    
    try:
        # Keep the script running
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping monitor...")
        monitor.stop()
        print("Monitor stopped.")

if __name__ == "__main__":
    main()

