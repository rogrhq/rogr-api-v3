"""
Pytest configuration for ROGRv2 tests.

This file is loaded BEFORE any test modules are imported.
Critical for setting environment variables that affect module initialization.
"""

import os

# Fix tokenizer fork deadlock (Task 2.4)
# CRITICAL: Must be set BEFORE any imports that load transformers/tokenizers
# This prevents deadlock when parallel R1/R2 execution uses SpaCy/transformers
os.environ["TOKENIZERS_PARALLELISM"] = "false"

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv(override=True)
