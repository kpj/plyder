#!/usr/bin/env bash
# PLYDER_HOST: mega.nz

url="$1"
output_dir="$2"

DURATION=$((60 * 10))
echo Duration: ${DURATION}s

while true; do
  timeout -k $DURATION $DURATION megadl --path "$output_dir" "$url"
  ret=$?

  if [ "$ret" -lt "100" ]; then
    # megadl did not timeout but finish on its own
    echo Download finished...
    break
  fi

  # megadl did timeout so we have to try again
  sleep $DURATION
  echo Retrying...
done