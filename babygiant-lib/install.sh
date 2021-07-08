#!/bin/bash

# tries to auto-install babygiant-lib using the available pre-built wheels if possible, otherwise install from source

ok=0
for f in ./dist/*.whl; do
  pip install $f 2>/dev/null
  retVal=$?
  if [ $retVal -eq 0 ]; then
    ok=1
    break
  fi
done

if [ $ok -eq 0 ]; then
  # did not find a suitable wheel, try building from source
  pip install .
  retVal=$?
  if [ $retVal -ne 0 ]; then
    echo "Unable to automatically install babygiant-lib"
    exit 1
  fi
fi
