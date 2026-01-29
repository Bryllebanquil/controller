"""
Comprehensive performance monitoring and latency tracking system
Provides real-time metrics and historical data analysis
"""

import time
import json
import statistics
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from collections import defaultdict, deque
import threading
import asyncio

@dataclass
class LatencyMetric:
    """Single latency measurement"""
    timestamp: float
    command_id: str
    agent_id: str
    command_type: str
    latency_ms: float
    success: bool
    error_message: Optional[str] = None

@dataclass
class ConnectionMetric:
    """Connection quality metric"""
    timestamp: float
    agent_id: str
    connection_time_ms: float
    disconnects: int
    reconnects: int
    uptime_percentage: float

class PerformanceMonitor:
    """High-performance monitoring system with minimal overhead"""
    
    def __init__(self, max_latency_samples: int = 10000, max_connection_samples: int = 1000):
        self.max_latency_samples = max_latency_samples
        self.max_connection_samples = max_connection_samples
        
        # Thread-safe data structures
        self.latency_samples: deque = deque(maxlen=max_latency_samples)
        self.connection_samples: deque = deque(maxlen=max_connection_samples)
        self.command_stats: Dict[str, Dict] = defaultdict(lambda: {
            'count': 0,
            'success_count': 0,
            'total_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0,
            'errors': []
        })
        
        self.agent_stats: Dict[str, Dict] = defaultdict(lambda: {
            'first_seen': None,
            'last_seen': None,
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'avg_latency': 0,
            'connection_drops': 0
        })
        
        # Real-time metrics
        self.current_metrics = {
            'commands_per_second': 0,
            'responses_per_second': 0,
            'active_connections': 0,
            'error_rate': 0,
            'p50_latency': 0,
            'p95_latency': 0,
            'p99_latency': 0
        }
        
        # Thread safety
        self.lock = threading.Lock()
        self.running = False
        self.metrics_thread = None
        
        # Time windows for analysis (in seconds)
        self.time_windows = {
            '1m': 60,
            '5m': 300,
            '15m': 900,
            '1h': 3600,
            '24h': 86400
        }
    
    def start(self):
        """Start background metrics calculation"""
        if self.running:
            return
        
        self.running = True
        self.metrics_thread = threading.Thread(target=self._calculate_metrics_loop, daemon=True)
        self.metrics_thread.start()
        print("🚀 Performance monitor started")
    
    def stop(self):
        """Stop performance monitoring"""
        self.running = False
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        print("👋 Performance monitor stopped")
    
    def record_latency(self, command_id: str, agent_id: str, command_type: str, 
                      latency_ms: float, success: bool = True, error_message: Optional[str] = None):
        """Record a latency measurement with minimal overhead"""
        metric = LatencyMetric(
            timestamp=time.time(),
            command_id=command_id,
            agent_id=agent_id,
            command_type=command_type,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        
        with self.lock:
            self.latency_samples.append(metric)
            
            # Update command statistics
            stats = self.command_stats[command_type]
            stats['count'] += 1
            stats['total_latency'] += latency_ms
            stats['min_latency'] = min(stats['min_latency'], latency_ms)
            stats['max_latency'] = max(stats['max_latency'], latency_ms)
            
            if success:
                stats['success_count'] += 1
            else:
                if error_message:
                    stats['errors'].append({
                        'timestamp': time.time(),
                        'message': error_message
                    })
                    # Keep only recent errors
                    if len(stats['errors']) > 100:
                        stats['errors'] = stats['errors'][-100:]
            
            # Update agent statistics
            agent_stats = self.agent_stats[agent_id]
            if agent_stats['first_seen'] is None:
                agent_stats['first_seen'] = time.time()
            agent_stats['last_seen'] = time.time()
            agent_stats['total_commands'] += 1
            
            if success:
                agent_stats['successful_commands'] += 1
            else:
                agent_stats['failed_commands'] += 1
            
            # Calculate running average for agent
            if agent_stats['avg_latency'] == 0:
                agent_stats['avg_latency'] = latency_ms
            else:
                # Exponential moving average
                alpha = 0.1
                agent_stats['avg_latency'] = (
                    agent_stats['avg_latency'] * (1 - alpha) + 
                    latency_ms * alpha
                )
    
    def record_connection_event(self, agent_id: str, connection_time_ms: float, 
                               disconnects: int = 0, reconnects: int = 0, 
                               uptime_percentage: float = 100.0):
        """Record connection quality metrics"""
        metric = ConnectionMetric(
            timestamp=time.time(),
            agent_id=agent_id,
            connection_time_ms=connection_time_ms,
            disconnects=disconnects,
            reconnects=reconnects,
            uptime_percentage=uptime_percentage
        )
        
        with self.lock:
            self.connection_samples.append(metric)
            
            # Update agent connection drops
            if disconnects > 0:
                self.agent_stats[agent_id]['connection_drops'] += disconnects
    
    def _calculate_metrics_loop(self):
        """Background thread for calculating real-time metrics"""
        last_calculation = time.time()
        
        while self.running:
            try:
                current_time = time.time()
                
                # Calculate metrics every 5 seconds
                if current_time - last_calculation >= 5:
                    self._calculate_realtime_metrics()
                    last_calculation = current_time
                
                time.sleep(1)
                
            except Exception as e:
                print(f"Error in metrics calculation: {e}")
                time.sleep(5)
    
    def _calculate_realtime_metrics(self):
        """Calculate real-time performance metrics"""
        with self.lock:
            if not self.latency_samples:
                return
            
            current_time = time.time()
            recent_samples = [
                sample for sample in self.latency_samples 
                if current_time - sample.timestamp <= 60  # Last minute
            ]
            
            if not recent_samples:
                return
            
            # Calculate rates
            self.current_metrics['commands_per_second'] = len(recent_samples) / 60
            
            # Calculate latency percentiles
            latencies = [sample.latency_ms for sample in recent_samples]
            latencies.sort()
            
            n = len(latencies)
            self.current_metrics['p50_latency'] = latencies[int(n * 0.5)]
            self.current_metrics['p95_latency'] = latencies[int(n * 0.95)]
            self.current_metrics['p99_latency'] = latencies[int(n * 0.99)]
            
            # Calculate error rate
            errors = sum(1 for sample in recent_samples if not sample.success)
            self.current_metrics['error_rate'] = (errors / len(recent_samples)) * 100
    
    def get_current_metrics(self) -> Dict[str, Any]:
        """Get current real-time metrics"""
        with self.lock:
            return self.current_metrics.copy()
    
    def get_command_statistics(self, command_type: Optional[str] = None) -> Dict[str, Any]:
        """Get detailed command statistics"""
        with self.lock:
            if command_type:
                return self._calculate_command_stats(command_type)
            else:
                return {
                    cmd_type: self._calculate_command_stats(cmd_type)
                    for cmd_type in self.command_stats.keys()
                }
    
    def _calculate_command_stats(self, command_type: str) -> Dict[str, Any]:
        """Calculate statistics for a specific command type"""
        stats = self.command_stats[command_type]
        
        if stats['count'] == 0:
            return {
                'command_type': command_type,
                'total_count': 0,
                'success_rate': 0,
                'avg_latency': 0,
                'min_latency': 0,
                'max_latency': 0,
                'recent_errors': []
            }
        
        return {
            'command_type': command_type,
            'total_count': stats['count'],
            'success_rate': (stats['success_count'] / stats['count']) * 100,
            'avg_latency': stats['total_latency'] / stats['count'],
            'min_latency': stats['min_latency'] if stats['min_latency'] != float('inf') else 0,
            'max_latency': stats['max_latency'],
            'recent_errors': stats['errors'][-10:]  # Last 10 errors
        }
    
    def get_agent_statistics(self, agent_id: Optional[str] = None) -> Dict[str, Any]:
        """Get agent performance statistics"""
        with self.lock:
            if agent_id:
                return self._calculate_agent_stats(agent_id)
            else:
                return {
                    agent_id: self._calculate_agent_stats(agent_id)
                    for agent_id in self.agent_stats.keys()
                }
    
    def _calculate_agent_stats(self, agent_id: str) -> Dict[str, Any]:
        """Calculate statistics for a specific agent"""
        stats = self.agent_stats[agent_id]
        
        if stats['total_commands'] == 0:
            success_rate = 0
        else:
            success_rate = (stats['successful_commands'] / stats['total_commands']) * 100
        
        uptime_hours = 0
        if stats['first_seen']:
            uptime_hours = (time.time() - stats['first_seen']) / 3600
        
        return {
            'agent_id': agent_id,
            'first_seen': datetime.fromtimestamp(stats['first_seen']).isoformat() if stats['first_seen'] else None,
            'last_seen': datetime.fromtimestamp(stats['last_seen']).isoformat() if stats['last_seen'] else None,
            'uptime_hours': uptime_hours,
            'total_commands': stats['total_commands'],
            'successful_commands': stats['successful_commands'],
            'failed_commands': stats['failed_commands'],
            'success_rate': success_rate,
            'avg_latency': stats['avg_latency'],
            'connection_drops': stats['connection_drops']
        }
    
    def get_latency_percentiles(self, window: str = '5m') -> Dict[str, float]:
        """Get latency percentiles for a specific time window"""
        if window not in self.time_windows:
            raise ValueError(f"Invalid window. Available: {list(self.time_windows.keys())}")
        
        with self.lock:
            current_time = time.time()
            window_seconds = self.time_windows[window]
            
            samples = [
                sample for sample in self.latency_samples
                if current_time - sample.timestamp <= window_seconds
            ]
            
            if not samples:
                return {'p50': 0, 'p90': 0, 'p95': 0, 'p99': 0, 'count': 0}
            
            latencies = [sample.latency_ms for sample in samples]
            latencies.sort()
            n = len(latencies)
            
            return {
                'p50': latencies[int(n * 0.5)],
                'p90': latencies[int(n * 0.9)],
                'p95': latencies[int(n * 0.95)],
                'p99': latencies[int(n * 0.99)],
                'count': n,
                'window': window
            }
    
    def export_metrics(self, format: str = 'json') -> str:
        """Export all metrics for analysis"""
        with self.lock:
            data = {
                'export_timestamp': datetime.now().isoformat(),
                'current_metrics': self.current_metrics,
                'command_statistics': self.get_command_statistics(),
                'agent_statistics': self.get_agent_statistics(),
                'latency_percentiles': {
                    window: self.get_latency_percentiles(window)
                    for window in self.time_windows.keys()
                },
                'total_samples': len(self.latency_samples),
                'total_connections': len(self.connection_samples)
            }
        
        if format == 'json':
            return json.dumps(data, indent=2)
        else:
            return str(data)

# Global performance monitor instance
performance_monitor = PerformanceMonitor()

# Convenience functions for recording metrics
def record_command_latency(command_id: str, agent_id: str, command_type: str, 
                          latency_ms: float, success: bool = True, error_message: Optional[str] = None):
    """Record command execution latency"""
    performance_monitor.record_latency(command_id, agent_id, command_type, 
                                     latency_ms, success, error_message)

def record_connection_quality(agent_id: str, connection_time_ms: float, **kwargs):
    """Record connection quality metrics"""
    performance_monitor.record_connection_event(agent_id, connection_time_ms, **kwargs)

def get_performance_summary() -> Dict[str, Any]:
    """Get quick performance summary"""
    current = performance_monitor.get_current_metrics()
    
    return {
        'status': 'healthy' if current['error_rate'] < 5 else 'degraded',
        'commands_per_second': current['commands_per_second'],
        'average_latency': current['p50_latency'],
        'error_rate': current['error_rate'],
        'active_connections': current['active_connections'],
        'p95_latency': current['p95_latency'],
        'timestamp': datetime.now().isoformat()
    }

# Example usage
if __name__ == "__main__":
    # Start monitoring
    performance_monitor.start()
    
    # Simulate some commands
    for i in range(100):
        record_command_latency(
            command_id=f"cmd_{i}",
            agent_id=f"agent_{i % 5}",
            command_type="execute" if i % 3 == 0 else "upload",
            latency_ms=50 + (i % 100),  # Simulate varying latency
            success=i % 10 != 0  # 10% failure rate
        )
        
        time.sleep(0.01)  # Small delay
    
    # Print summary
    print("📊 Performance Summary:")
    print(json.dumps(get_performance_summary(), indent=2))
    
    print("\n📈 Command Statistics:")
    print(json.dumps(performance_monitor.get_command_statistics(), indent=2))
    
    print("\n🤖 Agent Statistics:")
    print(json.dumps(performance_monitor.get_agent_statistics(), indent=2))
    
    print("\n⏱️ Latency Percentiles (5m):")
    print(json.dumps(performance_monitor.get_latency_percentiles('5m'), indent=2))
    
    # Stop monitoring
    performance_monitor.stop()