#!/bin/bash

echo "scanning devices ..."
mpremote connect list

echo -e "\ndirectory tree ..."
mpremote fs tree -s

echo -e "\nremoving all current files ..."
mpremote rm -rv :

echo -e "\ncreating /sd ..."
mpremote mkdir :/sd

echo -e "\ncopying programs ..."
mpremote fs cp device/main.py :main.py
mpremote fs cp -r device/lib :lib

echo -e "\n\nstarting program main.py"
mpremote run :main.py

