"""
Advanced Encrypted Communication Channel with Key Rotation
Implements end-to-end encryption, perfect forward secrecy, and key rotation for C2 communications
"""

import os
import json
import time
import base64
import hashlib
import hmac
from datetime import datetime, timedelta
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding, ec
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
import secrets
import threading


class AdvancedCryptoChannel:
    """
    Advanced encrypted communication channel with:
    - AES-256-GCM and ChaCha20-Poly1305 encryption
    - ECDH key exchange for perfect forward secrecy
    - Automatic key rotation
    - Message authentication and integrity
    - Anti-replay protection
    """
    
    def __init__(self, role='controller', key_rotation_interval=3600):
        """
        Initialize crypto channel
        
        Args:
            role: 'controller' or 'agent'
            key_rotation_interval: Seconds between automatic key rotations (default 1 hour)
        """
        self.role = role
        self.key_rotation_interval = key_rotation_interval
        
        # Generate long-term identity keys
        self.identity_private_key = ec.generate_private_key(ec.SECP384R1(), default_backend())
        self.identity_public_key = self.identity_private_key.public_key()
        
        # Session keys
        self.session_key = None
        self.session_key_timestamp = None
        self.encryption_cipher = None
        self.decryption_cipher = None
        
        # Peer public keys
        self.peer_public_keys = {}
        
        # Message tracking for anti-replay
        self.message_sequence = 0
        self.received_sequences = {}
        self.sequence_window = 100
        
        # Key rotation thread
        self.rotation_active = True
        self.rotation_thread = threading.Thread(target=self._auto_rotate_keys, daemon=True)
        self.rotation_thread.start()
        
        print(f"[CRYPTO] {role.upper()} initialized with ECDH P-384 and AES-256-GCM")
    
    def get_public_key_bytes(self):
        """Export public key for exchange"""
        return self.identity_public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
    
    def set_peer_public_key(self, peer_id, public_key_bytes):
        """Store peer's public key"""
        public_key = serialization.load_pem_public_key(
            public_key_bytes,
            backend=default_backend()
        )
        self.peer_public_keys[peer_id] = public_key
        print(f"[CRYPTO] Peer {peer_id} public key registered")
    
    def establish_session(self, peer_id):
        """
        Establish encrypted session with peer using ECDH
        
        Args:
            peer_id: Identifier of peer to establish session with
            
        Returns:
            dict: Session establishment data to send to peer
        """
        if peer_id not in self.peer_public_keys:
            raise ValueError(f"Peer {peer_id} public key not registered")
        
        # Generate ephemeral key pair for this session
        ephemeral_private = ec.generate_private_key(ec.SECP384R1(), default_backend())
        ephemeral_public = ephemeral_private.public_key()
        
        # Perform ECDH with peer's identity key
        shared_secret = ephemeral_private.exchange(
            ec.ECDH(),
            self.peer_public_keys[peer_id]
        )
        
        # Derive session key using HKDF
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=f"{self.role}_{peer_id}_session".encode(),
            backend=default_backend()
        )
        self.session_key = hkdf.derive(shared_secret)
        self.session_key_timestamp = datetime.now()
        
        # Initialize AEAD ciphers
        self._init_ciphers()
        
        # Reset sequence tracking
        self.message_sequence = 0
        self.received_sequences[peer_id] = []
        
        # Return ephemeral public key for peer
        ephemeral_public_bytes = ephemeral_public.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        )
        
        print(f"[CRYPTO] Session established with {peer_id}")
        
        return {
            'peer_id': self.role,
            'ephemeral_public_key': base64.b64encode(ephemeral_public_bytes).decode(),
            'timestamp': self.session_key_timestamp.isoformat()
        }
    
    def complete_session_establishment(self, peer_id, session_data):
        """
        Complete session establishment using peer's ephemeral key
        
        Args:
            peer_id: Identifier of peer
            session_data: Session data from peer
        """
        # Load peer's ephemeral public key
        ephemeral_public_bytes = base64.b64decode(session_data['ephemeral_public_key'])
        peer_ephemeral_public = serialization.load_pem_public_key(
            ephemeral_public_bytes,
            backend=default_backend()
        )
        
        # Generate our ephemeral key
        ephemeral_private = ec.generate_private_key(ec.SECP384R1(), default_backend())
        
        # Perform ECDH
        shared_secret = ephemeral_private.exchange(ec.ECDH(), peer_ephemeral_public)
        
        # Derive session key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=f"{peer_id}_{self.role}_session".encode(),
            backend=default_backend()
        )
        self.session_key = hkdf.derive(shared_secret)
        self.session_key_timestamp = datetime.now()
        
        # Initialize ciphers
        self._init_ciphers()
        
        # Reset sequence
        self.message_sequence = 0
        self.received_sequences[peer_id] = []
        
        print(f"[CRYPTO] Session completed with {peer_id}")
    
    def _init_ciphers(self):
        """Initialize AEAD ciphers with session key"""
        # Use ChaCha20-Poly1305 for better performance on systems without AES-NI
        self.encryption_cipher = ChaCha20Poly1305(self.session_key)
        self.decryption_cipher = ChaCha20Poly1305(self.session_key)
    
    def encrypt_message(self, plaintext, peer_id=None):
        """
        Encrypt message with authentication
        
        Args:
            plaintext: Message to encrypt (string or bytes)
            peer_id: Optional peer identifier for additional context
            
        Returns:
            dict: Encrypted message package
        """
        if self.session_key is None:
            raise ValueError("No session established")
        
        # Convert to bytes if string
        if isinstance(plaintext, str):
            plaintext = plaintext.encode('utf-8')
        
        # Generate nonce (96 bits for ChaCha20)
        nonce = secrets.token_bytes(12)
        
        # Increment sequence number
        self.message_sequence += 1
        
        # Build additional authenticated data (AAD)
        aad = json.dumps({
            'seq': self.message_sequence,
            'timestamp': datetime.now().isoformat(),
            'sender': self.role,
            'peer': peer_id
        }).encode()
        
        # Encrypt with authentication
        ciphertext = self.encryption_cipher.encrypt(nonce, plaintext, aad)
        
        # Build encrypted package
        package = {
            'version': '2.0',
            'nonce': base64.b64encode(nonce).decode(),
            'ciphertext': base64.b64encode(ciphertext).decode(),
            'aad': base64.b64encode(aad).decode(),
            'sequence': self.message_sequence,
            'timestamp': datetime.now().isoformat()
        }
        
        return package
    
    def decrypt_message(self, package, peer_id=None):
        """
        Decrypt and verify message
        
        Args:
            package: Encrypted message package
            peer_id: Optional peer identifier for validation
            
        Returns:
            str: Decrypted plaintext
        """
        if self.session_key is None:
            raise ValueError("No session established")
        
        # Extract components
        nonce = base64.b64decode(package['nonce'])
        ciphertext = base64.b64decode(package['ciphertext'])
        aad = base64.b64decode(package['aad'])
        sequence = package['sequence']
        
        # Anti-replay check
        if peer_id in self.received_sequences:
            if sequence in self.received_sequences[peer_id]:
                raise ValueError("Replay attack detected: duplicate sequence number")
            
            # Keep only recent sequences (window)
            self.received_sequences[peer_id].append(sequence)
            if len(self.received_sequences[peer_id]) > self.sequence_window:
                self.received_sequences[peer_id] = self.received_sequences[peer_id][-self.sequence_window:]
        else:
            self.received_sequences[peer_id] = [sequence]
        
        # Decrypt and verify
        try:
            plaintext = self.decryption_cipher.decrypt(nonce, ciphertext, aad)
            return plaintext.decode('utf-8')
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def rotate_session_key(self, peer_id):
        """
        Rotate session key for forward secrecy
        
        Args:
            peer_id: Identifier of peer to rotate key with
            
        Returns:
            dict: Key rotation data to send to peer
        """
        print(f"[CRYPTO] Rotating session key with {peer_id}")
        
        # Derive new key from current key + random salt
        if self.session_key:
            salt = secrets.token_bytes(32)
            hkdf = HKDF(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                info=f"rotation_{int(time.time())}".encode(),
                backend=default_backend()
            )
            new_key = hkdf.derive(self.session_key)
        else:
            # No existing key, establish new session
            return self.establish_session(peer_id)
        
        # Update session key
        old_key = self.session_key
        self.session_key = new_key
        self.session_key_timestamp = datetime.now()
        
        # Re-initialize ciphers
        self._init_ciphers()
        
        # Reset sequence for new key
        self.message_sequence = 0
        
        return {
            'rotation_salt': base64.b64encode(salt).decode(),
            'timestamp': self.session_key_timestamp.isoformat()
        }
    
    def apply_key_rotation(self, rotation_data):
        """
        Apply key rotation from peer
        
        Args:
            rotation_data: Key rotation data from peer
        """
        salt = base64.b64decode(rotation_data['rotation_salt'])
        
        if not self.session_key:
            raise ValueError("No session key to rotate")
        
        # Derive new key
        hkdf = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            info=f"rotation_{int(time.time())}".encode(),
            backend=default_backend()
        )
        self.session_key = hkdf.derive(self.session_key)
        self.session_key_timestamp = datetime.now()
        
        # Re-initialize ciphers
        self._init_ciphers()
        
        # Reset sequence
        self.message_sequence = 0
        
        print("[CRYPTO] Applied key rotation from peer")
    
    def _auto_rotate_keys(self):
        """Background thread for automatic key rotation"""
        while self.rotation_active:
            time.sleep(60)  # Check every minute
            
            if self.session_key and self.session_key_timestamp:
                age = (datetime.now() - self.session_key_timestamp).total_seconds()
                
                if age >= self.key_rotation_interval:
                    print(f"[CRYPTO] Session key expired ({age:.0f}s old), rotation needed")
                    # Note: Actual rotation requires coordination with peer
                    # This is handled by the C2 protocol layer
    
    def get_session_info(self):
        """Get current session information"""
        if not self.session_key:
            return {'status': 'no_session'}
        
        age = (datetime.now() - self.session_key_timestamp).total_seconds()
        
        return {
            'status': 'active',
            'established': self.session_key_timestamp.isoformat(),
            'age_seconds': age,
            'messages_sent': self.message_sequence,
            'rotation_due': age >= self.key_rotation_interval,
            'algorithm': 'ChaCha20-Poly1305',
            'key_exchange': 'ECDH-P384'
        }
    
    def export_config(self):
        """Export configuration for backup/recovery"""
        return {
            'role': self.role,
            'identity_public_key': base64.b64encode(self.get_public_key_bytes()).decode(),
            'key_rotation_interval': self.key_rotation_interval,
            'created': datetime.now().isoformat()
        }
    
    def shutdown(self):
        """Securely shutdown crypto channel"""
        self.rotation_active = False
        self.rotation_thread.join(timeout=2)
        
        # Securely erase keys from memory
        if self.session_key:
            self.session_key = b'\x00' * len(self.session_key)
        
        print("[CRYPTO] Crypto channel shutdown complete")


