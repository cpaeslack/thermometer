#!/bin/bash
set -e

if -z ${1}
then
    echo "provide type of sensor ('DHT22' or 'DS18B20 ')"

fname=thermometer_${1}.py

python ${fname} -db=sensordata -sn=test
