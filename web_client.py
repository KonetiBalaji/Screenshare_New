#!/usr/bin/env python3
"""
Web-based Screen Share Client
Provides a user-friendly web interface for global screen sharing
"""

from flask import Flask, render_template, request, jsonify, Response, stream_template
from flask_socketio import SocketIO, emit, join_room, leave_room
import base64
import json
import threading
import time
import os
from datetime import datetime

# Optional imports with error handling
try:
    import cv2
    import numpy as np
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False
    print("[-] OpenCV not available. Image processing features disabled.")

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here'
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables
active_sessions = {}
session_clients = {}

class WebScreenShare:
    def __init__(self, session_id, host_username):
        self.session_id = session_id
        self.host_username = host_username
        self.viewers = set()
        self.is_active = True
        self.last_frame = None
        self.frame_lock = threading.Lock()
        
    def add_viewer(self, viewer_id):
        self.viewers.add(viewer_id)
        
    def remove_viewer(self, viewer_id):
        self.viewers.discard(viewer_id)
        
    def update_frame(self, frame_data):
        with self.frame_lock:
            self.last_frame = frame_data
            
    def get_frame(self):
        with self.frame_lock:
            return self.last_frame

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/host')
def host_page():
    return render_template('host.html')

@app.route('/viewer')
def viewer_page():
    return render_template('viewer.html')

@app.route('/test')
def test_page():
    return render_template('test_viewer.html')

@app.route('/debug')
def debug_page():
    """Debug page to show active sessions and connections"""
    debug_info = {
        'active_sessions': len(active_sessions),
        'sessions': []
    }
    
    for session_id, session in active_sessions.items():
        debug_info['sessions'].append({
            'id': session_id,
            'host_username': session.host_username,
            'viewers_count': len(session.viewers),
            'is_active': session.is_active,
            'has_last_frame': session.last_frame is not None
        })
    
    return jsonify(debug_info)

@app.route('/api/sessions', methods=['GET'])
def get_sessions():
    """Get list of active sessions"""
    try:
        sessions = []
        for session_id, session in active_sessions.items():
            if session.is_active:
                sessions.append({
                    'id': session_id,
                    'host': session.host_username,
                    'viewers': len(session.viewers),
                    'created_at': datetime.now().isoformat()
                })
        return jsonify(sessions)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>', methods=['POST'])
