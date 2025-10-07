#!/usr/bin/env python3
"""
Pure Controller - Simple Web-based Remote Control Controller
No privilege escalation, no UAC bypasses, no persistence
Pure Socket.IO communication with agents
"""

from flask import Flask, render_template_string, request
from flask_socketio import SocketIO, emit, join_room, leave_room
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'pure-controller-secret-key-2024'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Store connected agents
AGENTS = {}
OPERATORS = set()

def log(message):
    """Simple logging"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}")

# HTML Template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>Pure Controller</title>
    <script src="https://cdn.socket.io/4.5.4/socket.io.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
        }
        
        header {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
            margin-bottom: 20px;
        }
        
        h1 {
            color: #667eea;
            font-size: 2em;
            margin-bottom: 5px;
        }
        
        .subtitle {
            color: #666;
            font-size: 0.9em;
        }
        
        .main-grid {
            display: grid;
            grid-template-columns: 350px 1fr;
            gap: 20px;
        }
        
        .panel {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        
        .panel h2 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        
        .agent-item {
            background: #f7f7f7;
            padding: 15px;
            margin-bottom: 10px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
            border: 2px solid transparent;
        }
        
        .agent-item:hover {
            background: #efefef;
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.2);
        }
        
        .agent-item.active {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border-color: #667eea;
        }
        
        .agent-id {
            font-weight: bold;
            font-size: 0.9em;
            margin-bottom: 5px;
        }
        
        .agent-info {
            font-size: 0.85em;
            opacity: 0.8;
        }
        
        .agent-item.active .agent-info {
            opacity: 1;
        }
        
        .status-indicator {
            display: inline-block;
            width: 10px;
            height: 10px;
            border-radius: 50%;
            background: #4CAF50;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        
        .controls {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .btn {
            padding: 12px 20px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-size: 0.95em;
            font-weight: 600;
            transition: all 0.3s;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
        }
        
        .btn:active {
            transform: translateY(0);
        }
        
        .btn.danger {
            background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        }
        
        .terminal {
            background: #1e1e1e;
            border-radius: 8px;
            padding: 15px;
            height: 400px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 0.9em;
        }
        
        .terminal-output {
            color: #d4d4d4;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .terminal-input {
            color: #4EC9B0;
        }
        
        .command-input-wrapper {
            display: flex;
            gap: 10px;
            margin-top: 15px;
        }
        
        input[type="text"] {
            flex: 1;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 0.95em;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
        }
        
        .stat-value {
            font-size: 2em;
            font-weight: bold;
            margin: 10px 0;
        }
        
        .stat-label {
            font-size: 0.9em;
            opacity: 0.9;
        }
        
        .no-agent {
            text-align: center;
            color: #999;
            padding: 40px;
        }
        
        .timestamp {
            color: #888;
            font-size: 0.85em;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎮 Pure Controller</h1>
            <p class="subtitle">Simple Remote Agent Control - No UAC, No Persistence, Pure Communication</p>
        </header>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-label">Connected Agents</div>
                <div class="stat-value" id="agent-count">0</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Selected Agent</div>
                <div class="stat-value" id="selected-agent">None</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Controller Status</div>
                <div class="stat-value">Online</div>
            </div>
        </div>
        
        <div class="main-grid">
            <div class="panel">
                <h2>🖥️ Connected Agents</h2>
                <div id="agents-list">
                    <div class="no-agent">No agents connected</div>
                </div>
            </div>
            
            <div class="panel">
                <h2>⚡ Agent Control</h2>
                
                <div class="controls">
                    <button class="btn" onclick="getSystemInfo()">📊 System Info</button>
                    <button class="btn" onclick="getProcesses()">📋 Processes</button>
                    <button class="btn" onclick="getNetworkInfo()">🌐 Network</button>
                    <button class="btn" onclick="getFiles()">📁 Files</button>
                    <button class="btn danger" onclick="shutdownAgent()">🛑 Shutdown</button>
                </div>
                
                <h3 style="color: #667eea; margin: 20px 0 10px 0;">💻 Command Terminal</h3>
                <div class="terminal">
                    <div class="terminal-output" id="terminal-output">
                        Welcome to Pure Controller Terminal
                        Select an agent and enter commands...
                        
                    </div>
                </div>
                
                <div class="command-input-wrapper">
                    <input type="text" id="command-input" placeholder="Enter command..." onkeypress="handleEnter(event)">
                    <button class="btn" onclick="executeCommand()">▶ Execute</button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        const socket = io();
        let selectedAgent = null;
        const agents = new Map();
        
        socket.on('connect', () => {
            console.log('Connected to controller');
            socket.emit('operator_connect');
        });
        
        socket.on('agents_list', (data) => {
            updateAgentsList(data.agents);
        });
        
        socket.on('agent_connected', (data) => {
            console.log('Agent connected:', data);
            addAgent(data);
        });
        
        socket.on('agent_disconnected', (data) => {
            console.log('Agent disconnected:', data);
            removeAgent(data.agent_id);
        });
        
        socket.on('command_result', (data) => {
            if (data.agent_id === selectedAgent) {
                appendToTerminal(data.output, 'output');
            }
        });
        
        socket.on('system_info', (data) => {
            if (data.agent_id === selectedAgent) {
                const info = data.info;
                let output = `\\n=== System Information ===\\n`;
                output += `Hostname: ${info.hostname}\\n`;
                output += `OS: ${info.os} ${info.os_version}\\n`;
                output += `Architecture: ${info.architecture}\\n`;
                output += `Username: ${info.username}\\n`;
                output += `Python: ${info.python_version}\\n`;
                if (info.cpu_usage !== undefined) {
                    output += `CPU Usage: ${info.cpu_usage.toFixed(2)}%\\n`;
                    output += `Memory Usage: ${info.memory_percent.toFixed(2)}%\\n`;
                    output += `Disk Usage: ${info.disk_percent.toFixed(2)}%\\n`;
                }
                appendToTerminal(output, 'output');
            }
        });
        
        socket.on('process_list', (data) => {
            if (data.agent_id === selectedAgent) {
                let output = `\\n=== Running Processes (${data.processes.length}) ===\\n`;
                data.processes.slice(0, 20).forEach(proc => {
                    output += `PID: ${proc.pid} | ${proc.name} | CPU: ${proc.cpu_percent}%\\n`;
                });
                appendToTerminal(output, 'output');
            }
        });
        
        socket.on('network_info', (data) => {
            if (data.agent_id === selectedAgent) {
                let output = `\\n=== Network Information ===\\n`;
                output += `Active Connections: ${data.info.connections ? data.info.connections.length : 0}\\n`;
                if (data.info.connections) {
                    data.info.connections.slice(0, 10).forEach(conn => {
                        output += `${conn.local_address} → ${conn.remote_address} [${conn.status}]\\n`;
                    });
                }
                appendToTerminal(output, 'output');
            }
        });
        
        socket.on('file_listing', (data) => {
            if (data.agent_id === selectedAgent) {
                const listing = data.listing;
                if (listing.error) {
                    appendToTerminal(`Error: ${listing.error}`, 'output');
                } else {
                    let output = `\\n=== Files in ${listing.path} ===\\n`;
                    listing.items.forEach(item => {
                        const type = item.is_dir ? '[DIR]' : '[FILE]';
                        const size = item.is_dir ? '' : `(${formatBytes(item.size)})`;
                        output += `${type} ${item.name} ${size}\\n`;
                    });
                    appendToTerminal(output, 'output');
                }
            }
        });
        
        function updateAgentsList(agentsList) {
            const container = document.getElementById('agents-list');
            agents.clear();
            
            if (agentsList.length === 0) {
                container.innerHTML = '<div class="no-agent">No agents connected</div>';
                document.getElementById('agent-count').textContent = '0';
                return;
            }
            
            container.innerHTML = '';
            agentsList.forEach(agent => {
                agents.set(agent.id, agent);
                addAgentElement(agent);
            });
            
            document.getElementById('agent-count').textContent = agentsList.length;
        }
        
        function addAgent(agent) {
            agents.set(agent.id, agent);
            addAgentElement(agent);
            document.getElementById('agent-count').textContent = agents.size;
        }
        
        function removeAgent(agentId) {
            agents.delete(agentId);
            const element = document.getElementById(`agent-${agentId}`);
            if (element) element.remove();
            
            if (selectedAgent === agentId) {
                selectedAgent = null;
                document.getElementById('selected-agent').textContent = 'None';
            }
            
            document.getElementById('agent-count').textContent = agents.size;
            
            if (agents.size === 0) {
                document.getElementById('agents-list').innerHTML = '<div class="no-agent">No agents connected</div>';
            }
        }
        
        function addAgentElement(agent) {
            const container = document.getElementById('agents-list');
            if (container.querySelector('.no-agent')) {
                container.innerHTML = '';
            }
            
            const div = document.createElement('div');
            div.className = 'agent-item';
            div.id = `agent-${agent.id}`;
            div.onclick = () => selectAgent(agent.id);
            
            div.innerHTML = `
                <div class="agent-id">
                    <span class="status-indicator"></span>
                    ${agent.id.substring(0, 8)}
                </div>
                <div class="agent-info">
                    ${agent.hostname || 'Unknown'} | ${agent.os || 'Unknown'}<br>
                    ${agent.username || 'Unknown'}
                </div>
            `;
            
            container.appendChild(div);
        }
        
        function selectAgent(agentId) {
            selectedAgent = agentId;
            
            document.querySelectorAll('.agent-item').forEach(item => {
                item.classList.remove('active');
            });
            
            const element = document.getElementById(`agent-${agentId}`);
            if (element) {
                element.classList.add('active');
            }
            
            document.getElementById('selected-agent').textContent = agentId.substring(0, 8);
            appendToTerminal(`\\n=== Selected agent: ${agentId.substring(0, 8)} ===\\n`, 'output');
        }
        
        function executeCommand() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            const input = document.getElementById('command-input');
            const command = input.value.trim();
            
            if (!command) return;
            
            appendToTerminal(`$ ${command}`, 'input');
            
            socket.emit('execute_command', {
                agent_id: selectedAgent,
                command: command
            });
            
            input.value = '';
        }
        
        function handleEnter(event) {
            if (event.key === 'Enter') {
                executeCommand();
            }
        }
        
        function getSystemInfo() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            socket.emit('get_system_info', { agent_id: selectedAgent });
        }
        
        function getProcesses() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            socket.emit('get_processes', { agent_id: selectedAgent });
        }
        
        function getNetworkInfo() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            socket.emit('get_network_info', { agent_id: selectedAgent });
        }
        
        function getFiles() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            const path = prompt('Enter path (leave empty for home directory):');
            socket.emit('get_file_listing', { 
                agent_id: selectedAgent,
                path: path || null
            });
        }
        
        function shutdownAgent() {
            if (!selectedAgent) {
                alert('Please select an agent first');
                return;
            }
            
            if (confirm('Are you sure you want to shutdown this agent?')) {
                socket.emit('shutdown', { agent_id: selectedAgent });
            }
        }
        
        function appendToTerminal(text, type) {
            const output = document.getElementById('terminal-output');
            const timestamp = new Date().toLocaleTimeString();
            const className = type === 'input' ? 'terminal-input' : '';
            
            output.innerHTML += `<span class="${className}">[${timestamp}] ${text}</span>\\n`;
            output.scrollTop = output.scrollHeight;
        }
        
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024;
            const sizes = ['B', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    """Serve the main page"""
    return render_template_string(HTML_TEMPLATE)

# Socket.IO Events - Operator (Controller UI)
@socketio.on('operator_connect')
def handle_operator_connect():
    """Handle operator connection"""
    OPERATORS.add(request.sid)
    join_room('operators')
    log(f"✅ Operator connected: {request.sid}")
    
    # Send current agents list
    agents_list = [agent for agent in AGENTS.values()]
    emit('agents_list', {'agents': agents_list})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle disconnection"""
    if request.sid in OPERATORS:
        OPERATORS.discard(request.sid)
        leave_room('operators')
        log(f"⚠️ Operator disconnected: {request.sid}")
    
    # Check if it's an agent
    agent_id = None
    for aid, agent in AGENTS.items():
        if agent.get('sid') == request.sid:
            agent_id = aid
            break
    
    if agent_id:
        del AGENTS[agent_id]
        log(f"⚠️ Agent disconnected: {agent_id}")
        socketio.emit('agent_disconnected', {'agent_id': agent_id}, room='operators')

