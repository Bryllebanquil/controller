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
import os
import base64

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
    """Configuration class for Neural Control Hub"""
    
    # Admin Authentication
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'Sphinx_Super_Admin_19')
    
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
            asyncio.create_task(pc.close())
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
        import psutil
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
        
    except ImportError:
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
                asyncio.create_task(pc.close())
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
        try:
            import psutil
            monitoring_data['system_overview']['system_load'] = {
                'cpu_percent': psutil.cpu_percent(interval=1),
                'memory_percent': psutil.virtual_memory().percent,
                'network_io': psutil.net_io_counters()._asdict()
            }
        except ImportError:
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
        <title>Neural Control Hub - Login Blocked</title>
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
                <h1>NEURAL CONTROL HUB</h1>
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
        <title>Neural Control Hub - Login</title>
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
                <h1>NEURAL CONTROL HUB</h1>
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
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Control Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.7.2/socket.io.js"></script>
    <style>
        :root {
            --primary-bg: #0a0a0f;
            --secondary-bg: #1a1a2e;
            --tertiary-bg: #16213e;
            --accent-blue: #00d4ff;
            --accent-purple: #6c5ce7;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --text-primary: #ffffff;
            --text-secondary: #a0a0a0;
            --border-color: #2d3748;
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
            overflow-x: hidden;
        }

        .neural-bg {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: 
                radial-gradient(circle at 20% 80%, rgba(0, 212, 255, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 80% 20%, rgba(108, 92, 231, 0.1) 0%, transparent 50%),
                radial-gradient(circle at 40% 40%, rgba(0, 255, 136, 0.05) 0%, transparent 50%);
            z-index: -1;
        }

        .top-bar {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border-bottom: 1px solid var(--glass-border);
            padding: 15px 0;
            position: sticky;
            top: 0;
            z-index: 100;
        }

        .top-bar-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }

        .header {
            text-align: center;
            margin-bottom: 30px;
            padding: 20px 0;
        }

        .header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 2.5rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 8px;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        }

        .header .subtitle {
            font-size: 1rem;
            color: var(--text-secondary);
            font-weight: 300;
        }

        .logout-btn {
            background: linear-gradient(45deg, var(--accent-red), #ff6b7a);
            border: none;
            border-radius: 8px;
            padding: 8px 16px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            text-decoration: none;
            font-size: 0.9rem;
        }

        .logout-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(255, 71, 87, 0.3);
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .main-grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 25px;
            margin-bottom: 25px;
        }

        .panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
            transition: all 0.3s ease;
        }

        .panel:hover {
            transform: translateY(-2px);
            box-shadow: 0 12px 48px rgba(0, 0, 0, 0.4);
        }

        .panel-header {
            display: flex;
            align-items: center;
            margin-bottom: 20px;
            padding-bottom: 15px;
            border-bottom: 1px solid var(--border-color);
        }

        .panel-icon {
            width: 24px;
            height: 24px;
            margin-right: 12px;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .panel-title {
            font-family: 'Orbitron', monospace;
            font-size: 1.2rem;
            font-weight: 700;
            color: var(--text-primary);
        }

        .agent-grid {
            display: grid;
            gap: 12px;
            max-height: 400px;
            overflow-y: auto;
        }

        .agent-card {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 15px;
            cursor: pointer;
            transition: all 0.3s ease;
            position: relative;
        }

        .agent-card:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.2);
        }

        .agent-card.selected {
            border-color: var(--accent-green);
            background: rgba(0, 255, 136, 0.1);
            box-shadow: 0 4px 20px rgba(0, 255, 136, 0.3);
        }

        .agent-status {
            position: absolute;
            top: 10px;
            right: 10px;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: var(--accent-green);
            box-shadow: 0 0 10px var(--accent-green);
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }

        .agent-id {
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 5px;
        }

        .agent-info {
            font-size: 0.9rem;
            color: var(--text-secondary);
        }

        .control-section {
            display: grid;
            gap: 16px;
        }

        .control-group {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 12px;
            padding: 16px;
            transition: all 0.3s ease;
        }

        .control-group:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.1);
        }

        .control-header {
            font-family: 'Orbitron', monospace;
            font-size: 1rem;
            font-weight: 600;
            color: var(--accent-blue);
            margin-bottom: 15px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }

        .input-group {
            margin-bottom: 15px;
        }

        .input-label {
            display: block;
            font-size: 0.9rem;
            color: var(--text-secondary);
            margin-bottom: 8px;
            font-weight: 500;
        }

        .neural-input {
            width: 100%;
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 12px 16px;
            color: var(--text-primary);
            font-size: 0.95rem;
            transition: all 0.3s ease;
        }

        .neural-input:focus {
            outline: none;
            border-color: var(--accent-blue);
            box-shadow: 0 0 0 3px rgba(0, 212, 255, 0.1);
        }

        .neural-input[readonly] {
            background: rgba(255, 255, 255, 0.05);
            color: var(--text-secondary);
        }

        .btn {
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border: none;
            border-radius: 8px;
            padding: 12px 24px;
            color: white;
            font-weight: 600;
            cursor: pointer;
            transition: all 0.3s ease;
            margin-right: 10px;
            margin-bottom: 10px;
            position: relative;
            overflow: hidden;
        }

        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 25px rgba(0, 212, 255, 0.3);
        }

        .btn:active {
            transform: translateY(0);
        }

        .btn-danger {
            background: linear-gradient(45deg, var(--accent-red), #ff6b7a);
        }

        .btn-success {
            background: linear-gradient(45deg, var(--accent-green), #2ed573);
        }

        .output-terminal {
            background: #000;
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 20px;
            font-family: 'Courier New', monospace;
            color: var(--accent-green);
            min-height: 200px;
            max-height: 400px;
            overflow-y: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
            position: relative;
        }

        .output-terminal::before {
            content: "NEURAL_TERMINAL_v2.1 > ";
            color: var(--accent-blue);
            font-weight: bold;
        }

        .status-indicator {
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 0.85rem;
            font-weight: 600;
            margin-top: 10px;
            display: none;
        }

        .status-success {
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }

        .status-error {
            background: rgba(255, 71, 87, 0.2);
            color: var(--accent-red);
            border: 1px solid var(--accent-red);
        }

        .config-status {
            display: grid;
            gap: 12px;
        }

        .config-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 8px 0;
            border-bottom: 1px solid var(--border-color);
        }

        .config-item:last-child {
            border-bottom: none;
        }

        .config-label {
            font-weight: 500;
            color: var(--text-secondary);
        }

        .config-value {
            font-family: 'Orbitron', monospace;
            color: var(--accent-blue);
            font-size: 0.9rem;
        }

        .password-management {
            display: grid;
            gap: 16px;
        }

        .password-strength {
            margin-top: 8px;
            padding: 8px;
            border-radius: 4px;
            font-size: 0.85rem;
            font-weight: 500;
        }

        .password-weak {
            background: rgba(255, 71, 87, 0.2);
            color: var(--accent-red);
            border: 1px solid var(--accent-red);
        }

        .password-medium {
            background: rgba(255, 193, 7, 0.2);
            color: #ffc107;
            border: 1px solid #ffc107;
        }

        .password-strong {
            background: rgba(0, 255, 136, 0.2);
            color: var(--accent-green);
            border: 1px solid var(--accent-green);
        }

        .no-agents {
            text-align: center;
            padding: 40px 20px;
            color: var(--text-secondary);
        }

        .no-agents-icon {
            font-size: 3rem;
            margin-bottom: 15px;
            opacity: 0.5;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 8px;
        }

        ::-webkit-scrollbar-track {
            background: var(--primary-bg);
        }

        ::-webkit-scrollbar-thumb {
            background: var(--accent-blue);
            border-radius: 4px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: var(--accent-purple);
        }

        /* Responsive Design */
        @media (max-width: 768px) {
            .main-grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
            
            .top-bar-content {
                flex-direction: column;
                gap: 15px;
            }
            
            .container {
                padding: 15px;
            }
        }
    </style>
</head>
<body>
    <div class="neural-bg"></div>
    
    <div class="top-bar">
        <div class="top-bar-content">
            <div class="header">
                <h1>NEURAL CONTROL HUB</h1>
                <p class="subtitle">Advanced Command & Control Interface</p>
            </div>
            <a href="/logout" class="logout-btn">Logout</a>
        </div>
    </div>
    
    <div class="container">
        <div class="main-grid">
            <!-- Agents Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon">🔗</div>
                    <div class="panel-title">Active Agents</div>
                </div>
                <div class="agent-grid" id="agent-list">
                    <div class="no-agents">
                        <div class="no-agents-icon">🤖</div>
                        <div>No agents connected</div>
                        <div style="font-size: 0.8rem; margin-top: 5px;">Waiting for neural links...</div>
                    </div>
                </div>
            </div>

            <!-- Control Panel -->
            <div class="panel">
                <div class="panel-header">
                    <div class="panel-icon">⚡</div>
                    <div class="panel-title">Command Interface</div>
                </div>
                
                <div class="control-section">
                    <div class="control-group">
                        <div class="control-header">Target Selection</div>
                        <div class="input-group">
                            <label class="input-label">Selected Agent</label>
                            <input type="text" class="neural-input" id="agent-id" readonly placeholder="Select an agent from the left panel">
                        </div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Command Execution</div>
                        <div class="input-group">
                            <label class="input-label">Command</label>
                            <input type="text" class="neural-input" id="command" placeholder="Enter command to execute...">
                        </div>
                        <button class="btn" onclick="issueCommand()">Execute Command</button>
                        <div id="command-status" class="status-indicator"></div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Quick Actions</div>
                        <button class="btn" onclick="listProcesses()">List Processes</button>
                        <button class="btn" onclick="startScreenStream()">Screen Stream</button>
                        <button class="btn" onclick="startCameraStream()">Camera Stream</button>
                        <button class="btn btn-danger" onclick="stopAllStreams()">Stop All Streams</button>
                    </div>

                    <div class="control-group">
                        <div class="control-header">WebRTC Commands</div>
                        <button class="btn btn-success" onclick="startWebRTCCommand()">Start WebRTC</button>
                        <button class="btn btn-danger" onclick="stopWebRTCCommand()">Stop WebRTC</button>
                        <button class="btn" onclick="getWebRTCStatsCommand()">Get Stats</button>
                        <button class="btn" onclick="setWebRTCQuality()">Set Quality</button>
                    </div>

                    <div class="control-group">
                        <div class="control-header">Live Keyboard</div>
                        <div class="input-group">
                            <label class="input-label">Press keys here to control the agent directly</label>
                            <div id="live-keyboard-input" tabindex="0" class="neural-input" style="height: 100px; overflow-y: auto;" placeholder="Click here and start typing..."></div>
                        </div>
                    </div>
                     <div class="control-group">
                        <div class="control-header">Live Mouse Control</div>
                        <div class="input-group">
                            <label class="input-label">Control the agent's mouse here</label>
                            <div id="live-mouse-area" style="width: 300px; height: 200px; border: 1px solid #ccc; position: relative; background: #222;"></div>
                        </div>
                        <div class="input-group">
                            <label class="input-label">Mouse Button</label>
                            <select id="mouse-button" class="neural-input">
                                <option value="left">Left</option>
                                <option value="right">Right</option>
                            </select>
                        </div>
                    </div>

                    <div class="control-group">
                        <div class="control-header">File Transfer</div>
                        <div class="input-group">
                            <label class="input-label">Upload File to Agent</label>
                            <input type="file" id="upload-file" class="neural-input">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Agent Destination Path (e.g., C:\Users\Public\file.txt)</label>
                            <input type="text" id="agent-upload-path" class="neural-input" placeholder="Enter full path on agent...">
                        </div>
                        <button class="btn" onclick="uploadFile()">Upload</button>
                        <div class="input-group" style="margin-top: 15px;">
                            <label class="input-label">Download File from Agent</label>
                            <input type="text" id="download-filename" class="neural-input" placeholder="Enter filename on agent...">
                        </div>
                        <div class="input-group">
                            <label class="input-label">Save to Local Path (e.g., C:\Users\YourName\Downloads\file.txt)</label>
                            <input type="text" id="local-download-path" class="neural-input" placeholder="Enter local path to save (e.g., C:\\Users\\YourName\\Downloads\\file.txt)">
                        </div>
                        <button class="btn" onclick="downloadFile()">Download</button>
                        <div id="file-transfer-status" class="status-indicator"></div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Video Stream Panel -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">🎥</div>
                <div class="panel-title">Live Video Stream (H.264)</div>
            </div>
            <video id="h264-video" width="640" height="360" controls autoplay muted style="background:#000; width:100%; max-width:100%; border-radius:10px;"></video>
            <div id="video-status" style="color:#00d4ff; margin-top:10px;"></div>
        </div>

        <!-- WebRTC Stream Panel -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">🌐</div>
                <div class="panel-title">WebRTC Stream (Low Latency)</div>
            </div>
            <div class="webrtc-controls">
                <button class="btn btn-success" onclick="startWebRTCStream()">Start WebRTC</button>
                <button class="btn btn-danger" onclick="stopWebRTCStream()">Stop WebRTC</button>
                <button class="btn" onclick="getWebRTCStats()">Get Stats</button>
            </div>
            <video id="webrtc-video" width="640" height="360" controls autoplay muted style="background:#000; width:100%; max-width:100%; border-radius:10px; margin-top:10px;"></video>
            <div id="webrtc-status" style="color:#00d4ff; margin-top:10px;"></div>
            <div id="webrtc-stats" style="color:#a0a0a0; margin-top:10px; font-size:0.9rem;"></div>
        </div>
        <!-- Output Terminal -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">💻</div>
                <div class="panel-title">Neural Terminal</div>
            </div>
            <div class="output-terminal" id="output-display">System ready. Awaiting commands...</div>
        </div>

        <!-- Configuration Status -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">⚙️</div>
                <div class="panel-title">System Configuration</div>
            </div>
            <div class="config-status" id="config-status">
                <div class="config-item">
                    <span class="config-label">Admin Password:</span>
                    <span class="config-value" id="admin-password-status">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Hash Algorithm:</span>
                    <span class="config-value" id="hash-algorithm">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Session Timeout:</span>
                    <span class="config-value" id="session-timeout">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Max Login Attempts:</span>
                    <span class="config-value" id="max-login-attempts">Checking...</span>
                </div>
                <div class="config-item">
                    <span class="config-label">Blocked IPs:</span>
                    <span class="config-value" id="blocked-ips">Checking...</span>
                </div>
                <button class="btn" onclick="refreshConfigStatus()">Refresh Status</button>
            </div>
        </div>

        <!-- Password Management -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">🔐</div>
                <div class="panel-title">Password Management</div>
            </div>
            <div class="password-management">
                <div class="control-group">
                    <div class="control-header">Change Admin Password</div>
                    <div class="input-group">
                        <label class="input-label">Current Password</label>
                        <input type="password" class="neural-input" id="current-password" placeholder="Enter current password">
                    </div>
                    <div class="input-group">
                        <label class="input-label">New Password</label>
                        <input type="password" class="neural-input" id="new-password" placeholder="Enter new password (min 8 chars)">
                    </div>
                    <div class="input-group">
                        <label class="input-label">Confirm New Password</label>
                        <input type="password" class="neural-input" id="confirm-password" placeholder="Confirm new password">
                    </div>
                    <button class="btn" onclick="changePassword()">Change Password</button>
                    <div id="password-change-status" class="status-indicator"></div>
                </div>
            </div>
        </div>

        <!-- Hidden audio player for streams -->
        <audio id="audio-player" controls style="display:none; width: 100%; margin-top: 10px;"></audio>
    </div>

    <script>
        const socket = io();
        let selectedAgentId = null;
        let videoWindow = null;
        let cameraWindow = null;
        let audioPlayer = null;

        // --- Agent Management ---
        function selectAgent(element, agentId) {
            if (selectedAgentId === agentId) return;

            // Clean up previous agent's state
            if (selectedAgentId) {
                stopAllStreams(); // Stop streams for the old agent
            }

            selectedAgentId = agentId;
            document.querySelectorAll('.agent-card').forEach(item => item.classList.remove('selected'));
            element.classList.add('selected');
            document.getElementById('agent-id').value = agentId;
            document.getElementById('output-display').textContent = `Agent ${agentId.substring(0,8)}... selected. Ready for commands.`;
            document.getElementById('command-status').style.display = 'none';
        }

        function updateAgentList(agents) {
            const agentList = document.getElementById('agent-list');
            agentList.innerHTML = '';

            if (Object.keys(agents).length === 0) {
                agentList.innerHTML = `
                    <div class="no-agents">
                        <div class="no-agents-icon">🤖</div>
                        <div>No agents connected</div>
                        <div style="font-size: 0.8rem; margin-top: 5px;">Waiting for neural links...</div>
                    </div>
                `;
                return;
            }

            for (const agentId in agents) {
                const agent = agents[agentId];
                const agentCard = document.createElement('div');
                agentCard.className = 'agent-card';
                agentCard.onclick = () => selectAgent(agentCard, agentId);
                
                const lastSeen = new Date(agent.last_seen).toLocaleString();
                agentCard.innerHTML = `
                    <div class="agent-status"></div>
                    <div class="agent-id">${agentId.substring(0, 8)}...</div>
                    <div class="agent-info">Last seen: ${lastSeen}</div>
                `;
                
                if (agentId === selectedAgentId) {
                    agentCard.classList.add('selected');
                }
                
                agentList.appendChild(agentCard);
            }
        }

        // --- Command & Control ---
        function issueCommand() {
            const command = document.getElementById('command').value;
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            if (!command) {
                showStatus('Please enter a command.', 'error');
                return;
            }

            socket.emit('execute_command', { agent_id: selectedAgentId, command: command });
            document.getElementById('output-display').textContent = `> ${command}\nExecuting...`;
            document.getElementById('command').value = '';
        }

        function issueCommandInternal(agentId, command) {
            if (!agentId) return;
            socket.emit('execute_command', { agent_id: agentId, command: command });
        }

        // --- Streaming ---
        function startScreenStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }
            
            issueCommandInternal(selectedAgentId, 'start-stream');
            issueCommandInternal(selectedAgentId, 'start-audio');

            if (videoWindow && !videoWindow.closed) videoWindow.close();
            videoWindow = window.open(`/video_feed/${selectedAgentId}`, `LiveStream_${selectedAgentId}`, 'width=800,height=600');

            audioPlayer = document.getElementById('audio-player');
            audioPlayer.src = `/audio_feed/${selectedAgentId}`;
            audioPlayer.style.display = 'block';
            audioPlayer.play();
            
            showStatus('Screen stream started', 'success');
        }

        function startCameraStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }

            issueCommandInternal(selectedAgentId, 'start-camera');
            if (cameraWindow && !cameraWindow.closed) cameraWindow.close();
            cameraWindow = window.open(`/camera_feed/${selectedAgentId}`, `CameraStream_${selectedAgentId}`, 'width=640,height=480');
            showStatus('Camera stream started', 'success');
        }

        function stopAllStreams() {
            if (selectedAgentId) {
                issueCommandInternal(selectedAgentId, 'stop-stream');
                issueCommandInternal(selectedAgentId, 'stop-audio');
                issueCommandInternal(selectedAgentId, 'stop-camera');
            }
            if (audioPlayer) {
                audioPlayer.pause();
                audioPlayer.src = '';
                audioPlayer.style.display = 'none';
            }
            if (videoWindow && !videoWindow.closed) videoWindow.close();
            if (cameraWindow && !cameraWindow.closed) cameraWindow.close();
            
            showStatus('All streams stopped', 'success');
        }

        function listProcesses() {
            document.getElementById('command').value = 'Get-Process | Select-Object Name, Id, MainWindowTitle | Format-Table -AutoSize';
            issueCommand();
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('command-status');
            statusDiv.style.display = 'block';
            statusDiv.className = `status-indicator status-${type}`;
            statusDiv.textContent = message;
            setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
        }

        // --- Socket.IO Event Handlers ---
        socket.on('connect', () => {
            console.log('Connected to controller');
            socket.emit('operator_connect'); // Announce presence as an operator
        });

        socket.on('disconnect', () => {
            console.log('Disconnected from controller');
        });

        socket.on('agent_list_update', (agents) => {
            updateAgentList(agents);
        });

        socket.on('command_output', (data) => {
            if (data.agent_id === selectedAgentId) {
                const outputDisplay = document.getElementById('output-display');
                // Append new output, keeping previous content
                outputDisplay.textContent += `\n${data.output}`;
                outputDisplay.scrollTop = outputDisplay.scrollHeight; // Scroll to bottom
            }
        });

        socket.on('status_update', (data) => {
            showStatus(data.message, data.type);
        });

        // Add key listener to command input
        document.getElementById('command').addEventListener('keyup', function(event) {
            if (event.key === 'Enter') {
                issueCommand();
            }
        });

        // Configuration status management
        function refreshConfigStatus() {
            fetch('/config-status')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('admin-password-status').textContent = 
                        data.admin_password_set ? `Set (${data.admin_password_length} chars)` : 'Not set';
                    document.getElementById('hash-algorithm').textContent = 
                        `${data.password_hash_algorithm} (${data.hash_iterations} iterations)`;
                    document.getElementById('session-timeout').textContent = 
                        `${data.session_timeout} seconds`;
                    document.getElementById('max-login-attempts').textContent = 
                        data.max_login_attempts.toString();
                    document.getElementById('blocked-ips').textContent = 
                        data.blocked_ips.length > 0 ? data.blocked_ips.join(', ') : 'None';
                })
                .catch(error => {
                    console.error('Error fetching config status:', error);
                    document.getElementById('admin-password-status').textContent = 'Error';
                    document.getElementById('hash-algorithm').textContent = 'Error';
                    document.getElementById('session-timeout').textContent = 'Error';
                    document.getElementById('max-login-attempts').textContent = 'Error';
                    document.getElementById('blocked-ips').textContent = 'Error';
                });
        }

        // Load config status on page load
        document.addEventListener('DOMContentLoaded', function() {
            refreshConfigStatus();
        });

        // Password management functions
        function changePassword() {
            const currentPassword = document.getElementById('current-password').value;
            const newPassword = document.getElementById('new-password').value;
            const confirmPassword = document.getElementById('confirm-password').value;
            const statusDiv = document.getElementById('password-change-status');

            // Validation
            if (!currentPassword || !newPassword || !confirmPassword) {
                showPasswordStatus('Please fill in all password fields.', 'error');
                return;
            }

            if (newPassword.length < 8) {
                showPasswordStatus('New password must be at least 8 characters long.', 'error');
                return;
            }

            if (newPassword !== confirmPassword) {
                showPasswordStatus('New passwords do not match.', 'error');
                return;
            }

            // Send password change request
            fetch('/change-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    current_password: currentPassword,
                    new_password: newPassword
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    showPasswordStatus('Password changed successfully!', 'success');
                    // Clear form
                    document.getElementById('current-password').value = '';
                    document.getElementById('new-password').value = '';
                    document.getElementById('confirm-password').value = '';
                    // Refresh config status
                    refreshConfigStatus();
                } else {
                    showPasswordStatus(data.message, 'error');
                }
            })
            .catch(error => {
                showPasswordStatus('Error changing password: ' + error.message, 'error');
            });
        }

        function showPasswordStatus(message, type) {
            const statusDiv = document.getElementById('password-change-status');
            statusDiv.style.display = 'block';
            statusDiv.className = `status-indicator status-${type}`;
            statusDiv.textContent = message;
            setTimeout(() => { statusDiv.style.display = 'none'; }, 5000);
        }

        // Password strength indicator
        function checkPasswordStrength(password) {
            let strength = 0;
            if (password.length >= 8) strength++;
            if (/[a-z]/.test(password)) strength++;
            if (/[A-Z]/.test(password)) strength++;
            if (/[0-9]/.test(password)) strength++;
            if (/[^A-Za-z0-9]/.test(password)) strength++;
            
            if (strength < 3) return 'weak';
            if (strength < 5) return 'medium';
            return 'strong';
        }

        // Add password strength indicator
        document.getElementById('new-password').addEventListener('input', function() {
            const password = this.value;
            const strength = checkPasswordStrength(password);
            const strengthDiv = this.parentNode.querySelector('.password-strength');
            
            if (strengthDiv) {
                strengthDiv.remove();
            }
            
            if (password.length > 0) {
                const div = document.createElement('div');
                div.className = `password-strength password-${strength}`;
                div.textContent = `Password strength: ${strength.charAt(0).toUpperCase() + strength.slice(1)}`;
                this.parentNode.appendChild(div);
            }
        });

        // --- Live Keyboard Event Listeners ---
        const liveKeyboardInput = document.getElementById('live-keyboard-input');
        const liveMouseArea = document.getElementById('live-mouse-area');

        liveKeyboardInput.addEventListener('keydown', (event) => {
            if (!selectedAgentId) return;
            event.preventDefault();
            socket.emit('live_key_press', {
                agent_id: selectedAgentId,
                event_type: 'down',
                key: event.key,
                code: event.code,
                shift: event.shiftKey,
                ctrl: event.ctrlKey,
                alt: event.altKey,
                meta: event.metaKey
            });
        });

        liveKeyboardInput.addEventListener('keyup', (event) => {
            if (!selectedAgentId) return;
            event.preventDefault();
            socket.emit('live_key_press', {
                agent_id: selectedAgentId,
                event_type: 'up',
                key: event.key,
                code: event.code
            });
        });
        liveMouseArea.addEventListener('mousemove', (event) => {
            if (!selectedAgentId) return;

            // Get the coordinates relative to the mouse area
            const rect = liveMouseArea.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            socket.emit('live_mouse_move', {
                agent_id: selectedAgentId,
                x: x,
                y: y
            });
        });

        liveMouseArea.addEventListener('mousedown', (event) => {
            if (!selectedAgentId) return;

            const button = document.getElementById('mouse-button').value;

            socket.emit('live_mouse_click', {
                agent_id: selectedAgentId,
                event_type: 'down',
                button: button
            });
        });

        liveMouseArea.addEventListener('mouseup', (event) => {
            if (!selectedAgentId) return;

            const button = document.getElementById('mouse-button').value;

            socket.emit('live_mouse_click', {
                agent_id: selectedAgentId,
                event_type: 'up',
                button: button
            });
        });

        // --- File Transfer (Chunked) ---
        let fileChunks = {};

        function uploadFile() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            const fileInput = document.getElementById('upload-file');
            const file = fileInput.files[0];

            if (!file) {
                showStatus('Please select a file to upload.', 'error');
                return;
            }

            const CHUNK_SIZE = 1024 * 512; // 512KB
            let offset = 0;

            showStatus(`Starting upload of ${file.name}...`, 'success');
            const reader = new FileReader();

            function readSlice(o) {
                const slice = file.slice(o, o + CHUNK_SIZE);
                reader.readAsDataURL(slice);
            }

            reader.onload = function(e) {
                const chunk = e.target.result;
                const agentUploadPath = document.getElementById('agent-upload-path').value;
                socket.emit('upload_file_chunk', {
                    agent_id: selectedAgentId,
                    filename: file.name,
                    data: chunk,
                    offset: offset,
                    destination_path: agentUploadPath
                });
                
                // Estimate offset for progress. Note: base64 is larger.
                // A more accurate progress would require more complex calculations.
                offset += CHUNK_SIZE; 
                if (offset > file.size) offset = file.size;

                showFileTransferProgress(file.name, offset, file.size, 'Uploading');

                if (offset < file.size) {
                    readSlice(offset);
                } else {
                    socket.emit('upload_file_end', {
                        agent_id: selectedAgentId,
                        filename: file.name
                    });
                    showStatus(`File ${file.name} upload complete.`, 'success');
                }
            };
            readSlice(0);
        }

        function downloadFile() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            const filename = document.getElementById('download-filename').value;
            if (!filename) {
                showStatus('Please enter a filename to download.', 'error');
                return;
            }
            fileChunks[filename] = []; // Reset chunks
            const localPath = document.getElementById('local-download-path').value;
            socket.emit('download_file', {
                agent_id: selectedAgentId,
                filename: filename,
                local_path: localPath
            });
            showStatus(`Requesting ${filename} from agent...`, 'success');
        }

        function showFileTransferProgress(filename, loaded, total, action) {
            const progress = total > 0 ? Math.round((loaded / total) * 100) : 100;
            const statusDiv = document.getElementById('file-transfer-status');
            statusDiv.style.display = 'block';
            statusDiv.className = 'status-indicator status-success';
            statusDiv.textContent = `${action} ${filename}: ${progress}%`;
             if (progress >= 100) {
                setTimeout(() => { statusDiv.style.display = 'none'; }, 3000);
            }
        }

        socket.on('file_download_chunk', (data) => {
            if (data.agent_id !== selectedAgentId) return;

            const { filename, chunk, offset, total_size, error } = data;

            if (error) {
                showStatus(`Error downloading ${filename}: ${error}`, 'error');
                if(fileChunks[filename]) delete fileChunks[filename];
                return;
            }

            if (!fileChunks[filename]) {
                fileChunks[filename] = [];
            }
            
            try {
                const byteString = atob(chunk.split(',')[1]);
                const ab = new ArrayBuffer(byteString.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteString.length; i++) {
                    ia[i] = byteString.charCodeAt(i);
                }
                fileChunks[filename].push(ia);
            } catch (e) {
                showStatus(`Error processing chunk for ${filename}: ${e}`, 'error');
                delete fileChunks[filename];
                return;
            }

            const loaded = fileChunks[filename].reduce((acc, curr) => acc + curr.length, 0);
            showFileTransferProgress(filename, loaded, total_size, 'Downloading');

            if (loaded >= total_size) {
                const blob = new Blob(fileChunks[filename], { type: 'application/octet-stream' });
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = filename;
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
                showStatus(`Downloaded ${filename}.`, 'success');
                delete fileChunks[filename];
            }
        });

        // --- H.264 Video Streaming via MSE ---
        let mseSourceBuffer = null;
        let mseMediaSource = null;
        let videoElement = null;
        let mseQueue = [];
        let mseReady = false;
        let videoAgentId = null;

        // --- WebRTC Variables ---
        let webrtcPeerConnection = null;
        let webrtcStream = null;
        let webrtcAgentId = null;

        function setupMSE() {
            videoElement = document.getElementById('h264-video');
            if (!window.MediaSource) {
                document.getElementById('video-status').textContent = 'MediaSource Extensions not supported.';
                return;
            }
            mseMediaSource = new MediaSource();
            videoElement.src = URL.createObjectURL(mseMediaSource);
            mseMediaSource.addEventListener('sourceopen', () => {
                mseSourceBuffer = mseMediaSource.addSourceBuffer('video/mp4; codecs="avc1.42E01E"');
                mseSourceBuffer.mode = 'segments';
                mseSourceBuffer.addEventListener('updateend', () => {
                    if (mseQueue.length > 0 && !mseSourceBuffer.updating) {
                        mseSourceBuffer.appendBuffer(mseQueue.shift());
                    }
                });
                mseReady = true;
            });
        }

        function requestVideoFrame(agentId) {
            if (!agentId) return;
            socket.emit('request_video_frame', {agent_id: agentId});
        }

        socket.on('video_frame', (data) => {
            if (!mseReady || !mseSourceBuffer) return;
            const frameData = data.frame;
            if (!frameData) return;
            // Convert base64 to ArrayBuffer
            const byteString = atob(frameData);
            const ab = new Uint8Array(byteString.length);
            for (let i = 0; i < byteString.length; i++) ab[i] = byteString.charCodeAt(i);
            if (mseSourceBuffer.updating || mseQueue.length > 0) {
                mseQueue.push(ab.buffer);
            } else {
                mseSourceBuffer.appendBuffer(ab.buffer);
            }
        });

        // Periodically request frames for the selected agent
        setInterval(() => {
            if (selectedAgentId) {
                requestVideoFrame(selectedAgentId);
            }
        }, 100);

        document.addEventListener('DOMContentLoaded', setupMSE);

        // --- WebRTC Functions ---
        function startWebRTCStream() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }

            if (webrtcPeerConnection) {
                stopWebRTCStream();
            }

            webrtcAgentId = selectedAgentId;
            
            // Create RTCPeerConnection
            const configuration = {
                iceServers: [
                    { urls: 'stun:stun.l.google.com:19302' },
                    { urls: 'stun:stun1.l.google.com:19302' }
                ]
            };

            webrtcPeerConnection = new RTCPeerConnection(configuration);
            
            // Set up event handlers
            webrtcPeerConnection.ontrack = function(event) {
                console.log('WebRTC track received:', event.track.kind);
                if (event.track.kind === 'video') {
                    document.getElementById('webrtc-video').srcObject = event.streams[0];
                }
                webrtcStream = event.streams[0];
            };

            webrtcPeerConnection.onicecandidate = function(event) {
                if (event.candidate) {
                    socket.emit('webrtc_ice_candidate', {
                        agent_id: webrtcAgentId,
                        candidate: event.candidate
                    });
                }
            };

            webrtcPeerConnection.onconnectionstatechange = function() {
                console.log('WebRTC connection state:', webrtcPeerConnection.connectionState);
                updateWebRTCStatus(webrtcPeerConnection.connectionState);
            };

            // Create offer
            webrtcPeerConnection.createOffer()
                .then(offer => webrtcPeerConnection.setLocalDescription(offer))
                .then(() => {
                    // Send offer to agent via controller
                    socket.emit('webrtc_offer', {
                        agent_id: webrtcAgentId,
                        offer: webrtcPeerConnection.localDescription.sdp
                    });
                    
                    updateWebRTCStatus('Creating offer...');
                    showStatus('WebRTC stream starting...', 'success');
                })
                .catch(error => {
                    console.error('Error creating WebRTC offer:', error);
                    showStatus('Error starting WebRTC stream', 'error');
                    updateWebRTCStatus('Error');
                });
        }

        function stopWebRTCStream() {
            if (webrtcPeerConnection) {
                webrtcPeerConnection.close();
                webrtcPeerConnection = null;
            }
            
            if (webrtcStream) {
                webrtcStream.getTracks().forEach(track => track.stop());
                webrtcStream = null;
            }
            
            document.getElementById('webrtc-video').srcObject = null;
            updateWebRTCStatus('Stopped');
            showStatus('WebRTC stream stopped', 'success');
            
            // Notify agent to stop WebRTC streaming
            if (webrtcAgentId) {
                socket.emit('webrtc_stop_streaming', { agent_id: webrtcAgentId });
                webrtcAgentId = null;
            }
        }

        function getWebRTCStats() {
            if (!webrtcPeerConnection) {
                showStatus('No WebRTC connection active', 'error');
                return;
            }

            webrtcPeerConnection.getStats()
                .then(stats => {
                    let statsText = 'WebRTC Statistics:\n';
                    stats.forEach(report => {
                        if (report.type === 'inbound-rtp' && report.mediaType === 'video') {
                            statsText += `Video: ${report.framesReceived} frames, ${report.bytesReceived} bytes\n`;
                        }
                        if (report.type === 'inbound-rtp' && report.mediaType === 'audio') {
                            statsText += `Audio: ${report.bytesReceived} bytes\n`;
                        }
                    });
                    document.getElementById('webrtc-stats').textContent = statsText;
                })
                .catch(error => {
                    console.error('Error getting WebRTC stats:', error);
                    showStatus('Error getting WebRTC stats', 'error');
                });
        }

        function updateWebRTCStatus(status) {
            const statusDiv = document.getElementById('webrtc-status');
            statusDiv.textContent = `Status: ${status}`;
            
            // Color coding for different states
            switch(status) {
                case 'connected':
                    statusDiv.style.color = '#00ff88';
                    break;
                case 'connecting':
                    statusDiv.style.color = '#ffc107';
                    break;
                case 'failed':
                case 'Error':
                    statusDiv.style.color = '#ff4757';
                    break;
                default:
                    statusDiv.style.color = '#00d4ff';
            }
        }

        // WebRTC Socket.IO event handlers
        socket.on('webrtc_answer', function(data) {
            if (webrtcPeerConnection && webrtcPeerConnection.signalingState !== 'closed') {
                const answer = new RTCSessionDescription({
                    type: data.type,
                    sdp: data.answer
                });
                
                webrtcPeerConnection.setRemoteDescription(answer)
                    .then(() => {
                        updateWebRTCStatus('Connected');
                        showStatus('WebRTC stream connected!', 'success');
                    })
                    .catch(error => {
                        console.error('Error setting remote description:', error);
                        updateWebRTCStatus('Error');
                        showStatus('Error connecting WebRTC stream', 'error');
                    });
            }
        });

        socket.on('webrtc_error', function(data) {
            console.error('WebRTC error:', data.message);
            updateWebRTCStatus('Error');
            showStatus(`WebRTC error: ${data.message}`, 'error');
        });

        socket.on('webrtc_stats', function(data) {
            console.log('WebRTC stats received:', data);
            let statsText = `Connection: ${data.connection_state}\n`;
            statsText += `ICE: ${data.ice_connection_state}\n`;
            statsText += `Signaling: ${data.signaling_state}`;
            document.getElementById('webrtc-stats').textContent = statsText;
        });

        // --- WebRTC Command Functions ---
        function startWebRTCCommand() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            
            socket.emit('webrtc_start_streaming', {
                agent_id: selectedAgentId,
                type: 'all'  // Start all streams (screen, audio, camera)
            });
            
            showStatus('Starting WebRTC streaming...', 'success');
        }

        function stopWebRTCCommand() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            
            socket.emit('webrtc_stop_streaming', {
                agent_id: selectedAgentId
            });
            
            showStatus('Stopping WebRTC streaming...', 'success');
        }

        function getWebRTCStatsCommand() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            
            socket.emit('webrtc_get_stats', {
                agent_id: selectedAgentId
            });
            
            showStatus('Requesting WebRTC stats...', 'success');
        }

        function setWebRTCQuality() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }
            
            const quality = prompt('Enter quality (low/medium/high/auto):', 'auto');
            if (quality && ['low', 'medium', 'high', 'auto'].includes(quality.toLowerCase())) {
                socket.emit('webrtc_set_quality', {
                    agent_id: selectedAgentId,
                    quality: quality.toLowerCase()
                });
                
                showStatus(`WebRTC quality set to ${quality}`, 'success');
            } else {
                showStatus('Invalid quality setting', 'error');
            }
        }

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

