#!/bin/bash

echo "read all files from '$1'"
echo "store results in '$1/tuples'"
echo "Ok?"
read

mkdir $1/tuples || true

# Read the files in the directory
for file in "$1"/*
do

    if [[ $file == *".txt"* ]]; then
        echo "FILE:" $file
        # execute perl script to generate tuples from the file
        perl generate-BWS-tuples.pl $file
    fi
done

echo "written files:"
ls -1 $1/tuples
