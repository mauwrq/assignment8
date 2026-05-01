import socket
import psycopg2
import json
import os
from dotenv import load_dotenv
from contextlib import contextmanager
import numpy as np
import time
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

load_dotenv()
MARC_DB = os.getenv("MARC_DB")
BERT_DB = os.getenv("BERT_DB")

DATA_SHARE_TIME = "1777524303"
SECONDS_IN_DAY = 24 * 60 * 60

command_list = [
    {"code" : "MOISTURE_LEVEL", "display" : "What is the average moisture inside our kitchen fridges in the past hours, week and month?"},
    {"code" : "WATER_CONSUMPTION", "display" : "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?"},
    {"code" : "ELECTRICITY_USAGE", "display" : "Which house consumed more electricity in the past 24 hours, and by how much?"}
]

MARC_ELECTRICITY_SENSORS = [
    ("my2ndraspberrypi", "ammeter2"),
    ("myraspberrypi", "ammeter"),
]

ALBERT_ELECTRICITY_SENSORS = [
    ("raspberrypi", "Ammeter"),
    ("raspberrydish", "Ammeter_Dish"),
]

@contextmanager
def db_connect():
    conn_bert = None
    conn_marc = None
    try:
        conn_bert = psycopg2.connect(BERT_DB)
        conn_marc = psycopg2.connect(MARC_DB)
        yield conn_bert, conn_marc
    finally:
        if conn_bert: conn_bert.close()
        if conn_marc: conn_marc.close()

def build_query(sensor, measurement, table, board, time):
    query = f"""SELECT
(payload->>'timestamp')::double precision AS epoch_time,
payload->>'{sensor}' AS {measurement}
FROM {table}
WHERE payload->>'board_name' = '{board}'
AND to_timestamp((payload->>'timestamp')::double precision) {time}
AND payload->>'{sensor}' IS NOT NULL
ORDER BY epoch_time DESC;"""
    return query

def to_pst(epoch_seconds):
    return datetime.fromtimestamp(epoch_seconds, tz=timezone.utc).astimezone(
        ZoneInfo("America/Los_Angeles")
    ).strftime("%Y-%m-%d %I:%M:%S %p %Z")

def fetch_electricity_readings(cursor, table, sensors, time_filter):
    data = []

    for board, sensor in sensors:
        query = build_query(sensor, "electricity_usage", table, board, time_filter)
        cursor.execute(query)
        data += cursor.fetchall()

    return data

def sum_electricity_usage(data):
    total = 0.0

    for row in data:
        total += float(row[1])

    return total

def format_kwh(value):
    return f"{value:.2f}"

def format_sensor_list(sensors):
    return ", ".join(
        f"{board}/{sensor}" for board, sensor in sensors
    )

