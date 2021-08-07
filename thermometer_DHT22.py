import glob
import time
import datetime
import argparse
import board
import adafruit_dht
from influxdb import InfluxDBClient

# Set required InfluxDB parameters.
host = "192.168.178.51" #Could also set local ip address
port = 8086
user = "admin"
password = "admin"
dbname = "sensordata"

def get_args():
    '''This function parses and returns arguments passed in'''
    # Assign description to the help doc
    parser = argparse.ArgumentParser(description='Program writes sensor measurement data to specified influx db.')
    # Add arguments
    parser.add_argument(
    '-db','--database', type=str, help='Database name', required=True)
    parser.add_argument(
    '-sn','--session', type=str, help='Session', required=True)
    now = datetime.datetime.now()
    parser.add_argument(
    '-rn','--run', type=str, help='Run number', required=False, default=now.strftime("%Y%m%d%H%M"))
    parser.add_argument(
    '-dt','--samplingrate', type=int, help='Sampling rate in seconds (default: 60)', required=False, default=60)
    parser.add_argument(
    '-v','--verbose', type=str, help='Be loud and noisy', required=False, default="no")
    parser.add_argument(
    '-gpio','--gpio_pin', type=str, help='ID of GPIO pin on raspberrypi (e.g. as "D4" for GPIO4)', required=True)
    # Array of all arguments passed to script
    args=parser.parse_args()
    # Assign args to variables
    dbname=args.database
    runNo=args.run
    session=args.session
    sampling_rate=args.samplingrate
    be_verbose = args.verbose
    gpio_pin = args.gpio_pin
    return dbname, session, runNo, sampling_rate, be_verbose, gpio_pin

def initialize_dht(pin):
    # Initialize the dht device, with data pin connected to:
    # dhtDevice = adafruit_dht.DHT22(board.D4)

    # you can pass DHT22 use_pulseio=False if you wouldn't like to use pulseio.
    # This may be necessary on a Linux single board computer like the Raspberry Pi,
    # but it will not work in CircuitPython.
    dhtDevice = adafruit_dht.DHT22(board.pin, use_pulseio=False)
    return dhtDevice

def read_sensor():
    temperature = dhtDevice.temperature
    humidity = dhtDevice.humidity
    return temperature, humidity

def get_data_points():
    # Get the three measurement values from the SenseHat sensors
    current_temp, current_humidity = read_sensor()
    timestamp = datetime.datetime.utcnow().isoformat()

    # Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1)
    datapoints = [
        {
            "measurement": session,
            "tags": {"runNum": runNo},
            "time": timestamp,
            "fields": {
                "temp_now_dht22": current_temp,
                "humid_now_dht22" : current_humidity,
            }
        }
    ]
    return datapoints

# Match return values from get_arguments()
# and assign to their respective variables
dbname, session, runNo, sampling_rate = get_args()
print "Session: ", session
print "Run No: ", runNo
print "DB name: ", dbname
print "Sampling rate: ", sampling_rate
print "Verbose mode: ", be_verbose

# Initialize dht sensor
dhtDevice = initialize_dht()

# Initialize the Influxdb client
client = InfluxDBClient(host, port, user, password, dbname)

while True:
    try:
        # Write datapoints to InfluxDB
        datapoints=get_data_points()
        bResult=client.write_points(datapoints)
        if be_verbose == "yes":
            print("Write points {0} Bresult:{1}".format(datapoints,bResult))

        # Wait for next sample
        time.sleep(sampling_rate)

    except RuntimeError as error:
        print(error.args[0])
        time.sleep(sampling_rate)
        continue

    except Exception as error:
        dhtDevice.exit()
        raise error

    except KeyboardInterrupt:
        print ("Program stopped by keyboard interrupt [CTRL+C] by user. ")
