# Streaming Optimizations for Real-Time Monitoring

## Overview
The streaming system has been optimized to send pictures every 0.5 seconds (2 FPS) for improved real-time monitoring while maintaining good image quality and reducing bandwidth usage.

## Changes Made

### 1. Controller.py Optimizations

#### Frame Generation Functions
- **generate_video_frames()**: Changed sleep interval from 0.05s to 0.5s (FRAME_INTERVAL)
- **generate_camera_frames()**: Changed sleep interval from 0.05s to 0.5s (FRAME_INTERVAL)
- Added global FRAME_INTERVAL constant set to 0.5 seconds for easy configuration

#### Performance Improvements
- Reduced server-side polling frequency to match 2 FPS target
- Added documentation explaining the 0.5-second optimization
- Consistent timing across all streaming endpoints

### 2. Main.py (Agent) Optimizations

#### Screen Streaming (_stream_screen_fallback)
- **Target FPS**: Changed from 30 FPS to 2 FPS (0.5-second intervals)
- **Frame Time**: Now 0.5 seconds per frame instead of ~33ms
- **Image Quality**: Maintained at 85% JPEG quality for clear monitoring
- **Request Timeout**: Optimized to 0.5 seconds for better responsiveness

#### Camera Streaming (stream_camera)
- **Camera FPS**: Set camera capture to 2 FPS instead of 30 FPS
- **Sleep Interval**: Changed from time.sleep(1/30) to time.sleep(0.5)
- **Frame Counter**: Adjusted logging frequency for 2 FPS monitoring
- **Request Timeout**: Optimized to 0.5 seconds

#### Audio Streaming (stream_audio)
- **Request Timeout**: Reduced from 1.0s to 0.5s for better synchronization

#### High-Performance Capture Class
- **Default FPS**: Changed from 60 FPS to 2 FPS for real-time monitoring
- **Documentation**: Updated to reflect optimization for monitoring use case

### 3. Additional Optimizations

#### Timing Precision
- Maintained precise frame timing with sleep calculations
- Added frame time calculations for consistent 0.5-second intervals
- Preserved change detection to avoid sending duplicate frames

#### Error Handling
- Maintained robust error handling and retry logic
- Kept timeout values optimized for 0.5-second intervals
- Preserved connection resilience

#### Image Quality
- Maintained high JPEG quality (85%) for clear monitoring
- Kept optimal resolution settings (1280x720 for screen, 640x480 for camera)
- Preserved compression optimizations

## Benefits of 0.5-Second Intervals

### 1. Real-Time Monitoring
- Perfect balance between responsiveness and system resources
- Suitable for monitoring applications where immediate response isn't critical
- Reduces bandwidth usage compared to high-FPS streaming

### 2. Performance Benefits
- Lower CPU usage on both agent and controller
- Reduced network bandwidth requirements
- Better system stability for long-running monitoring sessions

### 3. Quality Benefits
- Higher image quality possible with reduced frame rate
- More consistent timing and synchronization
- Better compatibility with slower network connections

## Technical Specifications

### Frame Rates
- **Screen Streaming**: 2 FPS (0.5-second intervals)
- **Camera Streaming**: 2 FPS (0.5-second intervals)
- **Audio Streaming**: Continuous (unchanged)

### Timeouts
- **Request Timeouts**: 0.5 seconds
- **Frame Intervals**: 0.5 seconds
- **Error Retry Delays**: 5 seconds (unchanged)

### Image Settings
- **Screen Resolution**: 1280x720 (optimized)
- **Camera Resolution**: 640x480 (standard)
- **JPEG Quality**: 85% (high quality for monitoring)
- **Compression**: Optimized with progressive JPEG

## Testing

A test function `test_streaming_timing()` has been added to verify the 0.5-second intervals are working correctly. This function:
- Tests timing accuracy over a 10-second period
- Verifies actual FPS matches target FPS (2 ±0.2)
- Provides detailed timing statistics
- Confirms the optimization is working as expected

## Usage

The optimized streaming system maintains the same API and commands:
- `start-stream`: Starts screen streaming at 2 FPS
- `start-camera`: Starts camera streaming at 2 FPS
- `stop-stream` / `stop-camera`: Stops respective streams

The system automatically uses the optimized 0.5-second intervals without requiring any changes to existing code or commands.

## Future Considerations

The FRAME_INTERVAL constant in controller.py can be easily adjusted if different timing requirements are needed:
- For faster monitoring: Set to 0.25 (4 FPS) or 0.1 (10 FPS)
- For slower monitoring: Set to 1.0 (1 FPS) or 2.0 (0.5 FPS)

All streaming functions will automatically adapt to the new interval.