def create_session(session_id):
    """Create a new screen sharing session"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
            
        host_username = data.get('host_username', 'Unknown')
        
        if session_id in active_sessions:
            return jsonify({'error': 'Session already exists'}), 400
            
        session = WebScreenShare(session_id, host_username)
        active_sessions[session_id] = session
        
        return jsonify({
            'session_id': session_id,
            'status': 'created',
            'host_username': host_username
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/session/<session_id>', methods=['DELETE'])
def delete_session(session_id):
    """Delete a screen sharing session"""
    try:
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session.is_active = False
            
            # Notify all viewers
            for viewer_id in session.viewers:
                socketio.emit('session_ended', {'session_id': session_id}, room=viewer_id)
                
            del active_sessions[session_id]
            
        return jsonify({'status': 'deleted'})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('join_session')
def handle_join_session(data):
    """Handle client joining a session"""
    try:
        session_id = data.get('session_id')
        client_type = data.get('client_type')
        username = data.get('username', 'Anonymous')
        
        if not session_id:
            emit('error', {'message': 'Session ID required'})
            return
            
        if session_id not in active_sessions:
            emit('error', {'message': 'Session not found'})
            return
            
        session = active_sessions[session_id]
        
        if client_type == 'viewer':
            session.add_viewer(request.sid)
            join_room(session_id)
            emit('joined_session', {
                'session_id': session_id,
                'host_username': session.host_username
            })
            
            # Send current frame if available
            if session.last_frame:
                emit('frame_update', {'frame': session.last_frame})
                
        elif client_type == 'host':
            join_room(session_id)
            emit('joined_session', {
                'session_id': session_id,
                'status': 'host_ready'
            })
        else:
            emit('error', {'message': 'Invalid client type'})
    except Exception as e:
        emit('error', {'message': f'Error joining session: {str(e)}'})

@socketio.on('leave_session')
def handle_leave_session(data):
    """Handle client leaving a session"""
    try:
        session_id = data.get('session_id')
        client_type = data.get('client_type')
        
        if session_id in active_sessions:
            session = active_sessions[session_id]
            
            if client_type == 'viewer':
                session.remove_viewer(request.sid)
                leave_room(session_id)
            elif client_type == 'host':
                # End session when host leaves
                session.is_active = False
                for viewer_id in session.viewers:
                    socketio.emit('session_ended', {'session_id': session_id}, room=viewer_id)
                del active_sessions[session_id]
    except Exception as e:
        print(f"Error leaving session: {e}")

@socketio.on('frame_data')
def handle_frame_data(data):
    """Handle incoming frame data from host"""
    try:
        session_id = data.get('session_id')
        frame_data = data.get('frame')
        
        if not session_id or not frame_data:
            print(f"Invalid frame data: session_id={session_id}, frame_data={'present' if frame_data else 'missing'}")
            return
            
        if session_id in active_sessions:
            session = active_sessions[session_id]
            session.update_frame(frame_data)
            
            # Broadcast to all viewers in the session
            viewer_count = len(session.viewers)
            print(f"Broadcasting frame to {viewer_count} viewers in session {session_id}")
            
            # Send to each viewer individually to ensure delivery
            for viewer_id in session.viewers:
                socketio.emit('frame_update', {'frame': frame_data}, room=viewer_id)
        else:
            print(f"Session {session_id} not found for frame data")
    except Exception as e:
        print(f"Error handling frame data: {e}")
        import traceback
        traceback.print_exc()

@socketio.on('clipboard_data')
def handle_clipboard_data(data):
    """Handle clipboard synchronization"""
    try:
        session_id = data.get('session_id')
        clipboard_text = data.get('text')
        
        if session_id in active_sessions:
            # Broadcast clipboard to all clients in session
            socketio.emit('clipboard_update', {
                'text': clipboard_text,
                'timestamp': datetime.now().isoformat()
            }, room=session_id)
    except Exception as e:
        print(f"Error handling clipboard data: {e}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection"""
    try:
        # Remove from all sessions
        for session_id, session in active_sessions.items():
            if request.sid in session.viewers:
                session.remove_viewer(request.sid)
    except Exception as e:
        print(f"Error handling disconnect: {e}")

if __name__ == '__main__':
    # Create templates directory if it doesn't exist
    os.makedirs('templates', exist_ok=True)
    
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    import argparse
    
    parser = argparse.ArgumentParser(description='Web-based Screen Share Client')
    parser.add_argument('--https', action='store_true', help='Enable HTTPS (requires cert.pem and key.pem)')
    parser.add_argument('--port', type=int, default=5000, help='Port to run on (default: 5000)')
    parser.add_argument('--host', default='0.0.0.0', help='Host to bind to (default: 0.0.0.0)')
    
    args = parser.parse_args()
    
    if args.https:
        # Check for SSL certificates
        if not os.path.exists('cert.pem') or not os.path.exists('key.pem'):
            print("[-] HTTPS mode requires cert.pem and key.pem files")
            print("[!] Generating self-signed certificates for testing...")
            
            try:
                import subprocess
                subprocess.run([
                    'openssl', 'req', '-x509', '-newkey', 'rsa:4096', '-keyout', 'key.pem', 
                    '-out', 'cert.pem', '-days', '365', '-nodes', '-subj', '/CN=localhost'
                ], check=True)
                print("[+] Self-signed certificates generated")
            except (subprocess.CalledProcessError, FileNotFoundError):
                print("[-] Failed to generate certificates. OpenSSL not found.")
                print("[!] Running without HTTPS...")
                args.https = False
        
        if args.https:
            print(f"[+] Starting web client with HTTPS on https://localhost:{args.port}")
            socketio.run(app, host=args.host, port=args.port, debug=True, 
                        ssl_context=('cert.pem', 'key.pem'))
        else:
            print(f"[+] Starting web client on http://localhost:{args.port}")
            socketio.run(app, host=args.host, port=args.port, debug=True)
    else:
        print(f"[+] Starting web client on http://localhost:{args.port}")
        print("[!] Note: For screen capture to work properly, use HTTPS in production")
        print("[!] For testing, you may need to allow insecure screen capture in your browser")
        print("[!] Use --https flag to enable HTTPS mode")
        
        socketio.run(app, host=args.host, port=args.port, debug=True)
