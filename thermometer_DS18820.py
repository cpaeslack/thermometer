import glob
import time
import datetime
import argparse
import glob
from influxdb import InfluxDBClient

host = "192.168.178.51" #Could also set local ip address
port = 8086
user = "admin"
password = "admin"
dbname = "sensordata"

base_dir = '/sys/bus/w1/devices/'
device_folder = glob.glob(base_dir + '28*')[0]
device_file = device_folder + '/w1_slave'

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
    # Array of all arguments passed to script
    args=parser.parse_args()
    # Assign args to variables
    dbname=args.database
    runNo=args.run
    session=args.session
    sampling_rate=args.samplingrate
    be_verbose = args.verbose
    return dbname, session, runNo, sampling_rate, be_verbose

def read_temp_raw():
    f = open(device_file, 'r')
    lines = f.readlines()
    f.close()
    return lines

def read_sensor():
    lines = read_temp_raw()
    while lines[0].strip()[-3:] != 'YES':
        time.sleep(0.2)
        lines = read_temp_raw()
    equals_pos = lines[1].find('t=')
    if equals_pos != -1:
        temp_string = lines[1][equals_pos+2:]
        temp_c = float(temp_string) / 1000.0
        return temp_c

def get_data_points():
    # Get the three measurement values from the SenseHat sensors
    current_temp= read_sensor()
    timestamp = datetime.datetime.utcnow().isoformat()

    # Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1)
    datapoints = [
        {
            "measurement": session,
            "tags": {"runNum": runNo},
            "time": timestamp,
            "fields": {
                "temp_now_ds18820": current_temp,
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
