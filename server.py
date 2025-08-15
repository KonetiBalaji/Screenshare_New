import socket
import struct
import pickle
import sys
import os
import platform
import time
import threading
from typing import Optional, Tuple

# Platform-specific imports with fallbacks
try:
    from PIL import ImageGrab
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[-] PIL not available. Screen capture may not work.")

try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[-] OpenCV not available. Image processing may not work.")

try:
    import pyperclip
    PYPERCLIP_AVAILABLE = True
except ImportError:
    PYPERCLIP_AVAILABLE = False
    print("[-] Pyperclip not available. Clipboard features disabled.")

try:
    import keyboard
    KEYBOARD_AVAILABLE = True
except ImportError:
    KEYBOARD_AVAILABLE = False
    print("[-] Keyboard module not available. Hotkeys disabled.")

try:
    import pyautogui
    PYAUTOGUI_AVAILABLE = True
except ImportError:
    PYAUTOGUI_AVAILABLE = False
    print("[-] PyAutoGUI not available. Typing simulation disabled.")

# System tray imports
try:
    import pystray
    from PIL import Image
    SYSTEM_TRAY_AVAILABLE = True
except ImportError:
    SYSTEM_TRAY_AVAILABLE = False
    print("[-] System tray not available. Running in console mode.")

# Configuration
HOST = '0.0.0.0'
PORT = 9999
MAX_CONNECTIONS = 5
BUFFER_SIZE = 4096
SCREEN_CAPTURE_INTERVAL = 0.1  # seconds

# Global variables
is_typing = False
typing_lock = threading.Lock()
active_clients = set()
clients_lock = threading.Lock()
server_running = True
icon = None

def create_system_tray():
    """Create system tray icon and menu."""
    if not SYSTEM_TRAY_AVAILABLE:
        return None

    def on_exit(icon, item):
        """Handle exit menu item click."""
        global server_running
        server_running = False
        icon.stop()

    def on_status(icon, item):
        """Show server status."""
        with clients_lock:
            client_count = len(active_clients)
        icon.notify(f"Active clients: {client_count}", "Server Status")

    # Create a simple icon (you can replace this with your own icon)
    icon_image = Image.new('RGB', (64, 64), color='blue')
    
    # Create menu
    menu = (
        pystray.MenuItem('Status', on_status),
        pystray.MenuItem('Exit', on_exit)
    )
    
    # Create icon
    icon = pystray.Icon("screen_share", icon_image, "Screen Share Server", menu)
    return icon

def hide_console():
    """Hide console window on Windows."""
    if platform.system().lower() == 'windows':
        try:
            import win32gui
            import win32con
            console_window = win32gui.GetForegroundWindow()
            win32gui.ShowWindow(console_window, win32con.SW_HIDE)
        except ImportError:
            print("[-] win32gui not available. Console will remain visible.")

def check_permissions() -> Tuple[bool, str]:
    """Check if the script has necessary permissions."""
    system = platform.system().lower()
    issues = []
    
    if system == 'darwin':  # macOS
        if not os.path.exists('/Library/ScreenCapture'):
            issues.append("Screen Recording permission not granted")
        if not os.path.exists('/Library/Accessibility'):
            issues.append("Accessibility permission not granted")
    
    elif system == 'linux':
        if not os.environ.get('DISPLAY'):
            issues.append("No display server available")
    
    return len(issues) == 0, ", ".join(issues)

def capture_screen() -> Optional[np.ndarray]:
    """Capture screen with error handling and platform-specific fallbacks."""
    if not PIL_AVAILABLE or not CV2_AVAILABLE:
        return None
        
    try:
        img = ImageGrab.grab()
        frame = np.array(img)
        # Convert from RGB to BGR for OpenCV
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        return frame
    except Exception as e:
        print(f"[-] Screen capture error: {e}")
        return None

def stop_typing():
    """Stop the typing simulation."""
    global is_typing
    with typing_lock:
        is_typing = False
    print("[+] Typing stopped")

def type_clipboard_content():
    """Type clipboard content with error handling."""
    if not PYAUTOGUI_AVAILABLE or not PYPERCLIP_AVAILABLE:
        print("[-] Typing simulation not available")
        return
        
    global is_typing
    try:
        content = pyperclip.paste()
        if not content:
            return
            
        with typing_lock:
            is_typing = True
        
        for char in content:
            with typing_lock:
                if not is_typing:
                    break
            try:
                pyautogui.write(char)
                time.sleep(0.05)
            except Exception as e:
                print(f"[-] Typing error: {e}")
                break
    except Exception as e:
        print(f"[-] Clipboard error: {e}")

