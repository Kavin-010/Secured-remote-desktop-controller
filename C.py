import socket
import pickle
import struct
import cv2
import numpy as np
import tkinter as tk
from PIL import Image, ImageTk
from pynput.mouse import Listener as MouseListener
from pynput.keyboard import Listener as KeyboardListener
import threading

# Server Details
SERVER_IP = "192.168.176.3"
PORT = 5555
PASSWORD = "secure123"
SECRET_KEY = b"my_secret_key"

def xor_encrypt_decrypt(data, key):
    key = key * (len(data) // len(key)) + key[:len(data) % len(key)]
    return bytes([data[i] ^ key[i] for i in range(len(data))])

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect((SERVER_IP, PORT))
print("Connected to server")

client.sendall(xor_encrypt_decrypt(PASSWORD.encode(), SECRET_KEY))

encrypted_response = client.recv(1024)
auth_response = xor_encrypt_decrypt(encrypted_response, SECRET_KEY).decode()

if auth_response != "AUTH_SUCCESS":
    print("Authentication failed. Exiting...")
    client.close()
    exit()

print("Authentication successful!")

root = tk.Tk()
root.title("Remote Desktop")

# Get screen resolution
screen_width = root.winfo_screenwidth()
screen_height = root.winfo_screenheight()

# Make window fullscreen
root.geometry(f"{screen_width}x{screen_height}")
root.attributes('-fullscreen', True)  # Fullscreen mode

label = tk.Label(root)
label.pack(fill=tk.BOTH, expand=True)

data = b""
payload_size = struct.calcsize("L")

def receive_frame():
    global data
    try:
        while len(data) < payload_size:
            packet = client.recv(4096)
            if not packet:
                raise ConnectionError("Disconnected from server")
            data += packet

        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack("L", packed_msg_size)[0]

        while len(data) < msg_size:
            packet = client.recv(4096)
            if not packet:
                raise ConnectionError("Disconnected from server")
            data += packet

        encrypted_frame_data = data[:msg_size]
        data = data[msg_size:]

        frame_data = xor_encrypt_decrypt(encrypted_frame_data, SECRET_KEY)
        frame = pickle.loads(frame_data)
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # Resize the frame to match screen size
        img = Image.fromarray(frame)
        img = img.resize((screen_width, screen_height))
        img_tk = ImageTk.PhotoImage(img)

        label.config(image=img_tk)
        label.image = img_tk

        root.after(33, receive_frame)  # ~30 FPS

    except ConnectionError:
        print("Connection lost. Closing client...")
        client.close()
        root.quit()

receive_frame()

def send_control_data(data):
    try:
        client.sendall(pickle.dumps(data))
    except:
        pass

def on_move(x, y):
    send_control_data({"type": "MOUSE_MOVE", "x": x, "y": y})

def on_click(x, y, button, pressed):
    if button.name == "left":
        send_control_data({"type": "MOUSE_CLICK", "action": "down" if pressed else "up"})

def on_press(key):
    try:
        key_value = key.char if hasattr(key, 'char') else str(key)
        send_control_data({"type": "KEY_PRESS", "key": key_value})
    except AttributeError:
        pass

mouse_listener = MouseListener(on_move=on_move, on_click=on_click)
keyboard_listener = KeyboardListener(on_press=on_press)

# Run mouse and keyboard listeners in separate threads
threading.Thread(target=mouse_listener.start, daemon=True).start()
threading.Thread(target=keyboard_listener.start, daemon=True).start()

# Exit fullscreen on pressing 'Esc'
def exit_fullscreen(event):
    root.attributes('-fullscreen', False)

root.bind("<Escape>", exit_fullscreen)

root.mainloop()

mouse_listener.stop()
keyboard_listener.stop()
