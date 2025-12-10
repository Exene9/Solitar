# main.py
import tkinter as tk
from tkinter import messagebox, scrolledtext, filedialog
import os
import datetime

import settings
import models
import game_logic as gl
import solvers
import benchmark

# Image Library Check
HAS_PIL = False
try:
    from PIL import Image, ImageTk
    HAS_PIL = True
except ImportError:
    pass

# --- Solution Guide Window ---
class StepsWindow(tk.Toplevel):
    def __init__(self, parent, moves):
        super().__init__(parent)
        self.title("Solution Guide")
        self.geometry("300x600")
        self.configure(bg="#1a452a")
        
        tk.Label(self, text="Winning Steps", font=("Arial", 14, "bold"), 
                 bg="#1a452a", fg="#f0d060").pack(pady=10)
        
        tk.Label(self, text="Follow these moves to win:", 
                 bg="#1a452a", fg="#ddd").pack(pady=(0, 5))

        self.txt_steps = scrolledtext.ScrolledText(self, bg="#222", fg="#eee", 
                                                   font=("Consolas", 10), width=30)
        self.txt_steps.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)
        
        self.populate_steps(moves)

    def populate_steps(self, moves):
        self.txt_steps.delete("1.0", tk.END)
        for i, move in enumerate(moves):
            step_str = gl.get_move_string(move)
            self.txt_steps.insert(tk.END, f"{i+1}. {step_str}\n")
        self.txt_steps.config(state=tk.DISABLED)

class BenchmarkWindow(tk.Toplevel):
    def __init__(self, parent):
        super().__init__(parent)
        self.title("Algorithm Benchmark")
        self.geometry("600x500")
        self.configure(bg="#1a452a")
        
        frame_top = tk.Frame(self, bg="#1a452a")
        frame_top.pack(pady=10, fill=tk.X, padx=10)

        tk.Label(frame_top, text="Simulations:", bg="#1a452a", fg="white").grid(row=0, column=0, padx=5, sticky="e")
        self.ent_runs = tk.Entry(frame_top, width=10)
        self.ent_runs.insert(0, "20") 
        self.ent_runs.grid(row=0, column=1, padx=5)

        tk.Label(frame_top, text="Node Limit:", bg="#1a452a", fg="white").grid(row=0, column=2, padx=5, sticky="e")
        self.ent_limit = tk.Entry(frame_top, width=10)
        self.ent_limit.insert(0, "100000") 
        self.ent_limit.grid(row=0, column=3, padx=5)

        self.btn_run = tk.Button(frame_top, text="Start Benchmark", command=self.start_benchmark, 
                                 bg="#f0d060", fg="black", font=("Arial", 10, "bold"))
        self.btn_run.grid(row=0, column=4, padx=15)

        self.txt_output = scrolledtext.ScrolledText(self, bg="#111", fg="#ddd", font=("Consolas", 9))
        self.txt_output.pack(expand=True, fill=tk.BOTH, padx=10, pady=10)

    def log(self, text):
        def _write():
            self.txt_output.insert(tk.END, text)
            self.txt_output.see(tk.END)
        self.after(0, _write)

    def on_finish(self):
        self.after(0, lambda: self.btn_run.config(state=tk.NORMAL, text="Start Benchmark"))

    def start_benchmark(self):
        try:
            runs = int(self.ent_runs.get())
            limit = int(self.ent_limit.get())
        except ValueError:
            messagebox.showerror("Error", "Please enter valid integers.")
            return

        self.txt_output.delete("1.0", tk.END)
        self.btn_run.config(state=tk.DISABLED, text="Running...")
        benchmark.run_benchmark_gui(runs, limit, self.log, self.on_finish)


class SolitaireApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Pyramid Solitaire - Modular AI")
        self.geometry(f"{settings.SCREEN_W}x{settings.SCREEN_H}")
        self.resizable(False, False)
        self.configure(bg="#225a37")

        self.deck = []
        self.pyramid = []
        self.stock = []
        self.waste = []
        self.foundation = []
        self.selected = []
        
        self.ai_moves = None
        self.ai_running = False
        self.last_algo_used = ""
        
        self.image_cache = {}
        self.back_image = None
        self.load_assets()

        self._init_gui()
        self.start_new_game()

    def load_assets(self):
        self.image_cache = {}
        if not HAS_PIL: return

        for i in range(1, 53):
            path = os.path.join(settings.ASSET_DIR, f"{i}.JPG")
            if os.path.exists(path):
                try:
                    img = Image.open(path).resize((settings.CARD_W, settings.CARD_H), Image.LANCZOS)
                    self.image_cache[i] = ImageTk.PhotoImage(img)
                except: pass
        
        back_path = os.path.join(settings.ASSET_DIR, "Back.JPG")
        if os.path.exists(back_path):
            try:
                img = Image.open(back_path).resize((settings.CARD_W, settings.CARD_H), Image.LANCZOS)
                self.back_image = ImageTk.PhotoImage(img)
            except: pass

    def _init_gui(self):
        self.sidebar = tk.Frame(self, bg="#1a452a", width=240)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        tk.Label(self.sidebar, text="PYRAMID", font=("Helvetica", 22, "bold"), bg="#1a452a", fg="#f0d060").pack(pady=(30, 5))
        tk.Label(self.sidebar, text="SOLITAIRE", font=("Helvetica", 12), bg="#1a452a", fg="#a0c0a0").pack(pady=(0, 20))

        btn_opts = {"font":("Arial", 11), "bg":"#e0e0e0", "fg":"#111", "bd":0, "cursor":"hand2"}
        tk.Button(self.sidebar, text="New Game", command=self.start_new_game, **btn_opts).pack(fill=tk.X, padx=20, pady=5, ipady=3)
        tk.Button(self.sidebar, text="Rotate Stock", command=self.user_rotate, **btn_opts).pack(fill=tk.X, padx=20, pady=5, ipady=3)
        
        tk.Frame(self.sidebar, height=2, bg="#557766").pack(fill=tk.X, padx=10, pady=15)
        
        tk.Label(self.sidebar, text="AI Solvers", font=("Arial", 10, "bold"), bg="#1a452a", fg="#ccc").pack(pady=(0,5))
        tk.Button(self.sidebar, text="Solve (DFS)", command=lambda: self.start_ai_search("DFS"), 
                  font=("Arial", 10), bg="#f0d060", fg="#222", bd=0, cursor="hand2").pack(fill=tk.X, padx=20, pady=5, ipady=5)
        tk.Button(self.sidebar, text="Solve (A*)", command=lambda: self.start_ai_search("A*"), 
                  font=("Arial", 10, "bold"), bg="#40a0ff", fg="white", bd=0, cursor="hand2").pack(fill=tk.X, padx=20, pady=5, ipady=5)

        self.btn_show_steps = tk.Button(self.sidebar, text="📖 Show Steps", command=self.open_steps_window, 
                                    font=("Arial", 10), bg="#557766", fg="#ddd", bd=0, cursor="hand2", state=tk.DISABLED)
        self.btn_show_steps.pack(fill=tk.X, padx=20, pady=5, ipady=5)

        self.btn_export = tk.Button(self.sidebar, text="💾 Export File", command=self.export_moves, 
                                    font=("Arial", 10), bg="#557766", fg="#ddd", bd=0, cursor="hand2", state=tk.DISABLED)
        self.btn_export.pack(fill=tk.X, padx=20, pady=5, ipady=5)

        tk.Frame(self.sidebar, height=2, bg="#557766").pack(fill=tk.X, padx=10, pady=15)
        tk.Button(self.sidebar, text="📊 Benchmark", command=self.open_benchmark, 
                  font=("Arial", 10), bg="#aaa", fg="#000", bd=0, cursor="hand2").pack(fill=tk.X, padx=20, pady=5, ipady=5)

        self.lbl_status = tk.Label(self.sidebar, text="Ready", bg="#1a452a", fg="white", wraplength=220)
        self.lbl_status.pack(side=tk.BOTTOM, pady=20)

        self.canvas = tk.Canvas(self, bg="#225a37", highlightthickness=0)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_click)

    def open_benchmark(self):
        BenchmarkWindow(self)
    
    def open_steps_window(self):
        if not self.ai_moves: return
        StepsWindow(self, self.ai_moves)

    def start_new_game(self):
        self.deck = models.create_deck()
        self.pyramid = self.deck[:28]
        self.stock = self.deck[28:]
        self.waste = ["**"]
        self.foundation = []
        self.selected = []
        self.ai_moves = None
        self.ai_running = False
        self.last_algo_used = ""
        
        self.btn_export.config(state=tk.DISABLED, bg="#557766")
        self.btn_show_steps.config(state=tk.DISABLED, bg="#557766")
        self.lbl_status.config(text="New Game Started")
        self.refresh_canvas()

    def refresh_canvas(self):
        self.canvas.delete("all")
        
        y = settings.TOP_OFFSET
        idx = 0
        for row in range(1, 8):
            row_width = row * settings.CARD_W + (row - 1) * settings.PADDING_X
            start_x = (self.canvas.winfo_width() - row_width) // 2
            if start_x < 0: start_x = (settings.SCREEN_W - 240 - row_width) // 2

            for col in range(row):
                if idx < len(self.pyramid):
                    c = self.pyramid[idx]
                    x = start_x + col * (settings.CARD_W + settings.PADDING_X)
                    self.draw_card_at(c, x, y, f"pyramid_{idx}")
                idx += 1
            y += settings.CARD_H + settings.PADDING_Y

        if len(self.stock) > 0 and self.stock[0] != "**":
            self.draw_card_at("back", settings.SIDE_OFFSET, settings.TOP_OFFSET, "stock")
            self.canvas.create_text(settings.SIDE_OFFSET + settings.CARD_W/2, settings.TOP_OFFSET - 15, text=f"Stock ({len(self.stock)})", fill="#ccc")
        else:
            self.draw_placeholder(settings.SIDE_OFFSET, settings.TOP_OFFSET, "stock")
            self.canvas.create_text(settings.SIDE_OFFSET + settings.CARD_W/2, settings.TOP_OFFSET - 15, text="Empty", fill="#ccc")

        if "stock_pile" in self.selected:
            x, y = settings.SIDE_OFFSET, settings.TOP_OFFSET
            self.canvas.create_rectangle(x-3, y-3, x+settings.CARD_W+3, y+settings.CARD_H+3, 
                                         outline="yellow", width=3, tags=("highlight",))

        waste_x = settings.SIDE_OFFSET + settings.CARD_W + 30
        if len(self.waste) > 0 and isinstance(self.waste[0], models.Card):
            self.draw_card_at(self.waste[0], waste_x, settings.TOP_OFFSET, "waste")
        else:
            self.draw_placeholder(waste_x, settings.TOP_OFFSET, "waste")

    def draw_card_at(self, card, x, y, tag):
        if card == "**": return 
        
        is_sel = (card in self.selected)
        
        if card == "back":
            if self.back_image:
                self.canvas.create_image(x, y, image=self.back_image, anchor="nw", tags=(tag,))
            else:
                self.canvas.create_rectangle(x, y, x+settings.CARD_W, y+settings.CARD_H, fill="#406080", outline="white", tags=(tag,))
            return

        img = self.image_cache.get(card.number) if HAS_PIL else None
        
        if is_sel:
            self.canvas.create_rectangle(x-3, y-3, x+settings.CARD_W+3, y+settings.CARD_H+3, fill="yellow", outline="")

        if img:
            self.canvas.create_image(x, y, image=img, anchor="nw", tags=(tag,))
        else:
            self.canvas.create_rectangle(x, y, x+settings.CARD_W, y+settings.CARD_H, fill="white", outline="#111", tags=(tag,))
            color = card.get_color()
            self.canvas.create_text(x+10, y+15, text=card.get_display_rank(), fill=color, font=("Arial", 12, "bold"))
            self.canvas.create_text(x+settings.CARD_W/2, y+settings.CARD_H/2, text=card.get_suit_symbol(), fill=color, font=("Arial", 28))

    def draw_placeholder(self, x, y, tag):
        self.canvas.create_rectangle(x, y, x+settings.CARD_W, y+settings.CARD_H, outline="#3a6f50", width=2, tags=(tag,))

    def user_rotate(self):
        if self.ai_running: return
        self.stock, self.waste = gl.stock_rotate(self.stock, self.waste)
        self.lbl_status.config(text="Stock Rotated")
        self.refresh_canvas()

    def on_click(self, event):
        if self.ai_running: return

        x, y = event.x, event.y
        
        # Stock (Rotate)
        if settings.SIDE_OFFSET <= x <= settings.SIDE_OFFSET+settings.CARD_W and settings.TOP_OFFSET <= y <= settings.TOP_OFFSET+settings.CARD_H:
            self.user_rotate()
            return

        # Waste
        w_x = settings.SIDE_OFFSET + settings.CARD_W + 30
        if w_x <= x <= w_x+settings.CARD_W and settings.TOP_OFFSET <= y <= settings.TOP_OFFSET+settings.CARD_H:
            if len(self.waste) > 0 and isinstance(self.waste[0], models.Card):
                self.handle_card_select(self.waste[0])
            return

        # Pyramid
        card = self.get_pyramid_card_at(x, y)
        if card:
            acc = gl.get_accessible_cards(self.pyramid, self.stock, self.waste)
            if card in acc:
                self.handle_card_select(card)
            else:
                self.lbl_status.config(text="Card Blocked", fg="#ffaaaa")

    def get_pyramid_card_at(self, mx, my):
        y = settings.TOP_OFFSET
        idx = 0
        for row in range(1, 8):
            row_width = row * settings.CARD_W + (row - 1) * settings.PADDING_X
            start_x = (self.canvas.winfo_width() - row_width) // 2
            if start_x < 0: start_x = (settings.SCREEN_W - 240 - row_width) // 2

            for col in range(row):
                if idx < len(self.pyramid):
                    c = self.pyramid[idx]
                    if c != "**":
                        cx = start_x + col * (settings.CARD_W + settings.PADDING_X)
                        if cx <= mx <= cx+settings.CARD_W and y <= my <= y+settings.CARD_H:
                            return c
                idx += 1
            y += settings.CARD_H + settings.PADDING_Y
        return None

    def handle_card_select(self, card):
        # Toggle Selection
        if card in self.selected:
            self.selected.remove(card)
            self.lbl_status.config(text="Deselected")
        else:
            self.selected.append(card)
            
            # 1. King (Single Remove)
            if gl.is_king(card):
                self.pyramid, self.stock, self.waste, self.foundation = gl.removeCards_obj(
                    card, "none", self.pyramid, self.stock, self.waste, self.foundation
                )
                self.selected.clear()
                self.lbl_status.config(text=f"Removed King {card.name()}")
            
            # 2. Pair Logic
            elif len(self.selected) == 2:
                a, b = self.selected
                
                # --- NEW VALIDATION CHECK ---
                if not gl.is_valid_source_pair(a, b, self.pyramid):
                    self.lbl_status.config(text="Invalid: Stock & Waste cannot match!", fg="#ff4444")
                    self.selected.clear()
                else:
                    if a.rank + b.rank == 13:
                        self.pyramid, self.stock, self.waste, self.foundation = gl.removeCards_obj(
                            a, b, self.pyramid, self.stock, self.waste, self.foundation
                        )
                        self.lbl_status.config(text=f"Matched {a.name()} & {b.name()}")
                    else:
                        self.lbl_status.config(text="Sum is not 13", fg="#ffaaaa")
                    self.selected.clear()
        
        self.refresh_canvas()

    def start_ai_search(self, algo_type):
        if self.ai_running: return
        self.lbl_status.config(text=f"{algo_type} Searching...", fg="#ffff00")
        self.update()

        sol = None
        if algo_type == "DFS":
            sol = solvers.find_solution_dfs(self.pyramid, self.stock, self.waste, self.foundation)
        elif algo_type == "A*":
            sol = solvers.find_solution_astar(self.pyramid, self.stock, self.waste, self.foundation)
        
        if not sol:
            messagebox.showinfo("AI", f"No solution found via {algo_type}.")
            self.lbl_status.config(text="No Solution", fg="#ffaaaa")
        else:
            self.ai_moves = sol
            self.last_algo_used = algo_type
            
            self.btn_export.config(state=tk.NORMAL, bg="#f0d060", fg="black")
            self.btn_show_steps.config(state=tk.NORMAL, bg="#f0d060", fg="black")

            ans = messagebox.askyesno(
                "AI Success", 
                f"{algo_type} found solution in {len(sol)} moves.\n\n"
                "• Click YES to watch the AI play it.\n"
                "• Click NO to play it yourself (Use 'Show Steps')."
            )
            
            if ans:
                self.ai_running = True
                self.lbl_status.config(text="AI Executing...", fg="#ffff00")
                self.execute_ai_step(0)
            else:
                self.lbl_status.config(text="Solution Ready. Click 'Show Steps'.")

    def export_moves(self):
        if not self.ai_moves: return

        filename = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt"), ("All Files", "*.*")],
            title="Save Solution As"
        )
        if not filename: return 

        try:
            with open(filename, "w") as f:
                f.write(f"Pyramid Solitaire Solution\n")
                f.write(f"Date: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"Algorithm: {self.last_algo_used}\n")
                f.write(f"Total Moves: {len(self.ai_moves)}\n")
                f.write("-" * 40 + "\n\n")
                for i, move in enumerate(self.ai_moves):
                    txt = gl.get_move_string(move)
                    f.write(f"Step {i+1}: {txt}\n")
                f.write("\n" + "-" * 40 + "\n")
                f.write("End of Solution\n")
            messagebox.showinfo("Export", f"Successfully saved to:\n{filename}")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to save file:\n{e}")

    def execute_ai_step(self, index):
        if not self.ai_running: return
        if index >= len(self.ai_moves):
            self.ai_running = False
            self.lbl_status.config(text="AI DONE - CLEARED", fg="#aaffaa")
            return

        move = self.ai_moves[index]
        txt = gl.get_move_string(move)
        self.lbl_status.config(text=f"Step {index+1}/{len(self.ai_moves)}: {txt}")

        m_type = move[0]
        self.selected = []

        if m_type == "rotate":
            self.selected.append("stock_pile") 
        elif m_type == "king":
            c = self.find_card(move[1])
            if c: self.selected.append(c)
        elif m_type == "pair":
            c1 = self.find_card(move[1])
            c2 = self.find_card(move[2])
            if c1: self.selected.append(c1)
            if c2: self.selected.append(c2)

        self.refresh_canvas()
        delay = settings.AI_STEP_DELAY_MS // 2
        self.after(delay, lambda: self.finalize_ai_step(index, move))

    def finalize_ai_step(self, index, move):
        if not self.ai_running: return
        
        m_type = move[0]
        
        if m_type == "rotate":
            self.stock, self.waste = gl.stock_rotate(self.stock, self.waste)
        elif m_type == "king":
            c = self.find_card(move[1])
            if c:
                self.pyramid, self.stock, self.waste, self.foundation = gl.removeCards_obj(
                    c, "none", self.pyramid, self.stock, self.waste, self.foundation
                )
        elif m_type == "pair":
            c1 = self.find_card(move[1])
            c2 = self.find_card(move[2])
            if c1 and c2:
                self.pyramid, self.stock, self.waste, self.foundation = gl.removeCards_obj(
                    c1, c2, self.pyramid, self.stock, self.waste, self.foundation
                )

        self.selected = []
        self.refresh_canvas()
        delay = settings.AI_STEP_DELAY_MS // 2
        self.after(delay, lambda: self.execute_ai_step(index+1))

    def find_card(self, num):
        all_cards = self.pyramid + self.stock + self.waste
        for x in all_cards:
            if isinstance(x, models.Card) and x.number == num:
                return x
        return None

if __name__ == "__main__":
    app = SolitaireApp()
    app.mainloop()