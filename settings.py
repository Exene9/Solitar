import tkinter as tk
import ctypes

# 1. High DPI Fix (Windows) - Prevents blurry window/wrong size
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

# 2. Get Screen Dimensions (Hidden Window)
# We create a temporary hidden window just to read the screen size
_temp_root = tk.Tk()
_temp_root.withdraw()

monitor_w = _temp_root.winfo_screenwidth()
monitor_h = _temp_root.winfo_screenheight()

_temp_root.destroy()

# 3. Define Base Design Resolution (Your original 1920x1080)
BASE_W = 1920
BASE_H = 1080

# 4. Calculate Scaling Factor
# Target 85% of screen height to ensure it fits with taskbars/title bars
_target_h = monitor_h * 0.85
SCALE = _target_h / BASE_H

# ==========================================
# DYNAMIC CONSTANTS (Calculated)
# ==========================================
# Note: We force int() here because Tkinter geometry crashes with floats

SCREEN_W = int(BASE_W * SCALE)
SCREEN_H = int(BASE_H * SCALE)

CARD_W = int(80 * SCALE)
CARD_H = int(115 * SCALE)

PADDING_X = int(15 * SCALE)
PADDING_Y = int(15 * SCALE)
TOP_OFFSET = int(50 * SCALE)
SIDE_OFFSET = int(50 * SCALE)

# ==========================================
# STATIC CONSTANTS
# ==========================================

ASSET_DIR = "Carded"

AI_STEP_DELAY_MS = 600
DFS_MAX_NODES = 200000
ASTAR_MAX_NODES = 150000