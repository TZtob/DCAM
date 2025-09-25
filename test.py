#!/usr/bin/env python3
print("Hello World!")
print("Testing Python environment")

try:
    import flask
    print("Flask is available")
except ImportError:
    print("Flask is NOT available")

try:
    import yaml
    print("PyYAML is available")
except ImportError:
    print("PyYAML is NOT available")