# Socket.IO Events - Agent
@socketio.on('agent_register')
def handle_agent_register(data):
    """Handle agent registration"""
    agent_id = data.get('id')
    data['sid'] = request.sid
    data['connected_at'] = time.time()
    
    AGENTS[agent_id] = data
    
    log(f"✅ Agent registered: {agent_id[:8]} | {data.get('hostname')} | {data.get('os')}")
    
    # Notify all operators
    socketio.emit('agent_connected', data, room='operators')

@socketio.on('heartbeat')
def handle_heartbeat(data):
    """Handle agent heartbeat"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        AGENTS[agent_id]['last_heartbeat'] = time.time()

@socketio.on('command_result')
def handle_command_result(data):
    """Forward command result to operators"""
    socketio.emit('command_result', data, room='operators')

@socketio.on('system_info')
def handle_system_info(data):
    """Forward system info to operators"""
    socketio.emit('system_info', data, room='operators')

@socketio.on('process_list')
def handle_process_list(data):
    """Forward process list to operators"""
    socketio.emit('process_list', data, room='operators')

@socketio.on('network_info')
def handle_network_info(data):
    """Forward network info to operators"""
    socketio.emit('network_info', data, room='operators')

@socketio.on('file_listing')
def handle_file_listing(data):
    """Forward file listing to operators"""
    socketio.emit('file_listing', data, room='operators')

# Operator Commands (forwarded to agents)
@socketio.on('execute_command')
def handle_execute_command(data):
    """Forward command execution to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('execute_command', data, room=agent_sid)
        log(f"📤 Command sent to agent {agent_id[:8]}: {data.get('command')}")