# --- Real-time Streaming Endpoints (optimized for 0.5-second intervals) ---
# 
# STREAMING OPTIMIZATION FOR REAL-TIME MONITORING:
# - Frame interval: 0.5 seconds (2 FPS)
# - Optimized for real-time monitoring with 0.5-second picture updates
# - Reduced latency and improved responsiveness
# - Better performance for monitoring applications
#

VIDEO_FRAMES = defaultdict(lambda: None)
CAMERA_FRAMES = defaultdict(lambda: None)
AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())

# Frame timing for real-time monitoring
FRAME_INTERVAL = 0.5  # 0.5-second intervals for 2 FPS

# HTTP streaming endpoints for browser compatibility
@app.route('/video_feed/<agent_id>')
@require_auth
def video_feed(agent_id):
    """Stream video feed for a specific agent"""
    def generate_video():
        while True:
            if agent_id in VIDEO_FRAMES_H264 and VIDEO_FRAMES_H264[agent_id]:
                frame = VIDEO_FRAMES_H264[agent_id]
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Send empty frame if no data available
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            time.sleep(0.5)  # 2 FPS
    
    return Response(generate_video(),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'})

@app.route('/camera_feed/<agent_id>')
@require_auth
def camera_feed(agent_id):
    """Stream camera feed for a specific agent"""
    def generate_camera():
        while True:
            if agent_id in CAMERA_FRAMES_H264 and CAMERA_FRAMES_H264[agent_id]:
                frame = CAMERA_FRAMES_H264[agent_id]
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            else:
                # Send empty frame if no data available
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + b'\r\n')
            time.sleep(0.5)  # 2 FPS
    
    return Response(generate_camera(),
                    mimetype='multipart/x-mixed-replace; boundary=frame',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'})

@app.route('/audio_feed/<agent_id>')
@require_auth
def audio_feed(agent_id):
    """Stream audio feed for a specific agent"""
    def generate_audio():
        while True:
            if agent_id in AUDIO_FRAMES_OPUS and AUDIO_FRAMES_OPUS[agent_id]:
                frame = AUDIO_FRAMES_OPUS[agent_id]
                yield frame
            else:
                # Send silence if no data available
                yield b'\x00' * 1024
            time.sleep(0.1)  # 10 FPS for audio
    
    return Response(generate_audio(),
                    mimetype='audio/wav',
                    headers={'Cache-Control': 'no-cache, no-store, must-revalidate',
                            'Pragma': 'no-cache',
                            'Expires': '0'})

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

# Add a new buffer for H.264 frames
VIDEO_FRAMES_H264 = defaultdict(lambda: None)

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

# Add new buffers for H.264 camera frames and Opus/PCM audio frames
CAMERA_FRAMES_H264 = defaultdict(lambda: None)
AUDIO_FRAMES_OPUS = defaultdict(lambda: None)

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
        asyncio.create_task(pc.setRemoteDescription(offer))
        
        # Create answer
        answer = asyncio.create_task(pc.createAnswer())
        answer.add_done_callback(lambda future: handle_answer_created(future, agent_id, request.sid))
        
        print(f"WebRTC offer received from {agent_id}")
        
    except Exception as e:
        print(f"Error handling WebRTC offer from {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error processing offer: {str(e)}'}, room=request.sid)

def handle_answer_created(future, agent_id, sid):
    """Handle WebRTC answer creation"""
    try:
        answer = future.result()
        asyncio.create_task(WEBRTC_PEER_CONNECTIONS[agent_id].setLocalDescription(answer))
        
        # Send answer back to agent
        socketio.emit('webrtc_answer', {
            'answer': answer.sdp,
            'type': answer.type
        }, room=sid)
        
        print(f"WebRTC answer sent to {agent_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC answer for {agent_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating answer: {str(e)}'}, room=sid)

@socketio.on('webrtc_ice_candidate')
def handle_webrtc_ice_candidate(data):
    """Handle ICE candidate from agent"""
    agent_id = data.get('agent_id')
    candidate = data.get('candidate')
    
    if not agent_id or not candidate or agent_id not in WEBRTC_PEER_CONNECTIONS:
        return
    
    try:
        pc = WEBRTC_PEER_CONNECTIONS[agent_id]
        asyncio.create_task(pc.addIceCandidate(candidate))
        print(f"ICE candidate added for {agent_id}")
        
    except Exception as e:
        print(f"Error adding ICE candidate for {agent_id}: {e}")

@socketio.on('webrtc_start_streaming')
def handle_webrtc_start_streaming(data):
    """Handle WebRTC streaming start request"""
    agent_id = data.get('agent_id')
    stream_type = data.get('type', 'all')  # screen, audio, camera, all
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Ensure peer connection exists
        if agent_id not in WEBRTC_PEER_CONNECTIONS:
            pc = create_webrtc_peer_connection(agent_id)
            if not pc:
                emit('webrtc_error', {'message': 'Failed to create peer connection'}, room=request.sid)
                return
        
        # Notify agent to start WebRTC streaming
        emit('start_webrtc_streaming', {
            'type': stream_type,
            'ice_servers': WEBRTC_CONFIG['ice_servers'],
            'codecs': WEBRTC_CONFIG['codecs']
        }, room=request.sid)
        
        print(f"WebRTC streaming started for {agent_id} ({stream_type})")
        
    except Exception as e:
        print(f"Error starting WebRTC streaming for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error starting streaming: {str(e)}'}, room=request.sid)

@socketio.on('webrtc_stop_streaming')
def handle_webrtc_stop_streaming(data):
    """Handle WebRTC streaming stop request"""
    agent_id = data.get('agent_id')
    
    if not agent_id:
        emit('webrtc_error', {'message': 'Agent ID required'}, room=request.sid)
        return
    
    try:
        # Close WebRTC connection
        close_webrtc_connection(agent_id)
        
        # Notify agent to stop WebRTC streaming
        emit('stop_webrtc_streaming', {}, room=request.sid)
        
        print(f"WebRTC streaming stopped for {agent_id}")
        
    except Exception as e:
        print(f"Error stopping WebRTC streaming for {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error stopping streaming: {str(e)}'}, room=request.sid)

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
        offer = asyncio.create_task(viewer_pc.createOffer())
        offer.add_done_callback(lambda future: handle_viewer_offer_created(future, viewer_id))
        
        print(f"WebRTC viewer {viewer_id} connected to agent {agent_id}")
        
    except Exception as e:
        print(f"Error connecting WebRTC viewer {viewer_id} to agent {agent_id}: {e}")
        emit('webrtc_error', {'message': f'Error connecting viewer: {str(e)}'}, room=request.sid)

def handle_viewer_offer_created(future, viewer_id):
    """Handle viewer offer creation"""
    try:
        offer = future.result()
        asyncio.create_task(WEBRTC_VIEWERS[viewer_id]['pc'].setLocalDescription(offer))
        
        # Send offer to viewer
        socketio.emit('webrtc_viewer_offer', {
            'offer': offer.sdp,
            'type': offer.type
        }, room=viewer_id)
        
        print(f"WebRTC viewer offer sent to {viewer_id}")
        
    except Exception as e:
        print(f"Error creating WebRTC viewer offer for {viewer_id}: {e}")
        socketio.emit('webrtc_error', {'message': f'Error creating viewer offer: {str(e)}'}, room=viewer_id)

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
        asyncio.create_task(viewer_pc.setRemoteDescription(answer))
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
            asyncio.create_task(viewer_pc.close())
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

if __name__ == "__main__":
    print("Starting Neural Control Hub with Socket.IO + WebRTC support...")
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
    socketio.run(app, host=Config.HOST, port=Config.PORT, debug=False)