def handle_clipboard(conn: socket.socket) -> None:
    """Handle clipboard synchronization with error handling."""
    if not PYPERCLIP_AVAILABLE:
        return
        
    while True:
        try:
            # Receive size with timeout
            conn.settimeout(1.0)
            size_data = conn.recv(struct.calcsize(">L"))
            if not size_data:
                break
                
            size = struct.unpack(">L", size_data)[0]
            if size > 1024 * 1024:  # Limit clipboard size to 1MB
                print("[-] Clipboard data too large")
                continue
            
            # Receive data with timeout
            clipboard_data = b""
            while len(clipboard_data) < size:
                try:
                    chunk = conn.recv(min(size - len(clipboard_data), BUFFER_SIZE))
                    if not chunk:
                        break
                    clipboard_data += chunk
                except socket.timeout:
                    continue
                except Exception as e:
                    print(f"[-] Data receive error: {e}")
                    break
            
            if clipboard_data:
                try:
                    pyperclip.copy(clipboard_data.decode('utf-8'))
                except Exception as e:
                    print(f"[-] Clipboard copy error: {e}")
                    
        except socket.timeout:
            continue
        except Exception as e:
            print(f"[-] Clipboard handling error: {e}")
            break

def handle_client(conn: socket.socket, addr: Tuple[str, int]) -> None:
    """Handle individual client connection with error handling."""
    print(f"[+] New connection from {addr}")
    
    with clients_lock:
        active_clients.add(conn)
    
    # Start clipboard handling in a separate thread
    if PYPERCLIP_AVAILABLE:
        clipboard_thread = threading.Thread(target=handle_clipboard, args=(conn,))
        clipboard_thread.daemon = True
        clipboard_thread.start()
    
    try:
        while True:
            frame = capture_screen()
            if frame is None:
                time.sleep(SCREEN_CAPTURE_INTERVAL)
                continue
                
            try:
                # Compress the image using JPEG
                encoded, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 60])
                data = pickle.dumps(buffer)
                size = len(data)
                
                # Send size then data
                conn.sendall(struct.pack(">L", size) + data)
                time.sleep(SCREEN_CAPTURE_INTERVAL)
                
            except Exception as e:
                print(f"[-] Frame sending error: {e}")
                break
                
    except Exception as e:
        print(f"[-] Client {addr} error: {e}")
    finally:
        print(f"[-] Client {addr} disconnected")
        with clients_lock:
            active_clients.remove(conn)
        conn.close()

def setup_hotkeys() -> None:
    """Setup keyboard hotkeys with error handling."""
    if KEYBOARD_AVAILABLE:
        try:
            keyboard.add_hotkey('ctrl+space', type_clipboard_content)
            keyboard.add_hotkey('ctrl+m', stop_typing)
            print("[+] Hotkeys configured")
        except Exception as e:
            print(f"[-] Hotkey setup error: {e}")

def main() -> None:
    """Main server function with error handling."""
    global server_running, icon
    
    # Hide console if possible
    hide_console()
    
    # Create system tray icon
    if SYSTEM_TRAY_AVAILABLE:
        icon = create_system_tray()
        if icon:
            # Start system tray in a separate thread
            threading.Thread(target=icon.run, daemon=True).start()
    
    # Check permissions
    has_permissions, permission_issues = check_permissions()
    if not has_permissions:
        print(f"[-] Permission issues: {permission_issues}")
        print("[!] Some features may not work properly")
    
    # Setup hotkeys
    setup_hotkeys()
    
    # Create server socket
    try:
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_socket.bind((HOST, PORT))
        server_socket.listen(MAX_CONNECTIONS)
        print(f"[+] Server listening on {HOST}:{PORT}...")
        
        while server_running:
            try:
                server_socket.settimeout(1.0)  # Add timeout to check server_running
                conn, addr = server_socket.accept()
                client_thread = threading.Thread(target=handle_client, args=(conn, addr))
                client_thread.daemon = True
                client_thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                print(f"[-] Connection error: {e}")
                continue
                
    except KeyboardInterrupt:
        print("\n[+] Shutting down server...")
    except Exception as e:
        print(f"[-] Server error: {e}")
    finally:
        # Cleanup
        server_running = False
        with clients_lock:
            for client in active_clients:
                try:
                    client.close()
                except:
                    pass
        server_socket.close()
        if icon:
            icon.stop()

if __name__ == "__main__":
    main()