#!/usr/bin/env bash

function usage {
  echo "Usage: run_vitrage_tempest.sh [OPTIONS]"
  echo "Run Vitrage Tempest tests"
  echo ""
  echo "  -h, --help               Print this usage message"
}

#case "$1" in
#    -h|--help) usage; exit;;
#    *) echo "Unknown command"; usage; exit;;
#esac

function run_tests {

  find . -type f -name "*.pyc" -delete

  echo "run env"
  nosetests -vx vitrage_tempest_tests/tests/run_vitrage_env.py
  sleep 10s

  echo "run tests"
  nosetests -vx vitrage_tempest_tests/tests/api/topology/*
  sleep 5s

  echo "stop env"
  nosetests -vx vitrage_tempest_tests/tests/stop_vitrage_env.py
}

run_tests