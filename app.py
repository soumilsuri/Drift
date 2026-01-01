"""
Flask Server for Real-time Anomaly Monitoring with Configuration
Provides REST API for monitoring and configuring detection per metric
"""

from flask import Flask, jsonify, render_template_string, request
from anomaly_detector import AnomalyMonitor, ServerMetrics, MetricConfig
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
                max-width: 1400px;
                margin: 0 auto;
            }
            h1 { color: #333; }
            h2 { color: #555; margin-top: 0; }
            
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
            .btn-primary { background: #007bff; color: white; }
            .btn-danger { background: #dc3545; color: white; }
            .btn-secondary { background: #6c757d; color: white; }
            .btn-success { background: #28a745; color: white; }
            
            .config-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(350px, 1fr));
                gap: 15px;
                margin-top: 15px;
            }
            
            .config-item {
                border: 1px solid #dee2e6;
                padding: 15px;
                border-radius: 5px;
                background: #f8f9fa;
            }
            
            .config-item h3 {
                margin-top: 0;
                color: #007bff;
                font-size: 16px;
            }
            
            .config-row {
                margin: 8px 0;
            }
            
            .config-row label {
                display: inline-block;
                width: 140px;
                font-size: 13px;
                color: #495057;
            }
            
            .config-row input, .config-row select {
                width: 120px;
                padding: 4px 8px;
                border: 1px solid #ced4da;
                border-radius: 3px;
                font-size: 13px;
            }
            
            .config-row input[type="checkbox"] {
                width: auto;
            }
            
            .config-description {
                font-size: 12px;
                color: #6c757d;
                font-style: italic;
                margin-top: 5px;
            }
            
            .two-column {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 20px;
            }
            
            @media (max-width: 968px) {
                .two-column {
                    grid-template-columns: 1fr;
                }
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
            
            <div class="two-column">
                <div class="card">
                    <h2>Current Status</h2>
                    <div id="status"></div>
                </div>
                
                <div class="card">
                    <h2>Anomaly Detection Results</h2>
                    <div id="anomalies"></div>
                </div>
            </div>
            
            <div class="card">
                <h2>Server Metrics</h2>
                <div id="metrics"></div>
            </div>
            
            <div class="card">
                <h2>⚙️ Detector Configuration</h2>
                <p style="color: #6c757d; margin-bottom: 15px;">
                    Tune each metric's detection parameters. Lower thresholds = more sensitive.
                    Changes take effect immediately.
                </p>
                <div id="configs"></div>
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
                if (confirm('Reset all detectors? This will clear history and restart detection.')) {
                    fetch('/api/reset', {method: 'POST'})
                        .then(r => r.json())
                        .then(data => {
                            alert(data.message);
                            refreshData();
                        });
                }
            }
            
            function updateConfig(metric) {
                const config = {
                    enabled: document.getElementById(`${metric}_enabled`).checked,
                    algorithm: document.getElementById(`${metric}_algorithm`).value,
                };
                
                if (config.algorithm === 'CUMSUM') {
                    config.threshold = parseFloat(document.getElementById(`${metric}_threshold`).value);
                    config.drift = parseFloat(document.getElementById(`${metric}_drift`).value);
                    config.reference_mean = parseFloat(document.getElementById(`${metric}_reference`).value);
                } else {
                    config.alpha = parseFloat(document.getElementById(`${metric}_alpha`).value);
                    config.threshold_sigma = parseFloat(document.getElementById(`${metric}_sigma`).value);
                }
                
                fetch(`/api/config/${metric}`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(config)
                })
                .then(r => r.json())
                .then(data => {
                    if (data.status === 'success') {
                        alert(`✓ Configuration updated for ${metric}`);
                        refreshData();
                    } else {
                        alert(`Error: ${data.message}`);
                    }
                })
                .catch(err => alert(`Error: ${err}`));
            }
            
            function toggleAlgorithm(metric) {
                const algo = document.getElementById(`${metric}_algorithm`).value;
                const cumsumDiv = document.getElementById(`${metric}_cumsum`);
                const ewmaDiv = document.getElementById(`${metric}_ewma`);
                
                if (algo === 'CUMSUM') {
                    cumsumDiv.style.display = 'block';
                    ewmaDiv.style.display = 'none';
                } else {
                    cumsumDiv.style.display = 'none';
                    ewmaDiv.style.display = 'block';
                }
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
                        if (data.metrics && Object.keys(data.metrics).length > 1) {
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
                            let html = `<p><span class="status alert">⚠️ ${data.anomaly_count} Anomalies</span></p>`;
                            data.anomalies.forEach(anomaly => {
                                html += `
                                    <div class="anomaly ${anomaly.severity}">
                                        <strong>${anomaly.metric}</strong>: ${anomaly.value.toFixed(2)} 
                                        <br><small>Score: ${anomaly.score.toFixed(2)} | ${anomaly.algorithm} | 
                                        Severity: ${anomaly.severity} | Duration: ${anomaly.duration || 1}</small>
                                    </div>
                                `;
                            });
                            anomaliesDiv.innerHTML = html;
                        } else {
                            anomaliesDiv.innerHTML = '<p><span class="status normal">✓ All Normal</span></p>';
                        }
                    });
                
                // Get configs
                fetch('/api/config')
                    .then(r => r.json())
                    .then(data => {
                        let configDiv = document.getElementById('configs');
                        let html = '<div class="config-grid">';
                        
                        for (let [metric, config] of Object.entries(data.configs)) {
                            html += `
                                <div class="config-item">
                                    <h3>${metric}</h3>
                                    <div class="config-description">${config.description || ''}</div>
                                    
                                    <div class="config-row">
                                        <label>
                                            <input type="checkbox" id="${metric}_enabled" 
                                                   ${config.enabled ? 'checked' : ''}>
                                            Enabled
                                        </label>
                                    </div>
                                    
                                    <div class="config-row">
                                        <label>Algorithm:</label>
                                        <select id="${metric}_algorithm" onchange="toggleAlgorithm('${metric}')">
                                            <option value="CUMSUM" ${config.algorithm === 'CUMSUM' ? 'selected' : ''}>CUMSUM</option>
                                            <option value="EWMA" ${config.algorithm === 'EWMA' ? 'selected' : ''}>EWMA</option>
                                        </select>
                                    </div>
                                    
                                    <div id="${metric}_cumsum" style="display: ${config.algorithm === 'CUMSUM' ? 'block' : 'none'}">
                                        <div class="config-row">
                                            <label>Threshold:</label>
                                            <input type="number" step="0.1" id="${metric}_threshold" value="${config.threshold}">
                                        </div>
                                        <div class="config-row">
                                            <label>Drift:</label>
                                            <input type="number" step="0.1" id="${metric}_drift" value="${config.drift}">
                                        </div>
                                        <div class="config-row">
                                            <label>Reference Mean:</label>
                                            <input type="number" step="0.1" id="${metric}_reference" value="${config.reference_mean || 0}">
                                        </div>
                                    </div>
                                    
                                    <div id="${metric}_ewma" style="display: ${config.algorithm === 'EWMA' ? 'block' : 'none'}">
                                        <div class="config-row">
                                            <label>Alpha (0-1):</label>
                                            <input type="number" step="0.01" min="0" max="1" id="${metric}_alpha" value="${config.alpha}">
                                        </div>
                                        <div class="config-row">
                                            <label>Threshold Sigma:</label>
                                            <input type="number" step="0.1" id="${metric}_sigma" value="${config.threshold_sigma}">
                                        </div>
                                    </div>
                                    
                                    <button class="btn-success" onclick="updateConfig('${metric}')" style="width: 100%; margin-top: 10px;">
                                        Update
                                    </button>
                                </div>
                            `;
                        }
                        
                        html += '</div>';
                        configDiv.innerHTML = html;
                    });
                
                // Get history
                fetch('/api/history')
                    .then(r => r.json())
                    .then(data => {
                        let historyDiv = document.getElementById('history');
                        if (data.history && data.history.length > 0) {
                            let html = `<p><strong>Total anomalies:</strong> ${data.count}</p>`;
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


@app.route('/api/config', methods=['GET'])
def get_configs():
    """Get all metric configurations"""
    configs = monitor.get_all_configs()
    config_dict = {}
    
    for metric_name, config in configs.items():
        config_dict[metric_name] = {
            'algorithm': config.algorithm,
            'threshold': config.threshold,
            'drift': config.drift,
            'reference_mean': config.reference_mean,
            'alpha': config.alpha,
            'threshold_sigma': config.threshold_sigma,
            'enabled': config.enabled,
            'description': config.description
        }
    
    return jsonify({'configs': config_dict})


@app.route('/api/config/<metric_name>', methods=['POST'])
def update_config(metric_name):
    """Update configuration for a specific metric"""
    try:
        data = request.json
        
        config = MetricConfig(
            algorithm=data.get('algorithm', 'CUMSUM'),
            threshold=data.get('threshold', 5.0),
            drift=data.get('drift', 0.5),
            reference_mean=data.get('reference_mean'),
            alpha=data.get('alpha', 0.3),
            threshold_sigma=data.get('threshold_sigma', 3.0),
            enabled=data.get('enabled', True),
            description=monitor.get_config(metric_name).description if monitor.get_config(metric_name) else ""
        )
        
        monitor.update_metric_config(metric_name, config)
        
        return jsonify({
            'status': 'success',
            'message': f'Configuration updated for {metric_name}',
            'config': {
                'algorithm': config.algorithm,
                'threshold': config.threshold,
                'drift': config.drift,
                'reference_mean': config.reference_mean,
                'alpha': config.alpha,
                'threshold_sigma': config.threshold_sigma,
                'enabled': config.enabled
            }
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 400


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
    print("Server Anomaly Monitor with Configuration")
    print("=" * 60)
    print("\n📊 Dashboard: http://localhost:5000")
    print("\n🔌 API Endpoints:")
    print("  GET  /api/metrics       - Get current metrics")
    print("  GET  /api/check         - Check for anomalies")
    print("  GET  /api/history       - Get anomaly history")
    print("  GET  /api/config        - Get all configurations")
    print("  POST /api/config/<name> - Update metric configuration")
    print("  GET  /api/status        - Get monitoring status")
    print("  POST /api/start         - Start monitoring")
    print("  POST /api/stop          - Stop monitoring")
    print("  POST /api/reset         - Reset detectors")
    print("\n" + "=" * 60)
    
    app.run(debug=True, host='0.0.0.0', port=5000)