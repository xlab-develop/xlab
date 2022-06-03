#!/bin/bash

for f in linear quadratic sqrt
do
    python generate_data.py $f
done
