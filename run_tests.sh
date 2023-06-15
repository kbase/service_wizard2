#!/usr/bin/env bash

#( grep -vE "^(#.*|\s*)$" .env ) | xargs
PYTHONPATH=. pytest test
