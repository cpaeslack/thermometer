# -*- coding: utf-8 -*-
"""Measure and send DHT22 sensor data from Raspberry Pi Pico W
to InfluxDB via HTTP request.
After sending data the wifi is disconnected and device set
to light sleep mode to save energy (e.g. when running from battery).
"""

from machine import reset, lightsleep, Pin
import utime as time
import urequests as requests
from dht import DHT22
import config
import wifi_connect


# LED declaration
if config.LED_STATUS:
    led = Pin('LED', Pin.OUT)
    led.value(True)

# Initialization of GPIO und DHT22
time.sleep(1)
dht22_sensor = DHT22(Pin(config.SENSOR_GPIO_PIN, Pin.IN, Pin.PULL_UP))


def dht22_measure():
    """ Measure sensor data """

    dht22_sensor.measure()
    temperature = dht22_sensor.temperature()
    humidity = dht22_sensor.humidity()

    return temperature, humidity


def send_data(measurement, temperature, humidity):
    """ Send data via POST HTTP request to influx database
        on remote server.
    """

    time_ns = time.time_ns()
    base_url = f"http://{config.HOST_DB}"
    post_url = f"{base_url}/write?db={config.DATABASE}"

    db_status = requests.get(f"{base_url}/ping").status_code
    if db_status == 204:
        payload = f"{measurement},{config.INFLUXTAG}={config.INFLUXTAG_VALUE} luftfeuchte={humidity} {time_ns}"
        req = requests.post(post_url, data=payload)
        print(req.status_code)
        print("wrote humidity to database")
        payload = f"{measurement},{config.INFLUXTAG}={config.INFLUXTAG_VALUE} temperatur={temperature} {time_ns}"
        req = requests.post(post_url, data=payload)
        print(req.status_code)
        print("wrote temperature to database")
    else:
        wifi_connect.flash_led(0.1)
        print("database not available!")


while True:
    try:
        # read sensor
        temperature, humidity = dht22_measure()
        print(f"temperature: {temperature}")
        print(f"humidity: {humidity}")
        # connect to wifi
        wifi_connect.connect()
        if config.LED_STATUS:
            led.value(True)
        # send data to influxdb API
        send_data(config.MEASUREMENT, temperature, humidity)
        time.sleep(.3)
        if config.USE_LIGHT_SLEEP:
            time.sleep(.3)
            wifi_connect.disconnect()
            print(f"going to lightsleep for {config.SLEEP_DURATION} seconds")
            if config.LED_STATUS:
                led.value(False)
            time.sleep(.1)
            lightsleep(config.SLEEP_DURATION * 1000)
        else:
            time.sleep(.3)
            wifi_connect.disconnect()
            print(f"sleeping for {config.SLEEP_DURATION} seconds")
            if config.LED_STATUS:
                led.value(False)
            time.sleep(config.SLEEP_DURATION)
    except RuntimeError as e:
        print("resetting device due to runtime error")
        wifi_connect.flash_led(0.1)
        reset()
    except OSError as e:
        print("resetting device due to os error")
        wifi_connect.flash_led(0.1)
        reset()
    except KeyboardInterrupt:
        print("Keyboard interrupt")
        break
