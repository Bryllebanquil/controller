import aiortc
import inspect
from aiortc import MediaStreamTrack

print(f"aiortc version: {aiortc.__version__}")
print(f"MediaStreamTrack attributes: {dir(MediaStreamTrack)}")
if hasattr(MediaStreamTrack, 'next_timestamp'):
    print("next_timestamp exists")
else:
    print("next_timestamp DOES NOT exist")
