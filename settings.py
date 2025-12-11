import tkinter as tk
import ctypes

class Settings:
    def __init__(self):
        # 1. High DPI Fix (Windows)
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(1)
        except Exception:
            try:
                ctypes.windll.user32.SetProcessDPIAware()
            except Exception:
                pass

        # 2. Get Screen Dimensions using a temporary Tk instance
        temp_root = tk.Tk()
        temp_root.withdraw()  
        
        monitor_w = temp_root.winfo_screenwidth()
        monitor_h = temp_root.winfo_screenheight()
        
        temp_root.destroy()   

        # 3. Define Base Design Resolution (The 1920x1080 you designed for)
        base_w = 1920
        base_h = 1080

        # 4. Calculate Scaling Factor
     
        target_h = monitor_h * 0.85
        self.scale = target_h / base_h
        
    

        # 5. Calculate Final Screen Dimensions
        self.screen_w = int(base_w * self.scale)
        self.screen_h = int(base_h * self.scale)

        self.card_w = int(80 * self.scale)
        self.card_h = int(115 * self.scale)

        self.padding_x = int(15 * self.scale)
        self.padding_y = int(15 * self.scale)
        self.top_offset = int(50 * self.scale)
        self.side_offset = int(50 * self.scale)

  
        self.asset_dir = "Carded"
        # ai settings
        self.ai_step_delay_ms = 600
        self.dfs_max_nodes = 200000
        self.astar_max_nodes = 150000

