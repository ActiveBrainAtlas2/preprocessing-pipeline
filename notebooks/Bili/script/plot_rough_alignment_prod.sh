#!/usr/bin/env bash
for brain in DK39 DK41 DK43 DK54 DK55
do
    ./plot_rough_alignment.py $brain --zstep 10
done
