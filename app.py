"""
Flask Server for Real-time Anomaly Monitoring
Provides REST API for monitoring server metrics and detecting anomalies
"""

from flask import Flask, jsonify, render_template_string
from anomaly_detector import AnomalyMonitor, ServerMetrics
import threading
import time
from datetime import datetime

app = Flask(__name__)

# Global monitor instance
monitor = AnomalyMonitor()
metrics_collector = ServerMetrics()

# Store latest metrics
latest_metrics = {}
latest_anomaly_result = {}

# Background monitoring
monitoring_active = False
monitoring_interval = 5  # seconds


def background_monitor():
    """Background thread to continuously monitor metrics"""
    global latest_metrics, latest_anomaly_result
    
    while monitoring_active:
        try:
            # Collect metrics
            metrics = metrics_collector.get_all_metrics()
            latest_metrics = metrics
            
            # Check for anomalies
            result = monitor.check_metrics(metrics)
            latest_anomaly_result = result
            
            # Log anomalies
            if result['has_anomalies']:
                print(f"[ALERT] {result['anomaly_count']} anomalies detected at {result['timestamp']}")
                for anomaly in result['anomalies']:
                    print(f"  - {anomaly['metric']}: {anomaly['value']:.2f} "
                          f"(score: {anomaly['score']:.2f}, severity: {anomaly['severity']})")
            
        except Exception as e:
            print(f"Error in background monitor: {e}")
        
        time.sleep(monitoring_interval)


# API Endpoints

