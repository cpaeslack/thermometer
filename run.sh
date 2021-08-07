#!/bin/bash
set -e

helptext="provide type of sensor ('DHT22' or 'DS18B20')"

if [ -z "$1" ]
then
    echo ${helptext}
    exit
fi

sensor=${1}
fname=thermometer_${sensor}.py

if [ "${sensor}" == "DHT22" ] || [ "${sensor}" == "DS18B20" ]
then
    python3 ${fname} -db=sensordata -sn=test -v yes -dt 10
else
    echo ${helptext}
    exit
fi
