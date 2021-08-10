#!/bin/bash
set -e

helptext="provide type of sensor ('DHT22' or 'DS18B20')"
dir="/home/pi/Code/thermometer"

if [ -z "$1" ]
then
    echo ${helptext}
    exit
fi

sensor=${1}
fname=thermometer_${sensor}.py

if [ "${sensor}" == "DHT22" ] || [ "${sensor}" == "DS18B20" ]
then
    python3 ${dir}/${fname} -db=sensordata \
                            -sn=test \
                            -v=no -dt=30 > "/home/pi/log/sensor-${sensor}.log"
else
    echo ${helptext}
    exit
fi
