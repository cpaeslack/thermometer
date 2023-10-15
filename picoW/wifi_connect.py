# -*- coding: utf-8 -*-
"""Wifi Connection Module for Raspberry Pi Pico W
Connecting Wifi, disconnecting Wifi and Wifi status
Please configure SSID, Password and CountryCode in config.py
"""

import config
import machine
import time
import network
import usocket as socket
import ustruct as struct

# Declare Wifi network
wifi = network.WLAN(network.STA_IF)
# Declare LED
if config.LED_STATUS:
    led = machine.Pin('LED', machine.Pin.OUT)

# Winterzeit / Sommerzeit
#GMT_OFFSET = 3600 * 1 # 3600 = 1 h (Winterzeit)
GMT_OFFSET = 3600 * 2 # 3600 = 1 h (Sommerzeit)


def flash_led(sleep_time, iterations=10):
    """ flashes the LED repeatedly """

    for _ in range(iterations):
        # do some LED flashing to indicate state of device
        led.on()
        time.sleep(sleep_time)
        led.off()
        time.sleep(sleep_time)


def getTimeNTP():
    """ Get current time from NTP server"""

    ntp_host = 'pool.ntp.org'
    ntp_delta = 2208988800
    ntp_query = bytearray(48)
    ntp_query[0] = 0x1B
    addr = socket.getaddrinfo(ntp_host, 123)[0][-1]
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(1)
        res = s.sendto(ntp_query, addr)
        msg = s.recv(48)
    finally:
        s.close()
    ntp_time = struct.unpack("!I", msg[40:44])[0]

    return time.gmtime(ntp_time - ntp_delta + GMT_OFFSET)


def setTimeRTC():
    """ Set the time from NTP server on device """

    tm = getTimeNTP()
    machine.RTC().datetime((tm[0], tm[1], tm[2], tm[6] + 1, tm[3], tm[4], tm[5], 0))


def connect():
    """ Connect to a wifi network
        SSID and password must be defined in `config.py`!
    """

    network.country(config.WIFI_COUNTRY_CODE)

    if not wifi.isconnected():
        print('establishing wifi connection ', end="")
        wifi.active(True)
        wifi.connect(config.WIFI_SSID, config.WIFI_PASSWORD)
        for _ in range(30):
            print(".", end="")
            if wifi.status() < 0 or wifi.status() >= 3:
                break
            # do some LED flashing to indicate state of device
            led.on()
            time.sleep(0.5)
            led.off()
            time.sleep(0.5)
        print()

    if wifi.isconnected():
        # do some LED flashing to indicate state of device
        if config.LED_STATUS:
            flash_led(0.25, wifi.status())
        print(f'wifi connection established: {wifi.status()}')
        netconfig = wifi.ifconfig()
        print('IPv4 address:', netconfig[0])
        setTimeRTC()
        # print current date & time
        print(machine.RTC().datetime())
        return netconfig[0]
    else:
        print('wifi status:', wifi.status())
        raise RuntimeError('wifi connection failed')


def disconnect():
    wifi.disconnect()
    wifi.active(False)
    wifi.deinit()
    # Quick Fix for deinit and lightsleep mode problem https://github.com/micropython/micropython/discussions/10889
    wifi_led = machine.Pin('LED', machine.Pin.OUT)
    machine.Pin(23, machine.Pin.IN, machine.Pin.PULL_DOWN)
    flash_led(0.25,3)
    print('wifi disconnected: ' + str(wifi.status()))


def status():
    print(f"wifi status: {wifi.status()}")
