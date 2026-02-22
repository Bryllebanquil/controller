#!/usr/bin/env python3
"""
Diagnostic script to check PC1 cursor flicker causes.
Run while streaming is active to see real-time CPU usage.
"""

import psutil
import time
import threading
import os

def monitor_threads():
    """Monitor thread CPU usage and priorities."""
    try:
        current_process = psutil.Process(os.getpid())
        
        print("\n" + "="*80)
        print("PC1 CURSOR FLICKER DIAGNOSTIC")
        print("="*80)
        print(f"Process ID: {current_process.pid}")
        print(f"Process Name: {current_process.name()}")
        print()
        
        while True:
            try:
                # Get process CPU usage
                cpu_percent = current_process.cpu_percent(interval=0.1)
                memory_info = current_process.memory_info()
                num_threads = current_process.num_threads()
                
                print(f"\n[{time.strftime('%H:%M:%S')}] CPU Usage: {cpu_percent}% | Memory: {memory_info.rss / 1024 / 1024:.1f} MB | Threads: {num_threads}")
                
                # Check for high CPU threads
                print("\nThread Details (Top 5 CPU consumers):")
                threads_info = []
                
                try:
                    for thread in threading.enumerate():
                        if hasattr(thread, '_target'):
                            name = thread.name
                            is_daemon = thread.daemon
                            threads_info.append((name, is_daemon))
                except Exception:
                    pass
                
                if threads_info:
                    for i, (name, is_daemon) in enumerate(sorted(threads_info)[:5], 1):
                        daemon_str = "[DAEMON]" if is_daemon else "[USER  ]"
                        print(f"  {i}. {daemon_str} {name}")
                
                # Check if streaming threads are running
                stream_threads = [t for t in threading.enumerate() if 'screen' in t.name.lower() or 'capture' in t.name.lower() or 'encode' in t.name.lower()]
                if stream_threads:
                    print(f"\nStreaming Threads Found: {len(stream_threads)}")
                    for t in stream_threads:
                        print(f"  - {t.name} (alive: {t.is_alive()})")
                
                # Get system CPU usage
                system_cpu = psutil.cpu_percent(interval=0.1)
                print(f"\nSystem CPU Usage: {system_cpu}%")
                
                print("\n" + "-"*80)
                
                time.sleep(2)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(1)
    
    except Exception as e:
        print(f"Fatal error: {e}")

if __name__ == '__main__':
    try:
        print("Starting PC1 Cursor Flicker Diagnostic...")
        print("This will monitor CPU usage and thread info in real-time.")
        print("Press Ctrl+C to stop.\n")
        monitor_threads()
    except KeyboardInterrupt:
        print("\n\nDiagnostic stopped.")
