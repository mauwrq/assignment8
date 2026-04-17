import socket
import psycopg2

bert_db = "postgresql://neondb_owner:npg_WHRq2Okh6nzw@ep-old-pond-akp4qnxs-pooler.c-3.us-west-2.aws.neon.tech/neondb?sslmode=require&channel_binding=require"
marc_db = "f"


def query_moisture():
    #db stuff
    # psycopg2.connect(bert_db) or psycopg2.connect(marc_db)?
    return "Moisture level is 50%."

def query_electricity():
    #db stuff
    return "Electricity usage is 200 kWh."

def query_water():
    #db stuff
    return "Water usage is 100 liters."

def query_select(user_choice):
    if user_choice == "moisture_level":
        return query_moisture()
    elif user_choice == "water_consumption":
        return query_water()
    elif user_choice == "electricity_usage":
        return query_electricity()
    else:
        return "Invalid query."

PORT = 1024
s = socket.socket() # initialize socket
s.bind(('0.0.0.0', PORT)) # listen on all network interfaces and set port as 1024 (change to whatever port you have opened)
s.listen(1) # set it to listen
print(f"Server listening on port {PORT}...")
conn, addr = s.accept() # get the connection and address
while True:
    data = conn.recv(1024) # receive
    if not data: break # if theres no more data then stop

    client_message = data.decode() # decode the bytes to a string
    response = query_select(client_message) # run the query select function with the client's 1, 2, or 3

    conn.send(response.encode())
    print(data.decode()) # we get back bytes so we want to decode them into strings
    conn.send(data.upper()) # send back what they sent in all caps