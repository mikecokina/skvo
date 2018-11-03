#!/bin/bash

START_DATE=2010/01/01
END_DATE=2018/12/31

echo ========= Removing metrics =========

abc=("a" "b" "c" "d" "e" "f" "g" "h" "i" "j" "k" "l" "m" "n" "o" "p" "q" "r" "s" "t" "u" "v" "w" "x" "y" "z" "0" "1" "2" "3" "4" "5" "6" "7" "8" "9")

for L in ${abc[@]};
    do
       echo ========= metrics will be removed: =========
       set -f
       VAR=$(/usr/share/opentsdb/bin/tsdb uid grep metrics "${L}.*" | grep -E -o "metrics(.)*:")
       VAR=${VAR//metrics/}
       VAR=${VAR//:/}
       VAR="$(echo -e "${VAR}" | sed -e 's/^[[:space:]]*//')"

       for m in $VAR;
         do
           echo ========= removing data "for": $m =========
           /usr/share/opentsdb/bin/tsdb scan ${START_DATE} ${END_DATE} none "$m" --delete

           echo ========= removing metric "for": $m =========
           /usr/share/opentsdb/bin/tsdb uid delete metric $m
       done;
    done;

echo ========= Done. Data and metrics was removed.  =========
