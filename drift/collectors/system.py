"""
System metrics collector using psutil
"""

import psutil
from datetime import datetime
from typing import Dict


class SystemMetricsCollector:
    """Collect server metrics using psutil"""
    
    @staticmethod
    def collect() -> Dict[str, float]:
        """
        Get all server metrics at once
        
        Returns:
            Dictionary of metric names to values
        """
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory metrics
        memory = psutil.virtual_memory()
        ram_percent = memory.percent
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0.0
        disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0.0
        
        # Network metrics
        net_io = psutil.net_io_counters()
        net_sent_mb = net_io.bytes_sent / (1024 * 1024) if net_io else 0.0
        net_recv_mb = net_io.bytes_recv / (1024 * 1024) if net_io else 0.0
        
        # System load (1 minute average)
        try:
            load_avg = psutil.getloadavg()[0]  # 1-minute load average
        except (AttributeError, OSError):
            # Windows doesn't support getloadavg
            load_avg = cpu_percent / 100.0 * psutil.cpu_count()
        
        # Connection errors (approximation using connection count)
        try:
            connections = len(psutil.net_connections())
        except (psutil.AccessDenied, OSError):
            connections = 0
        
        return {
            'cpu_percent': cpu_percent,
            'ram_percent': ram_percent,
            'disk_read_mb': disk_read_mb,
            'disk_write_mb': disk_write_mb,
            'net_sent_mb': net_sent_mb,
            'net_recv_mb': net_recv_mb,
            'load_avg': load_avg,
            'connections': float(connections),
            'timestamp': datetime.now().isoformat()
        }