@app.route('/')
def index():
    """Dashboard HTML"""
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Server Anomaly Monitor</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 20px;
                background: #f5f5f5;
            }
            .container {
                max-width: 1200px;
                margin: 0 auto;
            }
            h1 {
                color: #333;
            }
            .card {
                background: white;
                padding: 20px;
                margin: 20px 0;
                border-radius: 8px;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }
            .metric {
                display: inline-block;
                margin: 10px 20px 10px 0;
            }
            .metric-label {
                font-weight: bold;
                color: #555;
            }
            .metric-value {
                color: #007bff;
                font-size: 1.2em;
            }
            .anomaly {
                background: #fff3cd;
                border-left: 4px solid #ffc107;
                padding: 10px;
                margin: 10px 0;
            }
            .anomaly.high {
                background: #f8d7da;
                border-left-color: #dc3545;
            }
            .status {
                display: inline-block;
                padding: 5px 15px;
                border-radius: 20px;
                font-weight: bold;
            }
            .status.normal {
                background: #d4edda;
                color: #155724;
            }
            .status.alert {
                background: #f8d7da;
                color: #721c24;
            }
            button {
                padding: 10px 20px;
                margin: 5px;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 14px;
            }
            .btn-primary {
                background: #007bff;
                color: white;
            }
            .btn-danger {
                background: #dc3545;
                color: white;
            }
            .btn-secondary {
                background: #6c757d;
                color: white;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🔍 Server Anomaly Monitor</h1>
            
            <div class="card">
                <h2>Control Panel</h2>
                <button class="btn-primary" onclick="startMonitoring()">Start Monitoring</button>
                <button class="btn-danger" onclick="stopMonitoring()">Stop Monitoring</button>
                <button class="btn-secondary" onclick="resetDetectors()">Reset Detectors</button>
                <button class="btn-secondary" onclick="refreshData()">Refresh</button>
            </div>
            
            <div class="card">
                <h2>Current Status</h2>
                <div id="status"></div>
            </div>
            
            <div class="card">
                <h2>Server Metrics</h2>
                <div id="metrics"></div>
            </div>
            
            <div class="card">
                <h2>Anomaly Detection Results</h2>
                <div id="anomalies"></div>
            </div>
            
            <div class="card">
                <h2>Anomaly History</h2>
                <div id="history"></div>
            </div>
        </div>
        
        <script>
            function startMonitoring() {
                fetch('/api/start', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        refreshData();
                    });
            }
            
            function stopMonitoring() {
                fetch('/api/stop', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        refreshData();
                    });
            }
            
            function resetDetectors() {
                fetch('/api/reset', {method: 'POST'})
                    .then(r => r.json())
                    .then(data => {
                        alert(data.message);
                        refreshData();
                    });
            }
            
            function refreshData() {
                // Get status
                fetch('/api/status')
                    .then(r => r.json())
                    .then(data => {
                        let statusDiv = document.getElementById('status');
                        let statusClass = data.monitoring_active ? 'normal' : 'alert';
                        let statusText = data.monitoring_active ? 'Active' : 'Inactive';
                        statusDiv.innerHTML = `
                            <p><strong>Monitoring:</strong> <span class="status ${statusClass}">${statusText}</span></p>
                            <p><strong>Interval:</strong> ${data.interval} seconds</p>
                            <p><strong>Last Update:</strong> ${data.timestamp || 'N/A'}</p>
                        `;
                    });
                
                // Get current metrics
                fetch('/api/metrics')
                    .then(r => r.json())
                    .then(data => {
                        let metricsDiv = document.getElementById('metrics');
                        if (data.metrics) {
                            let html = '';
                            for (let [key, value] of Object.entries(data.metrics)) {
                                if (key !== 'timestamp') {
                                    html += `
                                        <div class="metric">
                                            <span class="metric-label">${key}:</span>
                                            <span class="metric-value">${typeof value === 'number' ? value.toFixed(2) : value}</span>
                                        </div>
                                    `;
                                }
                            }
                            metricsDiv.innerHTML = html;
                        } else {
                            metricsDiv.innerHTML = '<p>No metrics available yet. Start monitoring.</p>';
                        }
                    });
                
                // Get anomaly results
                fetch('/api/check')
                    .then(r => r.json())
                    .then(data => {
                        let anomaliesDiv = document.getElementById('anomalies');
                        if (data.has_anomalies) {
                            let html = `<p><span class="status alert">⚠️ ${data.anomaly_count} Anomalies Detected</span></p>`;
                            data.anomalies.forEach(anomaly => {
                                html += `
                                    <div class="anomaly ${anomaly.severity}">
                                        <strong>${anomaly.metric}</strong>: ${anomaly.value.toFixed(2)} 
                                        (Score: ${anomaly.score.toFixed(2)}, Algorithm: ${anomaly.algorithm}, 
                                        Severity: ${anomaly.severity}, Duration: ${anomaly.duration || 1} checks)
                                    </div>
                                `;
                            });
                            anomaliesDiv.innerHTML = html;
                        } else {
                            anomaliesDiv.innerHTML = '<p><span class="status normal">✓ All metrics normal</span></p>';
                        }
                    });
                
                // Get history
                fetch('/api/history')
                    .then(r => r.json())
                    .then(data => {
                        let historyDiv = document.getElementById('history');
                        if (data.history && data.history.length > 0) {
                            let html = `<p><strong>Total anomalies detected:</strong> ${data.count}</p>`;
                            data.history.slice(-5).reverse().forEach(entry => {
                                html += `
                                    <div class="anomaly">
                                        <strong>${entry.timestamp}</strong>: ${entry.anomaly_count} anomalies
                                        <ul>
                                            ${entry.anomalies.map(a => `<li>${a.metric}: ${a.value.toFixed(2)} (${a.algorithm})</li>`).join('')}
                                        </ul>
                                    </div>
                                `;
                            });
                            historyDiv.innerHTML = html;
                        } else {
                            historyDiv.innerHTML = '<p>No anomalies detected yet.</p>';
                        }
                    });
            }
            
            // Auto-refresh every 5 seconds
            setInterval(refreshData, 5000);
            
            // Initial load
            refreshData();
        </script>
    </body>
    </html>
    """
    return render_template_string(html)


@app.route('/api/metrics')
def get_metrics():
    """Get current server metrics"""
    return jsonify({
        'timestamp': datetime.now().isoformat(),
        'metrics': latest_metrics
    })


@app.route('/api/check')
def check_anomalies():
    """Get latest anomaly detection result"""
    if latest_anomaly_result:
        return jsonify(latest_anomaly_result)
    
    # If no cached result, do a fresh check
    metrics = metrics_collector.get_all_metrics()
    result = monitor.check_metrics(metrics)
    return jsonify(result)


@app.route('/api/history')
def get_history():
    """Get anomaly history"""
    history = monitor.get_anomaly_history()
    return jsonify({
        'count': len(history),
        'history': history
    })


@app.route('/api/start', methods=['POST'])
def start_monitoring():
    """Start background monitoring"""
    global monitoring_active, monitor_thread
    
    if not monitoring_active:
        monitoring_active = True
        monitor_thread = threading.Thread(target=background_monitor, daemon=True)
        monitor_thread.start()
        return jsonify({'status': 'success', 'message': 'Monitoring started'})
    else:
        return jsonify({'status': 'info', 'message': 'Monitoring already active'})


@app.route('/api/stop', methods=['POST'])
def stop_monitoring():
    """Stop background monitoring"""
    global monitoring_active
    
    monitoring_active = False
    return jsonify({'status': 'success', 'message': 'Monitoring stopped'})


@app.route('/api/reset', methods=['POST'])
def reset():
    """Reset all detectors"""
    monitor.reset_all()
    return jsonify({'status': 'success', 'message': 'All detectors reset'})


@app.route('/api/status')
def get_status():
    """Get monitoring status"""
    return jsonify({
        'monitoring_active': monitoring_active,
        'interval': monitoring_interval,
        'timestamp': latest_metrics.get('timestamp', None)
    })


if __name__ == '__main__':
    print("=" * 60)
    print("Server Anomaly Monitor Starting...")
    print("=" * 60)
    print("\n📊 Dashboard: http://localhost:5000")
    print("\n🔌 API Endpoints:")
    print("  GET  /api/metrics  - Get current metrics")
    print("  GET  /api/check    - Check for anomalies")
    print("  GET  /api/history  - Get anomaly history")
    print("  GET  /api/status   - Get monitoring status")
    print("  POST /api/start    - Start monitoring")
    print("  POST /api/stop     - Stop monitoring")
    print("  POST /api/reset    - Reset detectors")
    print("\n" + "=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)