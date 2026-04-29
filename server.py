import socket
import psycopg2
import json
import os
from dotenv import load_dotenv
from contextlib import contextmanager
import numpy as np
import time

load_dotenv()
MARC_DB = os.getenv("MARC_DB")
BERT_DB = os.getenv("BERT_DB")

command_list = [
    {"code" : "MOISTURE_LEVEL", "display" : "What is the average moisture inside our kitchen fridges in the past hours, week and month?"},
    {"code" : "WATER_CONSUMPTION", "display" : "What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?"},
    {"code" : "ELECTRICITY_USAGE", "display" : "Which house consumed more electricity in the past 24 hours, and by how much?"}
]

@contextmanager
def db_connect():
    # conn_bert = None
    conn_marc = None
    try:
        # conn_bert = psycopg2.connect(BERT_DB)
        conn_marc = psycopg2.connect(MARC_DB)
        # yield conn_bert, conn_marc
        yield conn_marc
    finally:
        # if conn_bert: conn_bert.close()
        if conn_marc: conn_marc.close()

def query_moisture():
    #db stuff
    # with db_connect() as (bert, marc):
    with db_connect() as marc:
        # cur_bert = bert.cursor()
        cur_marc = marc.cursor()
        marc_query = f"""SELECT 
(payload->>'timestamp')::double precision AS epoch_time,
payload->>'Moisture Meter - mymoisturemeter' AS moisture_level
FROM neondata_virtual
WHERE payload->>'board_name' = 'my3rdrasppi'
AND to_timestamp((payload->>'timestamp')::double precision) >= NOW() - INTERVAL '1 month'
AND payload->>'Moisture Meter - mymoisturemeter' IS NOT NULL
ORDER BY epoch_time DESC;"""
        cur_marc.execute(marc_query)
        marc_data = cur_marc.fetchall()

        now = time.time()
        one_hour_ago = now - 3600
        one_week_ago = now - (7 * 24 * 3600)
        
        marc_last_hour_moisture = []
        marc_last_week_moisture = []
        marc_last_month_moisture = []
        
        for row in marc_data:
            ts = row[0]
            moisture = float(row[1])
            if ts >= one_hour_ago:
                marc_last_hour_moisture.append(moisture)
            if ts >= one_week_ago:
                marc_last_week_moisture.append(moisture)
            marc_last_month_moisture.append(moisture)
        
        marc_avg_moisture_1hr = np.mean(np.array(marc_last_hour_moisture, dtype=float))
        marc_avg_moisture_1wk = np.mean(np.array(marc_last_week_moisture, dtype=float))
        marc_avg_moisture_1mo = np.mean(np.array(marc_last_month_moisture, dtype=float))

    # psycopg2.connect(bert_db) or psycopg2.connect(marc_db)?
        return f"Marc's Smart Fridge Average Moisture:\n1 hour: {marc_avg_moisture_1hr}\n1 week: {marc_avg_moisture_1wk}\n1 month: {marc_avg_moisture_1mo}"

def query_electricity():
    #db stuff
    return "Electricity usage is 200 kWh."

def query_water():
    #db stuff
    return "Water usage is 100 liters."

def query_select(user_choice):
    if user_choice == "MOISTURE_LEVEL":
        return query_moisture()
    elif user_choice == "WATER_CONSUMPTION":
        return query_water()
    elif user_choice == "ELECTRICITY_USAGE":
        return query_electricity()
    else:
        return "Invalid query."

PORT = 1024
s = socket.socket() # initialize socket
s.bind(('0.0.0.0', PORT)) # listen on all network interfaces and set port as 1024 (change to whatever port you have opened)
s.listen(1) # set it to listen
print(f"Server listening on port {PORT}...")

# send commands
conn, addr = s.accept() # get the connection and address
command_list_json = json.dumps(command_list)
conn.send(command_list_json.encode('utf-8'))

while True:
    data = conn.recv(1024) # receive
    if not data: break # if theres no more data then stop

    client_message = data.decode() # decode the bytes to a string
    response = query_select(client_message) # run the query select function with the client's 1, 2, or 3

    conn.send(response.encode())