import socket
import json
ip = input("IP: ")
try: # to return errors when port is not a number
    port = int(input("Port: "))
except:
    print("Error: Invalid Port. Connection failed.")
s = socket.socket() # initialize socket
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # using this so i can restart immediately
try: # fails if we cannot connect
    s.connect((ip, port)) # make a connection using ip and port input
    print("Connected established.")
    command_list_recv = s.recv(4096)
    command_list_json = command_list_recv.decode('utf-8')
    command_list = json.loads(command_list_json)
    print(command_list)
    while True: # loop so i can input more stuff
        msg = input("> ") # show input
        queries = {
            "1" : "MOISTURE_LEVEL",
            "2" : "WATER_CONSUMPTION",
            "3" : "ELECTRICITY_USAGE"
        }
        s.send(queries[msg].encode()) # send as bytes
        print(s.recv(1024).decode()) # decode bytes to text
except:
    print("Error: Invalid IP or Port. Connection failed.")