def query_moisture():
    #db stuff
    with db_connect() as (bert, marc):
        cur_marc = marc.cursor()
        marc_query = build_query('Moisture Meter - mymoisturemeter', 'moisture_level', 'neondata_virtual', 'my3rdrasppi', ">= NOW() - INTERVAL '1 month'")
        cur_marc.execute(marc_query)
        marc_data = cur_marc.fetchall()

        seconds_in_month = 30 * 24 * 60 * 60
        one_month_ago = time.time() - seconds_in_month
        if int(DATA_SHARE_TIME) < one_month_ago:
            cur_bert = marc.cursor()
            bert_query = build_query('Moisture Meter - moisture_meter', 'moisture_level', 'neondata_virtual', 'raspberrypi', ">= NOW() - INTERVAL '1 month'")
            cur_bert.execute(bert_query)
            bert_data = cur_bert.fetchall()
        else:
            cur_bert1 = marc.cursor()
            cur_bert2 = bert.cursor()
            bert_query1 = build_query('Moisture Meter - moisture_meter', 'moisture_level', 'neondata_virtual', 'raspberrypi', ">= to_timestamp(" + DATA_SHARE_TIME + ")")
            bert_query2 = build_query('Moisture Meter - moisture_meter', 'moisture_level', 'my_iot_virtual', 'raspberrypi', "< to_timestamp(" + DATA_SHARE_TIME + ")")
            cur_bert1.execute(bert_query1)
            cur_bert2.execute(bert_query2)
            bert_data1 = cur_bert1.fetchall()
            bert_data2 = cur_bert2.fetchall()
            bert_data = bert_data1 + bert_data2

        now = time.time()
        one_hour_ago = now - 3600
        one_week_ago = now - (7 * 24 * 3600)

        marc_last_hour_moisture = []
        marc_last_week_moisture = []
        marc_last_month_moisture = []

        bert_last_hour_moisture = []
        bert_last_week_moisture = []
        bert_last_month_moisture = []

        for row in marc_data:
            ts = row[0]
            moisture = float(row[1])
            if ts >= one_hour_ago:
                marc_last_hour_moisture.append(moisture)
            if ts >= one_week_ago:
                marc_last_week_moisture.append(moisture)
            marc_last_month_moisture.append(moisture)

        for row in bert_data:
            ts = row[0]
            moisture = float(row[1])
            if ts >= one_hour_ago:
                bert_last_hour_moisture.append(moisture)
            if ts >= one_week_ago:
                bert_last_week_moisture.append(moisture)
            bert_last_month_moisture.append(moisture)

        marc_avg_moisture_1hr = np.mean(np.array(marc_last_hour_moisture, dtype=float))
        marc_avg_moisture_1wk = np.mean(np.array(marc_last_week_moisture, dtype=float))
        marc_avg_moisture_1mo = np.mean(np.array(marc_last_month_moisture, dtype=float))

        bert_avg_moisture_1hr = np.mean(np.array(bert_last_hour_moisture, dtype=float))
        bert_avg_moisture_1wk = np.mean(np.array(bert_last_week_moisture, dtype=float))
        bert_avg_moisture_1mo = np.mean(np.array(bert_last_month_moisture, dtype=float))

        now = time.time()

    return (
        f"Marc's Smart Fridge Average Moisture:\n"
        f"1 hour (since {to_pst(one_hour_ago)}): {marc_avg_moisture_1hr}\n"
        f"1 week (since {to_pst(one_week_ago)}): {marc_avg_moisture_1wk}\n"
        f"1 month (since {to_pst(one_month_ago)}): {marc_avg_moisture_1mo}\n\n"
        f"Albert's Smart Fridge Average Moisture:\n"
        f"1 hour (since {to_pst(one_hour_ago)}): {bert_avg_moisture_1hr}\n"
        f"1 week (since {to_pst(one_week_ago)}): {bert_avg_moisture_1wk}\n"
        f"1 month (since {to_pst(one_month_ago)}): {bert_avg_moisture_1mo}"
    )

def query_electricity():
    with db_connect() as (bert, marc):
        cur_marc = marc.cursor()
        marc_data = fetch_electricity_readings(
            cur_marc,
            "neondata_virtual",
            MARC_ELECTRICITY_SENSORS,
            ">= NOW() - INTERVAL '24 hours'",
        )

        one_day_ago = time.time() - SECONDS_IN_DAY
        if float(DATA_SHARE_TIME) < one_day_ago:
            albert_data = fetch_electricity_readings(
                cur_marc,
                "neondata_virtual",
                ALBERT_ELECTRICITY_SENSORS,
                ">= NOW() - INTERVAL '24 hours'",
            )
        else:
            albert_shared_data = fetch_electricity_readings(
                cur_marc,
                "neondata_virtual",
                ALBERT_ELECTRICITY_SENSORS,
                ">= to_timestamp(" + DATA_SHARE_TIME + ")",
            )

            cur_bert = bert.cursor()
            albert_original_data = fetch_electricity_readings(
                cur_bert,
                "my_iot_virtual",
                ALBERT_ELECTRICITY_SENSORS,
                ">= NOW() - INTERVAL '24 hours'\n"
                "AND to_timestamp((payload->>'timestamp')::double precision) < to_timestamp("
                + DATA_SHARE_TIME
                + ")",
            )

            albert_data = albert_shared_data + albert_original_data

        marc_total = sum_electricity_usage(marc_data)
        albert_total = sum_electricity_usage(albert_data)

    difference = abs(marc_total - albert_total)

    if marc_total > albert_total:
        higher_usage = "Marc's house"
    elif albert_total > marc_total:
        higher_usage = "Albert's house"
    else:
        higher_usage = "Tie"

    return (
        "Electricity Usage Comparison (Past 24 Hours, Pacific Time)\n"
        f"Marc's house: {format_kwh(marc_total)} kWh\n"
        f"Albert's house: {format_kwh(albert_total)} kWh\n"
        f"Higher usage: {higher_usage}\n"
        f"Difference: {format_kwh(difference)} kWh\n\n"
        f"Marc sensors: {format_sensor_list(MARC_ELECTRICITY_SENSORS)}\n"
        f"Albert sensors: {format_sensor_list(ALBERT_ELECTRICITY_SENSORS)}"
    )

