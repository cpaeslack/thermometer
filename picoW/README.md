# Measure & send DHT22 sensor data with Rasperry Pi Pico W

This code automates the measurement of temperature and humidity data
of a DHT22 sensor with a Raspberry Pi Pico W and sending them via HTTP request
to a InfluxDB database (v1.x).
The code can make use of the light sleep mode the RPi Pico provides,
which is useful when running the device on battery (set `USE_LIGHT_SLEEP = True`).

The file `config.py` should contain all necessary variables that must be
set by the user (e.g. wifi ssid/password, database, etc.). Start from the provided
`config.py.template`.

The module `wifi_connect.py` contains functions to connect and disconnect from
wifi and to print wifi status.

The file `main.py` is the main program code that must be named like
this exactly to be run automatically if placed on a RPi Pico W that is
run standalone.

Make sure to place all three files on the device!