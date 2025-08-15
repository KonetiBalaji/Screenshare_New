#!/usr/bin/env python3
"""
Global Screen Share Client
Can work as either a host (sharing screen) or viewer (watching screen)
"""

import socket
import ssl
import json
import struct
import pickle
import cv2
import numpy as np
import threading
import time
import argparse
import sys
import os
from typing import Optional, Tuple

# Platform-specific imports
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[-] PIL not available. Screen capture may not work.")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("[-] Pyperclip not available. Clipboard features disabled.")

try:
    from screeninfo import get_monitors
    SCREENINFO_AVAILABLE = True
except ImportError:
    SCREENINFO_AVAILABLE = False
    print("[-] Screeninfo not available. Using default resolution.")

class GlobalScreenShareClient:
    def __init__(self, server_host: str, server_port: int = 8443, use_ssl: bool = True):
        self.server_host = server_host
        self.server_port = server_port
        self.use_ssl = use_ssl
        self.client_socket = None
        self.session_id = None
        self.is_host = False
        self.running = True
        
        # Get screen resolution
        if SCREENINFO_AVAILABLE:
            try:
                primary_monitor = get_monitors()[0]
                self.screen_width = primary_monitor.width
                self.screen_height = primary_monitor.height
            except:
                self.screen_width = 1920
                self.screen_height = 1080
        else:
            self.screen_width = 1920
            self.screen_height = 1080
            
    def connect_to_server(self, username: str, password: str, client_type: str, session_id: str = None) -> bool:
        """Connect to the relay server with authentication"""
        try:
            # Create socket
            self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            
            # Connect to server first (without SSL)
            self.client_socket.connect((self.server_host, self.server_port))
            
            # Wrap with SSL if needed
            if self.use_ssl:
                try:
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    context.verify_mode = ssl.CERT_NONE
                    self.client_socket = context.wrap_socket(self.client_socket, server_hostname=self.server_host)
                    print("[+] SSL connection established")
                except Exception as ssl_error:
                    print(f"[-] SSL connection failed: {ssl_error}")
                    print("[!] Trying without SSL...")
                    # Reconnect without SSL
                    self.client_socket.close()
                    self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self.client_socket.connect((self.server_host, self.server_port))
                    self.use_ssl = False
            
            # Send authentication
            auth_data = {
                'type': 'auth',
                'username': username,
                'password': password,
                'client_type': client_type
            }
            
            if session_id:
                auth_data['session_id'] = session_id
                
            self.client_socket.send(json.dumps(auth_data).encode())
            
            # Receive response
            response = self.client_socket.recv(1024).decode()
            response_data = json.loads(response)
            
            if response_data.get('status') == 'auth_success':
                print(f"[+] Successfully authenticated as {username}")
                self.is_host = (client_type == 'host')
                
                if self.is_host and 'session_id' in response_data:
                    self.session_id = response_data['session_id']
                    print(f"[+] Session created: {self.session_id}")
                    
                return True
            else:
                print(f"[-] Authentication failed: {response_data}")
                return False
                
        except Exception as e:
            print(f"[-] Connection error: {e}")
            return False
            
    def resize_to_fit_screen(self, img):
        """Resize image to fit screen while maintaining aspect ratio"""
        height, width = img.shape[:2]
        
        scale_width = self.screen_width / width
        scale_height = self.screen_height / height
        scale = min(scale_width, scale_height)
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        return cv2.resize(img, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
    def capture_screen(self) -> Optional[np.ndarray]:
        """Capture screen (host only)"""
        if not PIL_AVAILABLE:
            return None
            
        try:
            img = ImageGrab.grab()
            frame = np.array(img)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            return frame
        except Exception as e:
            print(f"[-] Screen capture error: {e}")
            return None
            
    def monitor_clipboard(self):
        """Monitor clipboard for changes (host only)"""
        if not PYPERCLIP_AVAILABLE:
            return
            
        last_clipboard = ""
        while self.running:
            try:
                current_clipboard = pyperclip.paste()
                if current_clipboard != last_clipboard:
                    data = current_clipboard.encode('utf-8')
                    size = len(data)
                    self.client_socket.sendall(struct.pack(">L", size))
                    self.client_socket.sendall(data)
                    last_clipboard = current_clipboard
                time.sleep(0.1)
            except Exception as e:
                print(f"[-] Clipboard error: {e}")
                break
                
    def run_as_host(self):
        """Run as screen sharing host"""
        print("[+] Starting as host...")
        
        # Start clipboard monitoring
        if PYPERCLIP_AVAILABLE:
            clipboard_thread = threading.Thread(target=self.monitor_clipboard)
            clipboard_thread.daemon = True
            clipboard_thread.start()
            
        try:
            while self.running:
                frame = self.capture_screen()
                if frame is None:
                    time.sleep(0.1)
                    continue
                    
                # Compress and send frame
                encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                data = pickle.dumps(buffer)
                size = len(data)
                
                self.client_socket.sendall(struct.pack(">L", size) + data)
                time.sleep(0.1)  # 10 FPS
                
        except Exception as e:
            print(f"[-] Host error: {e}")
        finally:
            self.running = False
            
    def run_as_viewer(self):
        """Run as screen viewer"""
        print("[+] Starting as viewer...")
        
        data = b""
        payload_size = struct.calcsize(">L")
        
        try:
            while self.running:
                # Receive message length
                while len(data) < payload_size:
                    chunk = self.client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                if len(data) < payload_size:
                    break
                    
                packed_msg_size = data[:payload_size]
                data = data[payload_size:]
                msg_size = struct.unpack(">L", packed_msg_size)[0]
                
                # Receive image data
                while len(data) < msg_size:
                    chunk = self.client_socket.recv(4096)
                    if not chunk:
                        break
                    data += chunk
                    
                if len(data) < msg_size:
                    break
                    
                frame_data = data[:msg_size]
                data = data[msg_size:]
                
                # Decode and display image
                frame = pickle.loads(frame_data)
                img = cv2.imdecode(frame, cv2.IMREAD_COLOR)
                resized_img = self.resize_to_fit_screen(img)
                
                cv2.namedWindow('Remote Screen', cv2.WINDOW_NORMAL)
                cv2.imshow('Remote Screen', resized_img)
                
                if cv2.waitKey(1) == ord('q'):
                    break
                    
        except Exception as e:
            print(f"[-] Viewer error: {e}")
        finally:
            self.running = False
            cv2.destroyAllWindows()
            
    def run(self, username: str, password: str, client_type: str, session_id: str = None):
        """Main run method"""
        if not self.connect_to_server(username, password, client_type, session_id):
            return
            
        try:
            if self.is_host:
                self.run_as_host()
            else:
                self.run_as_viewer()
        except KeyboardInterrupt:
            print("\n[+] Shutting down...")
        finally:
            if self.client_socket:
                self.client_socket.close()

def main():
    parser = argparse.ArgumentParser(description='Global Screen Share Client')
    parser.add_argument('--server', required=True, help='Relay server hostname/IP')
    parser.add_argument('--port', type=int, default=8443, help='Server port (default: 8443)')
    parser.add_argument('--username', required=True, help='Username for authentication')
    parser.add_argument('--password', required=True, help='Password for authentication')
    parser.add_argument('--mode', choices=['host', 'viewer'], required=True, help='Client mode')
    parser.add_argument('--session', help='Session ID (required for viewer mode)')
    parser.add_argument('--no-ssl', action='store_true', help='Disable SSL (not recommended)')
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.mode == 'viewer' and not args.session:
        print("[-] Session ID is required for viewer mode")
        sys.exit(1)
    
    # Auto-detect SSL based on port (common convention)
    use_ssl = not args.no_ssl
    if args.port == 8443 and not args.no_ssl:
        use_ssl = True
    elif args.port == 9999:  # Original port, typically no SSL
        use_ssl = False
        print("[!] Using port 9999, assuming no SSL. Use --no-ssl flag to confirm.")
    
    # If --no-ssl is specified, use port 8443 but without SSL
    if args.no_ssl and args.port == 8443:
        print("[!] Using --no-ssl flag, connecting to port 8443 without SSL")
    
    # Create and run client
    client = GlobalScreenShareClient(
        server_host=args.server,
        server_port=args.port,
        use_ssl=use_ssl
    )
    
    client.run(args.username, args.password, args.mode, args.session)

if __name__ == "__main__":
    main()