class SecureMessageProtocol:
    """High-level secure messaging protocol using CryptoChannel"""
    
    def __init__(self, channel: AdvancedCryptoChannel):
        self.channel = channel
    
    def send_command(self, command, target_id):
        """Send encrypted command to agent"""
        message = {
            'type': 'command',
            'command': command,
            'timestamp': datetime.now().isoformat(),
            'sender': self.channel.role
        }
        
        message_json = json.dumps(message)
        encrypted = self.channel.encrypt_message(message_json, target_id)
        
        return encrypted
    
    def receive_command(self, encrypted_package, sender_id):
        """Receive and decrypt command"""
        decrypted = self.channel.decrypt_message(encrypted_package, sender_id)
        message = json.loads(decrypted)
        
        # Validate message structure
        if 'type' not in message or 'command' not in message:
            raise ValueError("Invalid message format")
        
        return message
    
    def send_result(self, result, target_id):
        """Send encrypted command result"""
        message = {
            'type': 'result',
            'result': result,
            'timestamp': datetime.now().isoformat(),
            'sender': self.channel.role
        }
        
        message_json = json.dumps(message)
        encrypted = self.channel.encrypt_message(message_json, target_id)
        
        return encrypted
    
    def receive_result(self, encrypted_package, sender_id):
        """Receive and decrypt result"""
        decrypted = self.channel.decrypt_message(encrypted_package, sender_id)
        message = json.loads(decrypted)
        
        if 'type' not in message or 'result' not in message:
            raise ValueError("Invalid message format")
        
        return message


