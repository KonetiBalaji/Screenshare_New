#!/usr/bin/env python3
"""
Global Screen Share Relay Server
Handles multiple screen sharing sessions with authentication and encryption
"""

import socket
import ssl
import json
import hashlib
import hmac
import time
import threading
import sqlite3
import uuid
import sys
from datetime import datetime, timedelta
from typing import Dict, Set, Optional, Tuple
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('relay_server.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RelayServer:
    def __init__(self, host='0.0.0.0', port=8443, ssl_cert=None, ssl_key=None):
        self.host = host
        self.port = port
        self.ssl_cert = ssl_cert
        self.ssl_key = ssl_key
        
        # Session management
        self.sessions: Dict[str, Dict] = {}
        self.clients: Dict[str, socket.socket] = {}
        self.viewers: Dict[str, Set[socket.socket]] = {}
        
        # Locks for thread safety
        self.sessions_lock = threading.Lock()
        self.clients_lock = threading.Lock()
        self.viewers_lock = threading.Lock()
        
        # Initialize database
        self.init_database()
        
    def init_database(self):
        """Initialize SQLite database for user management"""
        self.db_conn = sqlite3.connect('relay_server.db', check_same_thread=False)
        self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                api_key TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        self.db_conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id TEXT PRIMARY KEY,
                host_username TEXT NOT NULL,
                session_name TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP,
                is_active BOOLEAN DEFAULT 1
            )
        ''')
        
        self.db_conn.commit()
        
        # Create default admin user if not exists
        self.create_user('admin', 'admin123', 'admin')
        
    def create_user(self, username: str, password: str, role: str = 'user') -> bool:
        """Create a new user account"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            api_key = str(uuid.uuid4())
            
            self.db_conn.execute(
                'INSERT OR IGNORE INTO users (username, password_hash, api_key) VALUES (?, ?, ?)',
                (username, password_hash, api_key)
            )
            self.db_conn.commit()
            logger.info(f"Created user: {username}")
            return True
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return False
            
    def authenticate_user(self, username: str, password: str) -> Optional[str]:
        """Authenticate user and return API key"""
        try:
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            cursor = self.db_conn.execute(
                'SELECT api_key FROM users WHERE username = ? AND password_hash = ? AND is_active = 1',
                (username, password_hash)
            )
            result = cursor.fetchone()
            
            if result:
                api_key = result[0]
                # Update last login
                self.db_conn.execute(
                    'UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE username = ?',
                    (username,)
                )
                self.db_conn.commit()
                logger.info(f"User authenticated: {username}")
                return api_key
            return None
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return None
            
    def create_session(self, host_username: str, session_name: str) -> str:
        """Create a new screen sharing session"""
        session_id = str(uuid.uuid4())
        
        with self.sessions_lock:
            self.sessions[session_id] = {
                'host_username': host_username,
                'session_name': session_name,
                'created_at': datetime.now(),
                'last_activity': datetime.now(),
                'is_active': True
            }
            
        # Store in database
        self.db_conn.execute(
            'INSERT INTO sessions (id, host_username, session_name) VALUES (?, ?, ?)',
            (session_id, host_username, session_name)
        )
        self.db_conn.commit()
        
        logger.info(f"Created session: {session_id} by {host_username}")
        print(f"\n[+] NEW SESSION CREATED: {session_id}")
        print(f"[+] Share this ID with viewers: {session_id}")
        print(f"[+] Active sessions: {len(self.sessions)}\n")
        return session_id
        
    def list_active_sessions(self):
        """List all active sessions"""
        with self.sessions_lock:
            if not self.sessions:
                print("\n[!] No active sessions")
                return
                
            print(f"\n[+] ACTIVE SESSIONS ({len(self.sessions)}):")
            print("=" * 60)
            for session_id, session_info in self.sessions.items():
                viewers_count = len(self.viewers.get(session_id, set()))
                print(f"Session ID: {session_id}")
                print(f"Host: {session_info['host_username']}")
                print(f"Name: {session_info['session_name']}")
                print(f"Viewers: {viewers_count}")
                print(f"Created: {session_info['created_at'].strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 40)
            print("=" * 60)
        
    def handle_client(self, client_socket: socket.socket, client_address: Tuple[str, int]):
        """Handle individual client connection"""
        logger.info(f"New connection from {client_address}")
        
        try:
            # Handle authentication
            auth_data = client_socket.recv(1024).decode('utf-8')
            auth = json.loads(auth_data)
            
            if auth['type'] == 'auth':
                api_key = self.authenticate_user(auth['username'], auth['password'])
                if not api_key:
                    client_socket.send(json.dumps({'status': 'auth_failed'}).encode())
                    return
                    
                client_socket.send(json.dumps({'status': 'auth_success', 'api_key': api_key}).encode())
                username = auth['username']
            else:
                client_socket.close()
                return
                
            # Handle different client types
            if auth.get('client_type') == 'host':
                self.handle_host_client(client_socket, username)
            elif auth.get('client_type') == 'viewer':
                self.handle_viewer_client(client_socket, username, auth.get('session_id'))
            else:
                client_socket.close()
                
        except Exception as e:
            logger.error(f"Client handling error: {e}")
            client_socket.close()
            
    def handle_host_client(self, client_socket: socket.socket, username: str):
        """Handle screen sharing host client"""
        try:
            # Create session
            session_id = self.create_session(username, f"Session by {username}")
            
            with self.clients_lock:
                self.clients[session_id] = client_socket
                
            with self.viewers_lock:
                self.viewers[session_id] = set()
                
            # Send session info
            client_socket.send(json.dumps({
                'type': 'session_created',
                'session_id': session_id
            }).encode())
            
            logger.info(f"Host client connected: {username} (Session: {session_id})")
            
            # Handle screen data relay
            self.relay_screen_data(session_id, client_socket)
            
        except Exception as e:
            logger.error(f"Host client error: {e}")
            client_socket.close()
            
    def handle_viewer_client(self, client_socket: socket.socket, username: str, session_id: str):
        """Handle screen viewing client"""
        try:
            if session_id not in self.sessions:
                client_socket.send(json.dumps({'status': 'session_not_found'}).encode())
                return
                
            with self.viewers_lock:
                self.viewers[session_id].add(client_socket)
                
            logger.info(f"Viewer connected: {username} to session {session_id}")
            
            # Handle viewer data (clipboard, etc.)
            self.handle_viewer_data(session_id, client_socket)
            
        except Exception as e:
            logger.error(f"Viewer client error: {e}")
            client_socket.close()
            
    def relay_screen_data(self, session_id: str, host_socket: socket.socket):
        """Relay screen data from host to viewers"""
        try:
            while True:
                # Receive data size
                size_data = host_socket.recv(4)
                if not size_data:
                    break
                    
                size = int.from_bytes(size_data, 'big')
                
                # Receive data
                data = b""
                while len(data) < size:
                    chunk = host_socket.recv(min(size - len(data), 4096))
                    if not chunk:
                        break
                    data += chunk
                    
                if not data:
                    break
                    
                # Relay to all viewers
                with self.viewers_lock:
                    viewers_to_remove = set()
                    for viewer_socket in self.viewers.get(session_id, set()):
                        try:
                            viewer_socket.send(size_data + data)
                        except:
                            viewers_to_remove.add(viewer_socket)
                            
                    # Remove disconnected viewers
                    for viewer_socket in viewers_to_remove:
                        self.viewers[session_id].discard(viewer_socket)
                        
        except Exception as e:
            logger.error(f"Screen data relay error: {e}")
        finally:
            self.cleanup_session(session_id)
            
    def handle_viewer_data(self, session_id: str, viewer_socket: socket.socket):
        """Handle data from viewer (clipboard, etc.)"""
        try:
            while True:
                data = viewer_socket.recv(4096)
                if not data:
                    break
                    
                # Relay to host
                with self.clients_lock:
                    host_socket = self.clients.get(session_id)
                    if host_socket:
                        try:
                            host_socket.send(data)
                        except:
                            break
                            
        except Exception as e:
            logger.error(f"Viewer data handling error: {e}")
        finally:
            with self.viewers_lock:
                if session_id in self.viewers:
                    self.viewers[session_id].discard(viewer_socket)
                    
    def cleanup_session(self, session_id: str):
        """Clean up session resources"""
        with self.sessions_lock:
            if session_id in self.sessions:
                self.sessions[session_id]['is_active'] = False
                
        with self.clients_lock:
            if session_id in self.clients:
                try:
                    self.clients[session_id].close()
                except:
                    pass
                del self.clients[session_id]
                
        with self.viewers_lock:
            if session_id in self.viewers:
                for viewer_socket in self.viewers[session_id]:
                    try:
                        viewer_socket.close()
                    except:
                        pass
                del self.viewers[session_id]
                
        logger.info(f"Session cleaned up: {session_id}")
        
    def start(self):
        """Start the relay server"""
        try:
            # Create server socket
            server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.host, self.port))
            server_socket.listen(100)
            
            # Wrap with SSL if certificates provided
            if self.ssl_cert and self.ssl_key:
                context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
                context.load_cert_chain(self.ssl_cert, self.ssl_key)
                server_socket = context.wrap_socket(server_socket, server_side=True)
                logger.info("SSL enabled")
                
            logger.info(f"Relay server started on {self.host}:{self.port}")
            
            while True:
                try:
                    client_socket, client_address = server_socket.accept()
                    client_thread = threading.Thread(
                        target=self.handle_client,
                        args=(client_socket, client_address)
                    )
                    client_thread.daemon = True
                    client_thread.start()
                except Exception as e:
                    logger.error(f"Accept error: {e}")
                    continue
                    
        except KeyboardInterrupt:
            logger.info("Shutting down relay server...")
        except Exception as e:
            logger.error(f"Server error: {e}")
        finally:
            server_socket.close()
            self.db_conn.close()

if __name__ == "__main__":
    # Create default SSL certificates for testing (in production, use proper certificates)
    import subprocess
    import os
    import argparse
    
    parser = argparse.ArgumentParser(description='Global Screen Share Server')
    parser.add_argument('--list-sessions', action='store_true', help='List active sessions and exit')
    args = parser.parse_args()
    
    # Initialize server
    server = RelayServer(port=8443, ssl_cert='server.crt', ssl_key='server.key')
    
    # List sessions if requested
    if args.list_sessions:
        server.list_active_sessions()
        sys.exit(0)
    
    # Check if SSL certificates exist
    if not os.path.exists('server.crt') or not os.path.exists('server.key'):
        logger.info("SSL certificates not found. Attempting to generate...")
        try:
            # Try to generate SSL certificates using OpenSSL
            subprocess.run([
                'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', 'server.key',
                '-out', 'server.crt', '-days', '365', '-nodes', '-subj', '/CN=localhost'
            ], check=True, capture_output=True)
            logger.info("SSL certificates generated successfully")
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("OpenSSL not found or failed to generate certificates.")
            logger.info("Starting server without SSL (insecure mode)")
            logger.info("For production, install OpenSSL or use proper SSL certificates")
            
            # Start server without SSL
            server = RelayServer(port=8443, ssl_cert=None, ssl_key=None)
            server.start()
            sys.exit(0)
    
    # Start server with SSL
    server.start()
