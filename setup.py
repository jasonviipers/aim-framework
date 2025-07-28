#!/usr/bin/env python3
"""
Setup script for the AIM (Adaptive Intelligence Mesh) Framework.
"""

from setuptools import setup, find_packages
import os

# Read the README file
def read_readme():
    with open("README.md", "r", encoding="utf-8") as fh:
        return fh.read()

# Read requirements
def read_requirements():
    with open("requirements.txt", "r", encoding="utf-8") as fh:
        return [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="aim-framework",
    version="1.0.0",
    author="jasonviipers",
    author_email="support@jasonviipers",
    description="Adaptive Intelligence Mesh - A distributed coordination system for AI deployment and interaction",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/jasonviipers/aim-framework",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Intended Audience :: Science/Research",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Scientific/Engineering :: Artificial Intelligence",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Topic :: System :: Distributed Computing",
    ],
    python_requires=">=3.8",
    install_requires=read_requirements(),
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=5.0.0",
            "mypy>=0.991",
            "pre-commit>=2.20.0",
        ],
        "docs": [
            "sphinx>=5.0.0",
            "sphinx-rtd-theme>=1.0.0",
            "myst-parser>=0.18.0",
        ],
        "api": [
            "flask>=2.2.0",
            "flask-cors>=4.0.0",
            "gunicorn>=20.1.0",
        ],
        "visualization": [
            "matplotlib>=3.5.0",
            "plotly>=5.10.0",
            "networkx>=2.8.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "aim-server=aim.cli:start_server",
            "aim-benchmark=aim.cli:run_benchmark",
            "aim-init=aim.cli:init_framework",
        ],
    },
    include_package_data=True,
    package_data={
        "aim": [
            "config/*.json",
            "templates/*.html",
            "static/*",
        ],
    },
    zip_safe=False,
    keywords="ai artificial-intelligence distributed-systems mesh-network coordination agents",
    project_urls={
        "Bug Reports": "https://github.com/jasonviipers/aim-framework/issues",
        "Source": "https://github.com/jasonviipers/aim-framework",
        "Documentation": "https://aim-framework.readthedocs.io/",
    },
)