def query_water():
    #db stuff
    with db_connect() as (bert, marc):
        cur_marc = marc.cursor()
        marc_query = build_query('watercomsumptionsensor', 'water_consumption', 'neondata_virtual', 'my5thrasppi', ">= NOW() - INTERVAL '1 month'")
        cur_marc.execute(marc_query)
        marc_data = cur_marc.fetchall()

        seconds_in_month = 30 * 24 * 60 * 60
        one_month_ago = time.time() - seconds_in_month
        if int(DATA_SHARE_TIME) < one_month_ago:
            cur_bert = marc.cursor()
            bert_query = build_query('Water Consumption Meter', 'water_consumption', 'neondata_virtual', 'raspberrydish', ">= NOW() - INTERVAL '1 month'")
            cur_bert.execute(bert_query)
            bert_data = cur_bert.fetchall()
        else:
            cur_bert1 = marc.cursor()
            cur_bert2 = bert.cursor()
            bert_query1 = build_query('Water Consumption Meter', 'water_consumption', 'neondata_virtual', 'raspberrydish', ">= to_timestamp(" + DATA_SHARE_TIME + ")")
            bert_query2 = build_query('Water Consumption Meter', 'water_consumption', 'my_iot_virtual', 'raspberrydish', "< to_timestamp(" + DATA_SHARE_TIME + ")")
            cur_bert1.execute(bert_query1)
            cur_bert2.execute(bert_query2)
            bert_data1 = cur_bert1.fetchall()
            bert_data2 = cur_bert2.fetchall()
            bert_data = bert_data1 + bert_data2

        now = time.time()
        one_hour_ago = now - 3600
        one_week_ago = now - (7 * 24 * 3600)

        marc_last_hour_moisture = []
        marc_last_week_moisture = []
        marc_last_month_moisture = []

        bert_last_hour_moisture = []
        bert_last_week_moisture = []
        bert_last_month_moisture = []

        for row in marc_data:
            ts = row[0]
            moisture = float(row[1])
            if ts >= one_hour_ago:
                marc_last_hour_moisture.append(moisture)
            if ts >= one_week_ago:
                marc_last_week_moisture.append(moisture)
            marc_last_month_moisture.append(moisture)

        for row in bert_data:
            ts = row[0]
            moisture = float(row[1])
            if ts >= one_hour_ago:
                bert_last_hour_moisture.append(moisture)
            if ts >= one_week_ago:
                bert_last_week_moisture.append(moisture)
            bert_last_month_moisture.append(moisture)

        marc_avg_moisture_1hr = np.mean(np.array(marc_last_hour_moisture, dtype=float))
        marc_avg_moisture_1wk = np.mean(np.array(marc_last_week_moisture, dtype=float))
        marc_avg_moisture_1mo = np.mean(np.array(marc_last_month_moisture, dtype=float))

        bert_avg_moisture_1hr = np.mean(np.array(bert_last_hour_moisture, dtype=float))
        bert_avg_moisture_1wk = np.mean(np.array(bert_last_week_moisture, dtype=float))
        bert_avg_moisture_1mo = np.mean(np.array(bert_last_month_moisture, dtype=float))

        now = time.time()

        return (
            f"Marc's Smart Fridge Average Moisture:\n"
            f"1 hour (since {to_pst(one_hour_ago)}): {marc_avg_moisture_1hr}\n"
            f"1 week (since {to_pst(one_week_ago)}): {marc_avg_moisture_1wk}\n"
            f"1 month (since {to_pst(one_month_ago)}): {marc_avg_moisture_1mo}\n\n"
            f"Albert's Smart Fridge Average Moisture:\n"
            f"1 hour (since {to_pst(one_hour_ago)}): {bert_avg_moisture_1hr}\n"
            f"1 week (since {to_pst(one_week_ago)}): {bert_avg_moisture_1wk}\n"
            f"1 month (since {to_pst(one_month_ago)}): {bert_avg_moisture_1mo}"
        )


def query_select(user_choice):
    if user_choice == "MOISTURE_LEVEL":
        return query_moisture()
    elif user_choice == "WATER_CONSUMPTION":
        return query_water()
    elif user_choice == "ELECTRICITY_USAGE":
        return query_electricity()
    else:
        return "Invalid query."

def run_server():
    PORT = 1024
    with socket.socket() as s: # initialize socket
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind(('0.0.0.0', PORT)) # listen on all network interfaces and set port as 1024 (change to whatever port you have opened)
        s.listen(1) # set it to listen
        print(f"Server listening on port {PORT}...")

        # send commands
        conn, addr = s.accept() # get the connection and address
        with conn:
            command_list_json = json.dumps(command_list)
            conn.sendall(command_list_json.encode('utf-8'))

            while True:
                data = conn.recv(1024) # receive
                if not data: break # if theres no more data then stop

                client_message = data.decode() # decode the bytes to a string
                response = query_select(client_message) # run the query select function with the client's 1, 2, or 3

                conn.sendall(response.encode())

if __name__ == "__main__":
    run_server()
