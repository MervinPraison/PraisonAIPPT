# Shim retained for `pip install -e .` on tooling that still invokes setup.py.
# All real package metadata lives in pyproject.toml.
from setuptools import setup

setup()
