import socket
import threading
import time
import os
import hashlib
import json

CHUNK = 65536

def _get_free_port():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.bind(('', 0))
        return s.getsockname()[1]
    finally:
        s.close()

def _send_file_to_agent(agent_ip: str, port: int, file_path: str, upload_id: str):
    srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        srv.bind(('', port))
        srv.listen(1)
        srv.settimeout(60)
        conn, addr = srv.accept()
        try:
            conn.settimeout(30)
            sha = hashlib.sha256()
            size = os.path.getsize(file_path)
            with open(file_path, 'rb') as f:
                while True:
                    data = f.read(CHUNK)
                    if not data:
                        break
                    conn.sendall(data)
                    sha.update(data)
            # Close connection to signal end-of-stream; agent verifies size/hash separately
        finally:
            try:
                conn.close()
            except Exception:
                pass
    except Exception:
        pass
    finally:
        try:
            srv.close()
        except Exception:
            pass

def start_p2p_upload(agent_ip: str, file_path: str, upload_id: str) -> int:
    port = _get_free_port()
    t = threading.Thread(target=_send_file_to_agent, args=(agent_ip, port, file_path, upload_id), daemon=True)
    t.start()
    time.sleep(0.2)
    return port
