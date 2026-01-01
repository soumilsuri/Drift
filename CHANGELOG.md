# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2025-01-XX

### Added
- Initial release of drift-sre
- CUMSUM algorithm for detecting sustained shifts
- EWMA algorithm for adaptive detection
- System metrics collection via psutil
- Discord webhook notifications with rate limiting
- Per-metric configuration support
- Custom metrics registration
- Background monitoring thread
- Recovery notifications
- Comprehensive documentation
- Example integrations for Flask, FastAPI, Django

### Features
- CPU, RAM, disk, network, and connection monitoring
- Configurable anomaly detection thresholds
- Thread-safe operations
- Embeddable design (runs in same process)
- Smart default configurations for all metrics

