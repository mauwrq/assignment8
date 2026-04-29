import socket
import json

def build_command_menu(command_list):
    command_menu = ""
    for i, command in enumerate(command_list):
        command_menu += f"{i + 1}. {command['display']}\n"
    return command_menu.strip()

ip = input("IP: ")
try: # to return errors when port is not a number
    port = int(input("Port: "))
except:
    print("Error: Invalid Port. Connection failed.")
s = socket.socket() # initialize socket
s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) # using this so i can restart immediately

# connection
try: # fails if we cannot connect
    s.connect((ip, port)) # make a connection using ip and port input
    print("Connected established.")

    # menu stuff
    command_list_recv = s.recv(4096)
    command_list_json = command_list_recv.decode('utf-8')
    command_list = json.loads(command_list_json)
    command_menu = build_command_menu(command_list)

    while True: # loop so i can input more stuff
        print()
        print(command_menu)
        choice = input("> ") # show input
        
        # validation
        if choice.isdigit() and 0 < int(choice) <= len(command_list):
            s.send(command_list[int(choice) - 1]['code'].encode()) # send as bytes
            print(s.recv(1024).decode()) # decode bytes to text
        else:
            print(f"Invalid query. Please enter a number between 1 and {len(command_list)}.")
            
except Exception as e:
    print(f"Error: {e}")
