import socket
PORT = 1024
s = socket.socket() # initialize socket
s.bind(('0.0.0.0', PORT)) # listen on all network interfaces and set port as 1024 (change to whatever port you have opened)
s.listen(1) # set it to listen
conn, addr = s.accept() # get the connection and address
while True:
    data = conn.recv(1024) # receive
    if not data: break # if theres no more data then stop
    print(data.decode()) # we get back bytes so we want to decode them into strings
    conn.send(data.upper()) # send back what they sent in all caps