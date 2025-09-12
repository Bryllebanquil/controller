# Deployment Guide for Render

## Changes Made for Render Deployment

### 1. Fixed PyAudio Dependency Issue
- **Problem**: PyAudio was causing build failures because it requires PortAudio development libraries that aren't available in Render's build environment
- **Solution**: Removed PyAudio from `requirements.txt` since it's not actually used in the controller code
- **Note**: The controller uses `sounddevice` for Linux audio functionality instead

### 2. Updated Flask Configuration
- Modified `controller.py` to use the `PORT` environment variable provided by Render
- Changed from hardcoded port 8080 to `int(os.environ.get("PORT", 8080))`

### 3. Added System Dependencies
- Created `Aptfile` with necessary system libraries for OpenCV, pygame, and audio packages
- Includes libraries for GUI operations that may be needed by connected agents

### 4. Created Render Configuration
- Added `render.yaml` with proper build and start commands
- Added `Procfile` as alternative deployment method
- Set environment variables for headless operation

## Deployment Steps

### Option 1: Using render.yaml (Recommended)
1. Push your code to GitHub
2. Connect your GitHub repository to Render
3. Render will automatically detect the `render.yaml` file
4. The service will build and deploy automatically

### Option 2: Manual Configuration
1. Create a new Web Service on Render
2. Connect your GitHub repository
3. Use these settings:
   - **Build Command**: `pip install --upgrade pip && pip install -r requirements.txt`
   - **Start Command**: `python controller.py`
   - **Environment**: Python 3.13.4

## Environment Variables
The following environment variables are automatically set:
- `PORT`: Render assigns this automatically
- `DISPLAY`: Set to ":99" for headless GUI operations
- `PYTHONUNBUFFERED`: Set to "1" for better logging

## Important Notes

### Security Considerations
- The application runs with `debug=False` for production security
- The reverse shell server starts on port 9999 - ensure this is properly secured
- Consider adding authentication for production use

### Architecture
- This is a **controller** application that manages connected agents
- The GUI-related packages (opencv-python, pygame, pynput, etc.) are for the agents that connect to this controller
- The controller itself is a web-based dashboard accessible via browser

### Troubleshooting
1. **Build Failures**: Check that all system dependencies in `Aptfile` are properly installed
2. **Port Issues**: Render automatically assigns the PORT environment variable
3. **GUI Errors**: The DISPLAY environment variable is set for headless operation

## Testing Locally
To test the deployment configuration locally:
```bash
export PORT=8080
export DISPLAY=:99
python controller.py
```

## Post-Deployment
1. Access your application at the Render-provided URL
2. The Neural Control Hub dashboard should be accessible
3. Agents can connect to the controller using the public URL