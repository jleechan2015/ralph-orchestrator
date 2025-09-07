#!/usr/bin/env python3
# ABOUTME: Simple script to run Ralph Orchestrator
# ABOUTME: Provides an easy way to test the orchestrator with different tools

"""Simple runner script for Ralph Orchestrator."""

import sys
import os

# Add src to path so we can import the package
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from ralph_orchestrator.__main__ import main

if __name__ == "__main__":
    main()