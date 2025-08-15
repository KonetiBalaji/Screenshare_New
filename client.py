# client.py
import socket
import struct
import pickle
import cv2
import numpy as np
from screeninfo import get_monitors
import pyperclip
import threading
import time

# Get primary monitor resolution
primary_monitor = get_monitors()[0]
SCREEN_WIDTH = primary_monitor.width
SCREEN_HEIGHT = primary_monitor.height

SERVER_IP = '192.168.1.139'  # Replace with target IP
PORT = 9999

def resize_to_fit_screen(img):
    # Get image dimensions
    height, width = img.shape[:2]
    
    # Calculate scaling factor to fit screen while maintaining aspect ratio
    scale_width = SCREEN_WIDTH / width
    scale_height = SCREEN_HEIGHT / height
    scale = min(scale_width, scale_height)
    
    # Calculate new dimensions
    new_width = int(width * scale)
    new_height = int(height * scale)
    
    # Resize image
    return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)

def monitor_clipboard(client_socket):
    last_clipboard = ""
    while True:
        try:
            current_clipboard = pyperclip.paste()
            if current_clipboard != last_clipboard:
                # Send clipboard data size
                data = current_clipboard.encode('utf-8')
                size = len(data)
                client_socket.sendall(struct.pack(">L", size))
                # Send clipboard data
                client_socket.sendall(data)
                last_clipboard = current_clipboard
            time.sleep(0.1)  # Small delay to prevent high CPU usage
        except Exception as e:
            print("[-] Clipboard error:", e)
            break

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((SERVER_IP, PORT))

# Start clipboard monitoring in a separate thread
clipboard_thread = threading.Thread(target=monitor_clipboard, args=(client_socket,))
clipboard_thread.daemon = True
clipboard_thread.start()

data = b""
payload_size = struct.calcsize(">L")

try:
    while True:
        # Receive message length
        while len(data) < payload_size:
            data += client_socket.recv(4096)
        packed_msg_size = data[:payload_size]
        data = data[payload_size:]
        msg_size = struct.unpack(">L", packed_msg_size)[0]

        # Receive image data
        while len(data) < msg_size:
            data += client_socket.recv(4096)
        frame_data = data[:msg_size]
        data = data[msg_size:]

        # Decode image and resize
        frame = pickle.loads(frame_data)
        img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
        resized_img = resize_to_fit_screen(img)
        
        # Create a window that can be resized
        cv2.namedWindow('Remote Screen', cv2.WINDOW_NORMAL)
        cv2.imshow('Remote Screen', resized_img)
        
        if cv2.waitKey(1) == ord('q'):
            break

except Exception as e:
    print("[-] Error:", e)

finally:
    client_socket.close()
    cv2.destroyAllWindows()
