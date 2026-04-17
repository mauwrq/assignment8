import socket
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
    while True: # loop so i can input more stuff
        print("1. What is the average moisture inside our kitchen fridges in the past hours, week and month?\n2. What is the average water consumption per cycle across our smart dishwashers in the past hour, week and month?\n3. Which house consumed more electricity in the past 24 hours, and by how much?")
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
