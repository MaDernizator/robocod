import socket
HOST="192.168.1.42"; PORT=1883
with socket.create_connection((HOST, PORT), timeout=5) as s:
    print("MQTT TCP ok")