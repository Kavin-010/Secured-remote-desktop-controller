import socket
import pickle
import struct
import cv2
import numpy as np
import pyautogui
import threading
import time

# Server configuration
HOST = "0.0.0.0"
PORT = 5555
PASSWORD = "secure123"
SECRET_KEY = b"my_secret_key"

def xor_encrypt_decrypt(data, key):
    key = key * (len(data) // len(key)) + key[:len(data) % len(key)]
    return bytes([data[i] ^ key[i] for i in range(len(data))])

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind((HOST, PORT))
server.listen(1)

print("🟢 Server listening for connections...")
conn, addr = server.accept()
print(f"🔗 Client connected from {addr}")

# -------- Authentication --------
encrypted_pass = conn.recv(1024)
password = xor_encrypt_decrypt(encrypted_pass, SECRET_KEY).decode()

if password != PASSWORD:
    conn.sendall(xor_encrypt_decrypt(b"AUTH_FAILED", SECRET_KEY))
    conn.close()
    exit()

conn.sendall(xor_encrypt_decrypt(b"AUTH_SUCCESS", SECRET_KEY))
print("✅ Client authenticated")

# -------- Screen Streaming --------
def stream_screen():
    try:
        while True:
            screenshot = pyautogui.screenshot()
            frame = np.array(screenshot)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

            data = pickle.dumps(frame)
            encrypted = xor_encrypt_decrypt(data, SECRET_KEY)

            size = struct.pack("L", len(encrypted))
            conn.sendall(size + encrypted)

            time.sleep(0.03)  # ~30 FPS
    except:
        print("❌ Client disconnected")

# -------- Input Control --------
def receive_controls():
    try:
        while True:
            data = conn.recv(4096)
            if not data:
                break

            event = pickle.loads(data)

            if event["type"] == "MOUSE_MOVE":
                pyautogui.moveTo(event["x"], event["y"])

            elif event["type"] == "MOUSE_CLICK":
                if event["action"] == "down":
                    pyautogui.mouseDown()
                else:
                    pyautogui.mouseUp()

            elif event["type"] == "KEY_PRESS":
                pyautogui.press(event["key"])
    except:
        pass

# Run both threads
threading.Thread(target=stream_screen, daemon=True).start()
threading.Thread(target=receive_controls, daemon=True).start()

# Keep server alive
while True:
    time.sleep(1)