if __name__ == '__main__':
    # Test the crypto channel
    print("Testing Advanced Crypto Channel\n")
    
    # Create controller and agent channels
    controller = AdvancedCryptoChannel(role='controller', key_rotation_interval=300)
    agent = AdvancedCryptoChannel(role='agent', key_rotation_interval=300)
    
    # Exchange public keys
    controller.set_peer_public_key('agent_001', agent.get_public_key_bytes())
    agent.set_peer_public_key('controller', controller.get_public_key_bytes())
    
    # Establish session
    print("Establishing encrypted session...")
    session_init = controller.establish_session('agent_001')
    agent.complete_session_establishment('controller', session_init)
    
    # Test messaging
    print("\nTesting encrypted messaging...")
    
    test_message = "Execute command: whoami"
    print(f"Original: {test_message}")
    
    encrypted = controller.encrypt_message(test_message, 'agent_001')
    print(f"Encrypted: {encrypted['ciphertext'][:50]}...")
    
    decrypted = agent.decrypt_message(encrypted, 'controller')
    print(f"Decrypted: {decrypted}")
    
    # Test key rotation
    print("\nTesting key rotation...")
    rotation_data = controller.rotate_session_key('agent_001')
    agent.apply_key_rotation(rotation_data)
    
    # Test message after rotation
    test_message2 = "Command after key rotation"
    encrypted2 = controller.encrypt_message(test_message2, 'agent_001')
    decrypted2 = agent.decrypt_message(encrypted2, 'controller')
    print(f"Message after rotation: {decrypted2}")
    
    # Show session info
    print(f"\nController session: {json.dumps(controller.get_session_info(), indent=2)}")
    print(f"Agent session: {json.dumps(agent.get_session_info(), indent=2)}")
    
    # Cleanup
    controller.shutdown()
    agent.shutdown()
