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
        msg = input("> ") # show input
        s.send(msg.encode()) # send as bytes
        print(s.recv(1024).decode()) # decode bytes to text
except:
    print("Error: Invalid IP or Port. Connection failed.")