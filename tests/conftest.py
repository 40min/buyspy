"""
Pytest configuration file for setting up test environment.

This file is loaded before any test modules and sets up the test environment
to use .env.test instead of .env for testing.
"""

import os

# Set test environment file BEFORE any imports that could trigger config loading
os.environ["ENV_FILE"] = ".env.test"
