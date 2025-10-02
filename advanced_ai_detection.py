"""
Advanced AI-Powered Threat Detection and Anomaly Detection System
Implements machine learning models for behavioral analysis, anomaly detection, and automated threat response
"""

import numpy as np
import json
import time
import threading
import queue
from collections import defaultdict, deque
from datetime import datetime, timedelta
import hashlib
import pickle
import os

# Try importing ML libraries
try:
    from sklearn.ensemble import IsolationForest, RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.cluster import DBSCAN
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    print("Warning: scikit-learn not available, using rule-based detection")


class AdvancedThreatDetector:
    """AI-powered threat detection with behavioral analysis"""
    
    def __init__(self, sensitivity='medium'):
        self.sensitivity = sensitivity
        self.ml_models = {}
        self.baseline_profiles = {}
        self.anomaly_scores = defaultdict(list)
        self.threat_indicators = defaultdict(int)
        self.behavioral_patterns = defaultdict(lambda: deque(maxlen=1000))
        
        # Initialize ML models
        if ML_AVAILABLE:
            self._init_ml_models()
        
        # Rule-based threat signatures
        self.threat_signatures = self._load_threat_signatures()
        
        # Real-time monitoring thread
        self.monitoring_active = True
        self.alert_queue = queue.Queue()
        self.monitoring_thread = threading.Thread(target=self._monitor_threats, daemon=True)
        self.monitoring_thread.start()
    
    def _init_ml_models(self):
        """Initialize machine learning models for detection"""
        # Isolation Forest for anomaly detection
        self.ml_models['anomaly_detector'] = IsolationForest(
            contamination=0.1,
            random_state=42,
            n_estimators=100
        )
        
        # Random Forest for threat classification
        self.ml_models['threat_classifier'] = RandomForestClassifier(
            n_estimators=200,
            max_depth=15,
            random_state=42
        )
        
        # DBSCAN for clustering similar behaviors
        self.ml_models['behavior_clusterer'] = DBSCAN(
            eps=0.3,
            min_samples=5
        )
        
        # Feature scaler
        self.ml_models['scaler'] = StandardScaler()
        
        print("[AI] ML models initialized successfully")
    
    def _load_threat_signatures(self):
        """Load known threat signatures and IOCs"""
        return {
            'suspicious_processes': [
                'mimikatz', 'psexec', 'procdump', 'lsass', 'powershell.exe -enc',
                'cmd.exe /c', 'wscript', 'cscript', 'regsvr32', 'rundll32',
                'mshta', 'certutil', 'bitsadmin', 'installutil', 'regasm',
                'wmic', 'sc.exe', 'net.exe', 'netsh', 'taskkill', 'schtasks'
            ],
            'suspicious_network': [
                'tor', 'proxy', 'vpn', 'tunnel', 'reverse_shell', 'bind_shell',
                'nc.exe', 'ncat', 'socat', 'chisel', 'ngrok', 'ssh -D'
            ],
            'suspicious_files': [
                '.ps1', '.vbs', '.bat', '.cmd', '.hta', '.scr', '.pif',
                '.dll', '.exe', '.msi', 'payload', 'exploit', 'backdoor'
            ],
            'registry_persistence': [
                'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                'HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\RunOnce',
                'Winlogon', 'Userinit', 'Shell'
            ],
            'lateral_movement': [
                'psexec', 'wmiexec', 'smbexec', 'dcom', 'wmi', 'rdp',
                'winrm', 'ssh', 'powershell remoting'
            ],
            'credential_access': [
                'lsass.exe', 'sam', 'security', 'ntds.dit', 'credential',
                'password', 'hash', 'ticket', 'kerberos', 'ntlm'
            ],
            'privilege_escalation': [
                'uac bypass', 'token manipulation', 'exploit', 'vulnerability',
                'elevation', 'administrator', 'system', 'trustedinstaller'
            ]
        }
    
    def analyze_agent_behavior(self, agent_id, action_data):
        """
        Analyze agent behavior using AI and rule-based detection
        
        Args:
            agent_id: Unique agent identifier
            action_data: Dictionary containing action details (type, command, resource, etc.)
        
        Returns:
            dict: Threat analysis results with risk score and recommendations
        """
        timestamp = datetime.now()
        
        # Extract features from action
        features = self._extract_features(action_data)
        
        # Store behavioral pattern
        self.behavioral_patterns[agent_id].append({
            'timestamp': timestamp,
            'features': features,
            'action': action_data
        })
        
        # ML-based anomaly detection
        ml_score = 0
        if ML_AVAILABLE and len(self.behavioral_patterns[agent_id]) > 50:
            ml_score = self._ml_anomaly_detection(agent_id, features)
        
        # Rule-based threat detection
        rule_score, matched_rules = self._rule_based_detection(action_data)
        
        # Behavioral analysis
        behavior_score = self._behavioral_analysis(agent_id)
        
        # Calculate combined risk score (0-100)
        risk_score = self._calculate_risk_score(ml_score, rule_score, behavior_score)
        
        # Generate threat assessment
        threat_assessment = {
            'agent_id': agent_id,
            'timestamp': timestamp.isoformat(),
            'risk_score': risk_score,
            'ml_anomaly_score': ml_score,
            'rule_match_score': rule_score,
            'behavior_score': behavior_score,
            'matched_rules': matched_rules,
            'threat_level': self._categorize_threat_level(risk_score),
            'recommendations': self._generate_recommendations(risk_score, matched_rules),
            'action_summary': self._summarize_action(action_data)
        }
        
        # Store anomaly score
        self.anomaly_scores[agent_id].append({
            'timestamp': timestamp,
            'score': risk_score
        })
        
        # Alert if high risk
        if risk_score >= 70:
            self.alert_queue.put(threat_assessment)
        
        return threat_assessment
    
    def _extract_features(self, action_data):
        """Extract numerical features from action data for ML analysis"""
        features = []
        
        # Time-based features
        hour = datetime.now().hour
        features.append(hour)
        features.append(1 if 22 <= hour or hour <= 6 else 0)  # Off-hours activity
        
        # Action type encoding
        action_types = {'command': 1, 'file': 2, 'network': 3, 'registry': 4, 
                       'process': 5, 'credential': 6, 'system': 7}
        features.append(action_types.get(action_data.get('type', ''), 0))
        
        # String-based features
        text_data = str(action_data.get('command', '') + action_data.get('resource', ''))
        features.append(len(text_data))
        features.append(text_data.count('.'))
        features.append(text_data.count('\\'))
        features.append(text_data.count('/'))
        features.append(sum(c.isupper() for c in text_data))
        features.append(sum(c.isdigit() for c in text_data))
        
        # Suspicious keyword count
        suspicious_count = sum(1 for sig_list in self.threat_signatures.values() 
                              for sig in sig_list if sig.lower() in text_data.lower())
        features.append(suspicious_count)
        
        # Resource intensity (0-10)
        features.append(action_data.get('cpu_usage', 0))
        features.append(action_data.get('memory_usage', 0))
        features.append(action_data.get('network_usage', 0))
        
        # Privilege level (0=user, 1=admin, 2=system)
        priv_map = {'user': 0, 'admin': 1, 'system': 2}
        features.append(priv_map.get(action_data.get('privilege', 'user'), 0))
        
        return np.array(features)
    
    def _ml_anomaly_detection(self, agent_id, features):
        """Use ML models to detect anomalies"""
        try:
            # Get historical features
            historical_features = [bp['features'] for bp in self.behavioral_patterns[agent_id]]
            
            if len(historical_features) < 50:
                return 0
            
            # Scale features
            X = np.array(historical_features)
            X_scaled = self.ml_models['scaler'].fit_transform(X)
            
            # Fit and predict with Isolation Forest
            self.ml_models['anomaly_detector'].fit(X_scaled)
            current_scaled = self.ml_models['scaler'].transform([features])
            anomaly_score = self.ml_models['anomaly_detector'].score_samples(current_scaled)[0]
            
            # Convert to 0-100 scale (lower isolation forest score = more anomalous)
            normalized_score = max(0, min(100, (1 - anomaly_score) * 50))
            
            return normalized_score
        except Exception as e:
            print(f"[AI] ML detection error: {e}")
            return 0
    
    def _rule_based_detection(self, action_data):
        """Rule-based threat signature matching"""
        score = 0
        matched_rules = []
        
        text_data = str(action_data).lower()
        
        for category, signatures in self.threat_signatures.items():
            for signature in signatures:
                if signature.lower() in text_data:
                    score += 15
                    matched_rules.append({
                        'category': category,
                        'signature': signature,
                        'severity': 'high' if category in ['credential_access', 'privilege_escalation'] else 'medium'
                    })
        
        return min(score, 100), matched_rules
    
    def _behavioral_analysis(self, agent_id):
        """Analyze behavioral patterns for anomalies"""
        if agent_id not in self.behavioral_patterns:
            return 0
        
        patterns = list(self.behavioral_patterns[agent_id])
        if len(patterns) < 10:
            return 0
        
        score = 0
        
        # Check for rapid succession of commands
        recent_actions = [p for p in patterns[-20:]]
        if len(recent_actions) >= 10:
            time_diffs = []
            for i in range(1, len(recent_actions)):
                diff = (recent_actions[i]['timestamp'] - recent_actions[i-1]['timestamp']).total_seconds()
                time_diffs.append(diff)
            
            avg_time = np.mean(time_diffs) if time_diffs else 10
            if avg_time < 2:  # Commands less than 2 seconds apart
                score += 20
        
        # Check for unusual time patterns
        hours = [p['timestamp'].hour for p in patterns[-50:]]
        off_hour_ratio = sum(1 for h in hours if 22 <= h or h <= 6) / len(hours)
        if off_hour_ratio > 0.6:
            score += 15
        
        # Check for repeated failed actions
        failed_count = sum(1 for p in patterns[-20:] if p.get('action', {}).get('status') == 'failed')
        if failed_count > 5:
            score += 10
        
        return min(score, 100)
    
    def _calculate_risk_score(self, ml_score, rule_score, behavior_score):
        """Calculate combined risk score with weighted components"""
        weights = {
            'ml': 0.3,
            'rules': 0.5,
            'behavior': 0.2
        }
        
        total_score = (
            ml_score * weights['ml'] +
            rule_score * weights['rules'] +
            behavior_score * weights['behavior']
        )
        
        return min(100, max(0, total_score))
    
    def _categorize_threat_level(self, risk_score):
        """Categorize threat level based on risk score"""
        if risk_score >= 80:
            return 'CRITICAL'
        elif risk_score >= 60:
            return 'HIGH'
        elif risk_score >= 40:
            return 'MEDIUM'
        elif risk_score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'
    
    def _generate_recommendations(self, risk_score, matched_rules):
        """Generate security recommendations based on analysis"""
        recommendations = []
        
        if risk_score >= 70:
            recommendations.append("Immediate investigation required")
            recommendations.append("Consider isolating agent from network")
            recommendations.append("Review all recent agent activities")
        
        if risk_score >= 50:
            recommendations.append("Enhanced monitoring recommended")
            recommendations.append("Verify agent legitimacy")
        
        # Category-specific recommendations
        categories = {rule['category'] for rule in matched_rules}
        
        if 'credential_access' in categories:
            recommendations.append("Check for credential theft attempts")
            recommendations.append("Review authentication logs")
        
        if 'privilege_escalation' in categories:
            recommendations.append("Verify privilege levels")
            recommendations.append("Check for UAC bypass attempts")
        
        if 'lateral_movement' in categories:
            recommendations.append("Monitor network traffic for pivoting")
            recommendations.append("Check other systems for compromise")
        
        return recommendations
    
    def _summarize_action(self, action_data):
        """Create human-readable summary of action"""
        action_type = action_data.get('type', 'unknown')
        command = action_data.get('command', 'N/A')
        resource = action_data.get('resource', 'N/A')
        
        return f"{action_type.upper()}: {command[:100]} (Resource: {resource[:50]})"
    
    def _monitor_threats(self):
        """Background thread for continuous threat monitoring"""
        while self.monitoring_active:
            try:
                # Check for alerts
                if not self.alert_queue.empty():
                    alert = self.alert_queue.get()
                    self._handle_threat_alert(alert)
                
                time.sleep(1)
            except Exception as e:
                print(f"[AI] Monitoring error: {e}")
    
    def _handle_threat_alert(self, alert):
        """Handle high-risk threat alerts"""
        print(f"\n{'='*80}")
        print(f"[THREAT ALERT] Agent: {alert['agent_id']}")
        print(f"Risk Score: {alert['risk_score']:.1f}/100")
        print(f"Threat Level: {alert['threat_level']}")
        print(f"Action: {alert['action_summary']}")
        
        if alert['matched_rules']:
            print(f"\nMatched Rules:")
            for rule in alert['matched_rules'][:5]:
                print(f"  - [{rule['severity'].upper()}] {rule['category']}: {rule['signature']}")
        
        print(f"\nRecommendations:")
        for rec in alert['recommendations']:
            print(f"  • {rec}")
        print(f"{'='*80}\n")
    
    def get_agent_risk_profile(self, agent_id):
        """Get comprehensive risk profile for an agent"""
        if agent_id not in self.behavioral_patterns:
            return {'error': 'No data available for agent'}
        
        patterns = list(self.behavioral_patterns[agent_id])
        scores = self.anomaly_scores.get(agent_id, [])
        
        return {
            'agent_id': agent_id,
            'total_actions': len(patterns),
            'time_range': {
                'first_seen': patterns[0]['timestamp'].isoformat() if patterns else None,
                'last_seen': patterns[-1]['timestamp'].isoformat() if patterns else None
            },
            'average_risk_score': np.mean([s['score'] for s in scores]) if scores else 0,
            'max_risk_score': max([s['score'] for s in scores], default=0),
            'high_risk_actions': sum(1 for s in scores if s['score'] >= 70),
            'recent_activity': len([p for p in patterns if 
                                   (datetime.now() - p['timestamp']).total_seconds() < 3600])
        }
    
    def train_on_historical_data(self, historical_data):
        """Train ML models on historical data"""
        if not ML_AVAILABLE:
            print("[AI] ML libraries not available, skipping training")
            return
        
        try:
            # Extract features and labels from historical data
            X = []
            y = []
            
            for record in historical_data:
                features = self._extract_features(record['action'])
                label = 1 if record.get('is_threat', False) else 0
                X.append(features)
                y.append(label)
            
            X = np.array(X)
            y = np.array(y)
            
            # Train threat classifier
            self.ml_models['threat_classifier'].fit(X, y)
            
            print(f"[AI] Trained on {len(X)} historical records")
        except Exception as e:
            print(f"[AI] Training error: {e}")
    
    def export_threat_intelligence(self, filepath='threat_intelligence.json'):
        """Export collected threat intelligence"""
        intelligence = {
            'timestamp': datetime.now().isoformat(),
            'agents_monitored': len(self.behavioral_patterns),
            'total_alerts': self.alert_queue.qsize(),
            'agent_profiles': {
                agent_id: self.get_agent_risk_profile(agent_id)
                for agent_id in self.behavioral_patterns.keys()
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(intelligence, f, indent=2)
        
        print(f"[AI] Threat intelligence exported to {filepath}")
    
    def shutdown(self):
        """Gracefully shutdown the detector"""
        self.monitoring_active = False
        self.monitoring_thread.join(timeout=2)
        print("[AI] Threat detector shutdown complete")


# Global threat detector instance
threat_detector = None

def init_threat_detector(sensitivity='medium'):
    """Initialize global threat detector"""
    global threat_detector
    threat_detector = AdvancedThreatDetector(sensitivity=sensitivity)
    return threat_detector

def analyze_action(agent_id, action_data):
    """Convenient function to analyze an action"""
    global threat_detector
    if threat_detector is None:
        threat_detector = init_threat_detector()
    
    return threat_detector.analyze_agent_behavior(agent_id, action_data)


if __name__ == '__main__':
    # Test the threat detector
    print("Initializing Advanced Threat Detector...")
    detector = init_threat_detector(sensitivity='high')
    
    # Simulate some test actions
    test_actions = [
        {
            'type': 'command',
            'command': 'dir C:\\Users',
            'resource': 'filesystem',
            'cpu_usage': 2,
            'memory_usage': 10,
            'privilege': 'user'
        },
        {
            'type': 'command',
            'command': 'mimikatz.exe privilege::debug',
            'resource': 'credential',
            'cpu_usage': 45,
            'memory_usage': 80,
            'privilege': 'admin'
        },
        {
            'type': 'registry',
            'command': 'reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
            'resource': 'registry',
            'cpu_usage': 5,
            'memory_usage': 15,
            'privilege': 'user'
        }
    ]
    
    print("\nTesting threat detection...\n")
    for i, action in enumerate(test_actions):
        result = analyze_action('test_agent_001', action)
        print(f"Test {i+1}: Risk Score = {result['risk_score']:.1f}, Level = {result['threat_level']}")
    
    time.sleep(2)
    
    # Get agent profile
    profile = detector.get_agent_risk_profile('test_agent_001')
    print(f"\nAgent Profile: {json.dumps(profile, indent=2)}")
    
    detector.shutdown()
