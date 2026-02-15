import asyncio
import sys
import time
import numpy as np
import av
import cv2
import mss
import pyaudio
import queue
from fractions import Fraction
from aiortc import MediaStreamTrack, RTCPeerConnection, RTCSessionDescription

def log_message(msg, level="info"):
    print(f"[{level.upper()}] {msg}")

AIORTC_AVAILABLE = True
MSS_AVAILABLE = True
CV2_AVAILABLE = True
PYAUDIO_AVAILABLE = True

class ScreenTrack(MediaStreamTrack):
    """WebRTC MediaStreamTrack for screen capture with sub-second latency."""
    
    kind = "video"

    def __init__(self, agent_id, target_fps=30, quality=85):
        super().__init__()
        self.agent_id = agent_id
        self.target_fps = target_fps
        self.quality = quality
        self.frame_interval = 1.0 / target_fps
        self.last_frame_time = 0
        self.capture = None
        self._start_time = time.time()
        self.stats = {
            'frames_sent': 0,
            'total_bytes': 0,
            'avg_latency': 0.0,
            'fps': 0.0
        }
        
        # Initialize capture backend
        if AIORTC_AVAILABLE:
            try:
                if MSS_AVAILABLE:
                    import mss
                    self.capture = mss.mss()
                elif CV2_AVAILABLE:
                    self.capture = cv2.VideoCapture(0)  # Fallback to camera if screen capture fails
                log_message(f"ScreenTrack initialized for agent {agent_id} at {target_fps} FPS")
            except Exception as e:
                log_message(f"Failed to initialize ScreenTrack: {e}", "error")

    async def next_timestamp(self):
        pts = int((time.time() - self._start_time) * 90000)
        time_base = Fraction(1, 90000)
        return pts, time_base

    async def recv(self):
        """Generate and return video frames for WebRTC streaming."""
        if not AIORTC_AVAILABLE or not self.capture:
            # Fallback to placeholder frame
            frame = av.VideoFrame.from_ndarray(
                np.zeros((480, 640, 3), dtype=np.uint8),
                format="bgr24"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame
        
        try:
            current_time = time.time()
            
            # Control frame rate
            if current_time - self.last_frame_time < self.frame_interval:
                await asyncio.sleep(0.001)  # Brief pause
                return await self.recv()
            
            # Capture screen frame
            if MSS_AVAILABLE and hasattr(self.capture, 'grab'):
                # Use mss for screen capture
                if len(self.capture.monitors) > 1:
                    monitor = self.capture.monitors[1]
                else:
                    monitor = self.capture.monitors[0]
                
                screenshot = self.capture.grab(monitor)
                img_array = np.array(screenshot)
                
                # Convert BGRA to BGR
                if img_array.shape[2] == 4:
                    img_array = img_array[:, :, :3]
                
            elif CV2_AVAILABLE and hasattr(self.capture, 'read'):
                # Fallback to OpenCV
                ret, frame = self.capture.read()
                if not ret:
                    # Generate placeholder frame
                    img_array = np.zeros((480, 640, 3), dtype=np.uint8)
                else:
                    img_array = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            else:
                # Generate placeholder frame
                img_array = np.zeros((480, 640, 3), dtype=np.uint8)
            
            # Create VideoFrame for aiortc
            frame = av.VideoFrame.from_ndarray(img_array, format="bgr24")
            frame.pts, frame.time_base = await self.next_timestamp()
            
            # Update stats
            self.stats['frames_sent'] += 1
            self.stats['fps'] = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
            self.last_frame_time = current_time
            
            return frame
            
        except Exception as e:
            log_message(f"Error in ScreenTrack.recv: {e}", "error")
            # Return placeholder frame on error
            frame = av.VideoFrame.from_ndarray(
                np.zeros((480, 640, 3), dtype=np.uint8),
                format="bgr24"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame

class AudioTrack(MediaStreamTrack):
    """WebRTC MediaStreamTrack for audio capture with low latency."""
    
    kind = "audio"
    
    def __init__(self, agent_id, sample_rate=44100, channels=1):
        super().__init__()
        self.agent_id = agent_id
        self.sample_rate = sample_rate
        self.channels = channels
        self.frame_size = 960  # 20ms at 48kHz
        self.audio_queue = queue.Queue(maxsize=100)
        self._timestamp = 0
        self.stats = {
            'audio_frames_sent': 0,
            'total_samples': 0,
            'sample_rate': sample_rate
        }
        
        # Initialize audio capture
        if AIORTC_AVAILABLE and PYAUDIO_AVAILABLE:
            try:
                self.audio = pyaudio.PyAudio()
                self.stream = self.audio.open(
                    format=pyaudio.paFloat32,
                    channels=channels,
                    rate=sample_rate,
                    input=True,
                    frames_per_buffer=self.frame_size,
                    stream_callback=self._audio_callback
                )
                self.stream.start_stream()
                log_message(f"AudioTrack initialized for agent {agent_id}")
            except Exception as e:
                    log_message(f"Failed to initialize AudioTrack: {e}", "error")
                    self.audio = None
                    self.stream = None
    
    def _audio_callback(self, in_data, frame_count, time_info, status):
        """Audio capture callback for PyAudio."""
        try:
            if not self.audio_queue.full():
                self.audio_queue.put(in_data)
        except Exception as e:
            log_message(f"Audio callback error: {e}", "error")
        return (None, pyaudio.paContinue)
    
    async def next_timestamp(self):
        pts = self._timestamp
        self._timestamp += self.frame_size
        time_base = Fraction(1, self.sample_rate)
        return pts, time_base

    async def recv(self):
        """Generate and return audio frames for WebRTC streaming."""
        if not AIORTC_AVAILABLE:
            # Fallback to silence
            frame = av.AudioFrame.from_ndarray(
                np.zeros((1, self.frame_size), dtype=np.float32), # Changed shape
                format="flt",
                layout="stereo" if self.channels == 2 else "mono"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            frame.sample_rate = self.sample_rate
            return frame
        
        try:
            # Get audio data from queue
            try:
                audio_data = self.audio_queue.get_nowait()
            except queue.Empty:
                # Generate silence if no audio data
                audio_data = np.zeros(self.frame_size * self.channels, dtype=np.float32)
            
            # Convert to numpy array
            if isinstance(audio_data, bytes):
                audio_array = np.frombuffer(audio_data, dtype=np.float32)
            else:
                audio_array = np.array(audio_data, dtype=np.float32)
            
            # Reshape for channels
            # PyAV expects (channels, samples) for planar, (samples, channels) for packed?
            # Error said: Expected packed array.shape[0] to equal 1 but got 960
            # This implies it wants (1, 960) for mono packed?
            # Let's try (channels, samples) even for packed 'flt'.
            
            if self.channels == 2:
                audio_array = audio_array.reshape(2, -1)
            else:
                audio_array = audio_array.reshape(1, -1)
            
            # Create AudioFrame for aiortc
            frame = av.AudioFrame.from_ndarray(
                audio_array,
                format="flt",
                layout="stereo" if self.channels == 2 else "mono"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            frame.sample_rate = self.sample_rate
            
            # Update stats
            self.stats['audio_frames_sent'] += 1
            self.stats['total_samples'] += audio_array.shape[1]
            
            return frame
            
        except Exception as e:
            log_message(f"Error in AudioTrack.recv: {e}", "error")
            # Return silence on error
            frame = av.AudioFrame.from_ndarray(
            np.zeros((1, self.frame_size), dtype=np.float32), # Changed shape
            format="flt",
            layout="stereo" if self.channels == 2 else "mono"
        )
        frame.pts, frame.time_base = await self.next_timestamp()
        frame.sample_rate = self.sample_rate
        return frame

class CameraTrack(MediaStreamTrack):
    """WebRTC MediaStreamTrack for camera capture with low latency."""
    
    kind = "video"
    
    def __init__(self, agent_id, camera_index=0, target_fps=30, quality=85):
        super().__init__()
        self.agent_id = agent_id
        self.camera_index = camera_index
        self.target_fps = target_fps
        self.quality = quality
        self.frame_interval = 1.0 / target_fps
        self.last_frame_time = 0
        self.capture = None
        self._start_time = time.time()
        self.stats = {
            'frames_sent': 0,
            'total_bytes': 0,
            'avg_latency': 0.0,
            'fps': 0.0
        }
        
        # Initialize camera capture
        if AIORTC_AVAILABLE and CV2_AVAILABLE:
            try:
                self.capture = cv2.VideoCapture(camera_index)
                if not self.capture.isOpened():
                    log_message(f"Failed to open camera {camera_index}", "warning")
                    self.capture = None
                else:
                    # Set camera properties for low latency
                    self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    self.capture.set(cv2.CAP_PROP_FPS, target_fps)
                    self.capture.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Minimize buffering
                    log_message(f"CameraTrack initialized for agent {agent_id} at {target_fps} FPS")
            except Exception as e:
                log_message(f"Failed to initialize CameraTrack: {e}", "error")

    async def next_timestamp(self):
        pts = int((time.time() - self._start_time) * 90000)
        time_base = Fraction(1, 90000)
        return pts, time_base

    async def recv(self):
        """Generate and return camera frames for WebRTC streaming."""
        if not AIORTC_AVAILABLE or not self.capture:
            # Fallback to placeholder frame
            frame = av.VideoFrame.from_ndarray(
                np.zeros((480, 640, 3), dtype=np.uint8),
                format="bgr24"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame
        
        try:
            current_time = time.time()
            
            # Control frame rate
            if current_time - self.last_frame_time < self.frame_interval:
                await asyncio.sleep(0.001)  # Brief pause
                return await self.recv()
            
            # Capture camera frame
            ret, frame = self.capture.read()
            if not ret:
                # Return placeholder frame if read fails
                frame_data = np.zeros((480, 640, 3), dtype=np.uint8)
            else:
                frame_data = frame
            
            # Create VideoFrame for aiortc
            frame = av.VideoFrame.from_ndarray(frame_data, format="bgr24")
            frame.pts, frame.time_base = await self.next_timestamp()
            
            # Update stats
            self.stats['frames_sent'] += 1
            self.stats['fps'] = 1.0 / (current_time - self.last_frame_time) if self.last_frame_time > 0 else 0
            self.last_frame_time = current_time
            
            return frame
            
        except Exception as e:
            log_message(f"Error in CameraTrack.recv: {e}", "error")
            # Return placeholder frame on error
            frame = av.VideoFrame.from_ndarray(
                np.zeros((480, 640, 3), dtype=np.uint8),
                format="bgr24"
            )
            frame.pts, frame.time_base = await self.next_timestamp()
            return frame

async def test_tracks():
    print("Testing ScreenTrack...")
    try:
        screen_track = ScreenTrack("test_agent")
        frame = await screen_track.recv()
        print(f"ScreenTrack frame received: {frame.width}x{frame.height}")
    except Exception as e:
        print(f"ScreenTrack failed: {e}")

    print("\nTesting AudioTrack...")
    try:
        audio_track = AudioTrack("test_agent")
        if audio_track.audio:
            frame = await audio_track.recv()
            print(f"AudioTrack frame received: {frame.sample_rate}Hz, {frame.layout.name}")
        else:
            print("AudioTrack initialization failed (no device?)")
    except Exception as e:
        print(f"AudioTrack failed: {e}")

    print("\nTesting CameraTrack...")
    try:
        camera_track = CameraTrack("test_agent")
        if camera_track.capture:
            frame = await camera_track.recv()
            print(f"CameraTrack frame received: {frame.width}x{frame.height}")
        else:
            print("CameraTrack initialization failed (no device?)")
    except Exception as e:
        print(f"CameraTrack failed: {e}")

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_tracks())
    loop.close()
