# Cursor Flickering Fix - Technical Analysis & Solutions

## Root Causes Identified

### 1. **Timing Desynchronization** (CRITICAL)
   - **Problem**: Cursor position captured at different time than frame was encoded
   - **Impact**: Creates lag and positional mismatch visible as jitter
   - **Solution**: Synchronized cursor capture with frame processing by always caching position

### 2. **Deadzone Too Aggressive**
   - **Problem**: 2-pixel deadzone caused cursor to "stick" during slow movement
   - **Impact**: Cursor appears frozen during precise mouse movements
   - **Old Value**: `_cursor_deadzone = 2` pixels
   - **New Value**: `_cursor_deadzone = 0.5` pixels (still filters noise, more responsive)

### 3. **Smoothing Alpha Too Conservative** 
   - **Problem**: Low smoothing factor (0.4) gave too much weight to old positions
   - **Impact**: Cursor lags behind actual movement
   - **Old Value**: `_cursor_smoothing_alpha = 0.4` (70% old, 30% new)
   - **New Value**: `_cursor_smoothing_alpha = 0.7` (70% new, 30% old - more responsive)

### 4. **Cache Accumulation Issue**
   - **Problem**: Cache never reset between frames, mixing stale and current data
   - **Impact**: Smoothing included data from multiple different frames
   - **Solution**: Automatically pop oldest position when cache reaches size limit
   - **Added Logic**: Velocity tracking to predict smooth motion

### 5. **No Motion Prediction**
   - **Problem**: Cursor smoothed but not predicted, causing visible lag
   - **Solution**: Added velocity calculation and blending for predictive smoothing
   - **Implementation**: Two-position exponential weighted average with velocity data

### 6. **Visual Rendering Overhead**
   - **Problem**: Large double-circle outline (12px + 8px) created visible flutter
   - **Impact**: Multiple layers changing visibility frame-to-frame
   - **Solution**: Single 6px solid circle + 2px center dot (simpler = less flicker)

## Changes Made to `client.py`

### Global Variables Updated (Lines 21509-21518)
```python
# Before
_cursor_deadzone = 2
_cursor_smoothing_alpha = 0.4

# After
_cursor_deadzone = 0.5                    # More responsive
_cursor_smoothing_alpha = 0.7             # Higher = more recent data weighted
_cursor_velocity = [0, 0]                 # NEW: Velocity tracking
_cursor_last_raw_pos = None               # NEW: For velocity calculation
_cursor_frame_sync = None                 # NEW: Frame timestamp sync
```

### Configuration Updated (Lines 2609-2613)
```python
# Before
CURSOR_SMOOTHING_FRAMES = 8  # Increased cache
CURSOR_CACHE_SIZE = 8

# After  
CURSOR_SMOOTHING_FRAMES = 4  # Reduced for faster response
CURSOR_CACHE_SIZE = 5        # Smaller = less latency
```

### Function: `cache_cursor_position()` (NEW LOGIC)
- **Now tracks velocity** between frames for motion prediction
- **Automatic cache clearing** to prevent stale data accumulation
- **Separate raw position tracking** for velocity calculations
- **Always caches** for data collection (no deadzone filtering on cache)

### Function: `get_smoothed_cursor_position()` (IMPROVED)
- **Simplified logic** - focus on most recent 2 positions
- **Velocity-aware smoothing** - blends Kalman-like exponential average with velocity
- **Eliminates complex weighting** - previous algorithm was over-complicated
- **Better motion prediction** - anticipates cursor direction

### Function: `draw_cursor_on_frame()` (OPTIMIZED)
- **Before**: Double circles (12px outline + 8px filled) = visual noise
- **After**: Single 6px circle + 2px center = minimal visual footprint
- **Impact**: Reduced visual flutter from rendering changes

### Function: `screen_capture_worker()` (ENHANCED)
- **Always caches cursor** regardless of smoothing setting
- **Added velocity tracking** to enable motion prediction
- **Improved comment documentation**

## Expected Improvements

1. **Smoother Motion** - Velocity prediction fills gaps between frames
2. **Faster Response** - 70% weight on new data = quicker to cursor changes
3. **Reduced Jitter** - Smaller visual indicator + better caching
4. **Lower Latency** - Smaller cache (5 vs 8) = less accumulated delay
5. **Stable Slow Movement** - Lower deadzone (0.5 vs 2) catches subtle moves

## Testing Recommendations

1. **Rapid cursor movement** - Should follow smoothly without lag
2. **Slow/precise movement** - Should track consistently without sticking
3. **Stationary cursor** - Should remain stable without visual flutter
4. **Edge cases** - Moving cursor off/on screen edges

## Fallback Options

If flickering persists, try these environment variable overrides:

```bash
# More aggressive smoothing (very smooth, slightly more latency)
set CURSOR_SMOOTHING_FRAMES=6

# Less aggressive smoothing (faster response, less smooth)
set CURSOR_SMOOTHING_FRAMES=3

# Disable smoothing entirely (raw position only)
set CURSOR_SMOOTHING=0

# Disable cursor drawing (if performance is critical)
set STREAM_CURSOR_EMIT=0
```

## Technical Notes

- **Exponential Weighted Average Formula**: `smoothed = (α × new) + ((1-α) × old)`
  - α = 0.7: New position weighted 70%, previous 30%
  - Creates natural motion interpolation
  
- **Velocity Tracking**: `v = current_pos - last_raw_pos`
  - Stored between cache updates
  - Used to weight smoothing blend
  
- **Cache Size Trade-off**:
  - Larger = smoother but higher latency
  - Smaller = responsive but noisier
  - Optimal: 4-5 positions at 30+ FPS = ~133-166ms of history
