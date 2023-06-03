import argparse
import datetime
from dotenv import load_dotenv
import logging
import os
import time
import Adafruit_DHT
from influxdb import InfluxDBClient
import sys


class Sensor:
    """Class representing the DHT22 temperature/humidity sensor"""

    def __init__(self, sensor_pin) -> None:
        self.SENSOR = Adafruit_DHT.DHT22
        self.SENSOR_PIN = sensor_pin

    def read_sensor(self):
        humidity, temperature = Adafruit_DHT.read_retry(
            self.SENSOR, self.SENSOR_PIN
        )
        return temperature, humidity

    def prepare_datapoints(self, session, runNo):
        # Get the three measurement values from the SenseHat sensors
        current_temp, current_humidity = self.read_sensor()
        logging.info(f"temp: {current_temp}, hum: {current_humidity}")
        timestamp = datetime.datetime.utcnow().isoformat()

        # Create Influxdb datapoints (using lineprotocol as of Influxdb >1.1)
        datapoints = [
            {
                "measurement": session,
                "tags": {"runNum": runNo},
                "time": timestamp,
                "fields": {
                    "temp_now_dht22": current_temp,
                    "humid_now_dht22": current_humidity,
                },
            }
        ]
        return datapoints


class Database:
    """Class representing the InfluxDB database connection"""

    def __init__(self, host, port, user, password, dbname) -> None:
        self.client = InfluxDBClient(host, port, user, password, dbname)

    def store_data(self, data, be_verbose):
        try:
            bResult = self.client.write_points(data)
            if be_verbose == "yes":
                logging.info(
                    "Write points {0} Bresult:{1}".format(data, bResult)
                )
        except Exception as e:
            logging.error(f"Failed to write to database. Reason: {e}")
            raise e

    def close_connection(self):
        self.client.close()


def main():
    """Main loop of the program, calls the subprocesses after 10 seconds if they are not running"""

    # Set format of log messages
    logging.basicConfig(
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="[%Y-%m-%d %H:%M:%S]",
        level=logging.INFO,
    )

    load_dotenv()
    HOST = os.getenv("HOST")
    PORT = os.getenv("PORT")
    USER = os.getenv("USER")
    PASSWORD = os.getenv("PASSWORD")
    SENSOR_PIN = os.getenv("SENSOR_PIN")

    # Match return values from get_arguments()
    # and assign to their respective variables
    dbname, session, runNo, sampling_rate, be_verbose = get_args()
    logging.info(f"Session: {session}")
    logging.info(f"Run No: {runNo}")
    logging.info(f"DB name: {dbname}")
    logging.info(f"Sampling rate: {sampling_rate}")
    logging.info(f"Verbose mode: {be_verbose}")

    while True:
        sensor = Sensor(SENSOR_PIN)
        try:
            # Create database connection
            database = Database(HOST, PORT, USER, PASSWORD, dbname)
            # Get datapoints and write to database
            datapoints = sensor.prepare_datapoints(session, runNo)
            database.store_data(datapoints, be_verbose)
            # Close database connection
            database.close_connection()
            # Wait for next sample
            time.sleep(sampling_rate)

        except RuntimeError as e:
            # GPIO access may require sudo permissions
            # Other RuntimeError exceptions may occur, but
            # are common.  Just try again.
            logging.error(f"RuntimeError: {e}")
            logging.error("GPIO Access may need sudo permissions.")

            time.sleep(2.0)
            continue

        except KeyboardInterrupt:
            logging.info(
                "Program stopped by keyboard interrupt [CTRL+C] by user. "
            )
            sys.exit(0)


def get_args():
    """This function parses and returns arguments passed in"""
    # Assign description to the help doc
    parser = argparse.ArgumentParser(
        description="Program writes sensor measurement data to specified influx db."
    )
    # Add arguments
    parser.add_argument(
        "-db", "--database", type=str, help="Database name", required=True
    )
    parser.add_argument(
        "-sn", "--session", type=str, help="Session", required=True
    )
    now = datetime.datetime.now()
    parser.add_argument(
        "-rn",
        "--run",
        type=str,
        help="Run number",
        required=False,
        default=now.strftime("%Y%m%d%H%M"),
    )
    parser.add_argument(
        "-dt",
        "--samplingrate",
        type=int,
        help="Sampling rate in seconds (default: 60)",
        required=False,
        default=60,
    )
    parser.add_argument(
        "-v",
        "--verbose",
        type=str,
        help="Be loud and noisy",
        required=False,
        default="no",
    )
    # Array of all arguments passed to script
    args = parser.parse_args()
    # Assign args to variables
    dbname = args.database
    runNo = args.run
    session = args.session
    sampling_rate = args.samplingrate
    be_verbose = args.verbose
    return dbname, session, runNo, sampling_rate, be_verbose


if __name__ == "__main__":
    main()
