# rthook.py - Runtime hooks for PyInstaller
import os
import sys
import warnings

# Fix for OpenSSL on Windows
if sys.platform == 'win32':
    os.environ['PATH'] = sys._MEIPASS + os.pathsep + os.environ['PATH']

# Fix for OpenCV
try:
    import cv2
    # Set OpenCV to use bundled files
    cv2_base_path = os.path.join(sys._MEIPASS, 'cv2')
    if os.path.exists(cv2_base_path):
        os.environ['OPENCV_DATA_PATH'] = cv2_base_path
except ImportError:
    pass

# Fix for multiprocessing on Windows
if sys.platform == 'win32':
    import multiprocessing
    multiprocessing.freeze_support()

# Suppress unnecessary warnings
warnings.filterwarnings('ignore', category=DeprecationWarning)
warnings.filterwarnings('ignore', category=RuntimeWarning)

print(f"[RUNTIME] Application initialized in {sys._MEIPASS}")