@socketio.on('get_system_info')
def handle_get_system_info(data):
    """Forward system info request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('get_system_info', data, room=agent_sid)

@socketio.on('get_processes')
def handle_get_processes(data):
    """Forward process list request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('get_processes', data, room=agent_sid)

@socketio.on('kill_process')
def handle_kill_process(data):
    """Forward process kill request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('kill_process', data, room=agent_sid)

@socketio.on('get_network_info')
def handle_get_network_info(data):
    """Forward network info request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('get_network_info', data, room=agent_sid)

@socketio.on('get_file_listing')
def handle_get_file_listing(data):
    """Forward file listing request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('get_file_listing', data, room=agent_sid)

@socketio.on('shutdown')
def handle_shutdown(data):
    """Forward shutdown request to agent"""
    agent_id = data.get('agent_id')
    if agent_id in AGENTS:
        agent_sid = AGENTS[agent_id].get('sid')
        socketio.emit('shutdown', data, room=agent_sid)
        log(f"🛑 Shutdown sent to agent {agent_id[:8]}")

def main():
    """Main entry point"""
    print("=" * 70)
    print("Pure Controller - Simple Remote Control System")
    print("=" * 70)
    print("")
    print("Features:")
    print("  ✓ Web-based UI")
    print("  ✓ Real-time agent communication")
    print("  ✓ Command execution")
    print("  ✓ Process management")
    print("  ✓ File browsing")
    print("  ✓ Network monitoring")
    print("")
    print("No privilege escalation, no UAC bypasses, no persistence")
    print("Pure Socket.IO communication only")
    print("")
    print("=" * 70)
    print("")
    print("Starting server...")
    print("")
    
    socketio.run(app, host='0.0.0.0', port=8080, debug=False)

if __name__ == '__main__':
    main()
