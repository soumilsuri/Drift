"""
Setup script for drift-sre
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README for long description
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text(encoding="utf-8") if readme_file.exists() else ""

setup(
    name="drift-sre",
    version="0.1.0",
    description="Real-time Anomaly Detection Library for SRE with Discord notifications",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="soumilsuri",
    url="https://github.com/soumilsuri/Drift",
    packages=find_packages(exclude=["tests", "examples", "docs"]),
    python_requires=">=3.8",
    install_requires=[
        "psutil>=5.9.0",
        "requests>=2.28.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
        ],
    },
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: System Administrators",
        "Topic :: System :: Monitoring",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    keywords="monitoring, anomaly-detection, sre, discord, alerts, metrics",
    project_urls={
        "Documentation": "https://github.com/soumilsuri/Drift#readme",
        "Source": "https://github.com/soumilsuri/Drift",
        "Tracker": "https://github.com/soumilsuri/Drift/issues",
    },
)

