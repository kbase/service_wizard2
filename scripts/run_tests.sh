#!/bin/bash
# Helper script to run tests
PYTHONPATH=.:src pytest --cov=src --cov-report term-missing --cov-fail-under=99 --cov-report=xml:coverage.xml  -W ignore::DeprecationWarning test
