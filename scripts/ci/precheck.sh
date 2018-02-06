#!/usr/bin/env bash

echo 'Running pylint on azext_alias/...'
pip install pylint
pylint azext_alias/
