#!/usr/bin/env python3
"""
Quantum Sniffer - Post-Quantum Cryptography Network Analysis Tool

A tool for detecting and analyzing post-quantum cryptographic algorithms
in network traffic, including SSH, TLS, IPsec, and other protocols.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read long description from README
readme_file = Path(__file__).parent / "README.md"
long_description = ""
if readme_file.exists():
    long_description = readme_file.read_text(encoding='utf-8')

setup(
    name="quantum-sniffer",
    version="0.2.0",
    description="Post-Quantum Cryptography Network Analysis Tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Illumio Community",
    author_email="community@illumio.com",
    url="https://github.com/illumio-community/quantum-sniffer",
    license="MIT",
    
    # Python version requirement
    python_requires=">=3.6",
    
    # Packages to include
    packages=find_packages(exclude=["tests", "tests.*", "examples", "scans"]),
    package_data={
        'quantum_sniffer': ['py.typed'],
    },
    include_package_data=True,
    
    # Dependencies
    install_requires=[
        "scapy>=2.4.0",
        "python-dotenv>=0.19.0",
        # Python 3.6 needs these backports
        "dataclasses>=0.6; python_version<'3.7'",
        "contextvars>=2.4; python_version<'3.7'",
        "importlib-metadata>=1.0; python_version<'3.8'",
    ],
    
    # Optional dependencies
    extras_require={
        'dev': [
            'pytest>=6.0',
            'pytest-cov>=2.10',
            'mypy>=0.910',
        ],
        'api': [
            'fastapi>=0.70.0,<1.0.0',
            'pydantic>=1.8.0,<2.0.0',
            'uvicorn>=0.15.0',
        ],
        'illumio': [
            'python-dotenv>=0.19.0',
        ],
    },
    
    # Entry points (console scripts)
    entry_points={
        'console_scripts': [
            'quantum-sniffer=quantum_sniffer.cli.app:main',
        ],
    },
    
    # Classifiers
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Information Technology",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Telecommunications Industry",
        "License :: OSI Approved :: MIT License",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Security",
        "Topic :: System :: Networking :: Monitoring",
    ],
    
    # Keywords
    keywords="post-quantum cryptography pqc security network-analysis tls ssh ipsec",
    
    # Project URLs
    project_urls={
        "Bug Reports": "https://github.com/illumio-community/quantum-sniffer/issues",
        "Source": "https://github.com/illumio-community/quantum-sniffer",
        "Documentation": "https://github.com/illumio-community/quantum-sniffer/blob/main/README.md",
    },
)
