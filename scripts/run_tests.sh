#!/bin/bash

#Helper script to run tests
PYTHONPATH=.:src pytest  --cov=src --cov-report=xml test
