#!/usr/bin/env bash
# PLYDER_HOST: mega.nz

url="$1"
output_dir="$2"

megadl --path "$output_dir" "$url"
