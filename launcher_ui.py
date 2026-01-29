import tkinter as tk
from tkinter import ttk, messagebox
from tkinter.scrolledtext import ScrolledText
import os
import subprocess
import sys
import threading
import queue

# --- CONFIG & ASSETS ---
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
SCRIPT_PATH = os.path.join(REPO_DIR, "governing_files", "drug_surfactant_bo.py")

# Colors (VS Code Dark Theme inspired)
BG_COLOR = "#1e1e1e"        # Main Background
PANEL_COLOR = "#252526"     # Group Background
ACCENT_COLOR = "#007acc"    # Blue Accent
TEXT_COLOR = "#d4d4d4"      # Light Grey Text
SUBTEXT_COLOR = "#858585"   # Darker Grey Text
SUCCESS_COLOR = "#4CAF50"   # Green
ERROR_COLOR = "#f44336"     # Red

font_main = ("Segoe UI", 10)
font_bold = ("Segoe UI", 10, "bold")
font_head = ("Segoe UI", 14, "bold")
font_mono = ("Consolas", 9)

class ModernLauncher(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Drug Surfactant • Auto-Lab Controller")
        self.geometry("800x950")  # Increased size for console
        self.configure(bg=BG_COLOR)
        
        # --- VARIABLES ---
        self.smoke_test_var = tk.BooleanVar(value=False)
        self.exp_name_var = tk.StringVar(value="20261129_test")
        
        # Hardware Defaults
        self.plate_well_var = tk.StringVar()
        self.deep_well_var = tk.StringVar()
        self.rack_id_var = tk.StringVar(value="0")
        self.tip_1000_var = tk.StringVar(value="A1")
        self.tip_50_var = tk.StringVar(value="A1")

        # Param Defaults
        self.num_batches_var = tk.StringVar(value="5")
        self.trials_per_iter_var = tk.StringVar(value="2")
        self.replicates_var = tk.StringVar(value="2")
        self.surf_vol_red_var = tk.StringVar(value="20")
        self.drug_choices_var = tk.StringVar(value="IBP")
        self.absorbance_var = tk.StringVar(value="0.06")

        self.running_process = None
        self.log_queue = queue.Queue()

        self.setup_styles()
        self.build_ui()
        self.process_logs() # Start log loop
        
    def setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        
        # Frames
        style.configure("Card.TFrame", background=PANEL_COLOR, relief="flat")
        
        # Labels
        style.configure("TLabel", background=PANEL_COLOR, foreground=TEXT_COLOR, font=font_main)
        style.configure("Header.TLabel", background=BG_COLOR, foreground="white", font=font_head)
        style.configure("Sub.TLabel", background=PANEL_COLOR, foreground=SUBTEXT_COLOR, font=("Segoe UI", 9))
        
        # Checkbutton
        style.configure("TCheckbutton", background=PANEL_COLOR, foreground="white", font=font_bold)
        
        # Entries
        style.configure("TEntry", fieldbackground="#3c3c3c", foreground="white", insertcolor="white", borderwidth=0)
        style.map("TEntry", fieldbackground=[("active", "#454545")])
        
        # Buttons
        style.configure("Accent.TButton", 
                        background=ACCENT_COLOR, 
                        foreground="white", 
                        font=("Segoe UI", 12, "bold"),
                        borderwidth=0, focuscolor=ACCENT_COLOR)
        style.map("Accent.TButton", background=[("active", "#0062a3")])
        
        style.configure("Stop.TButton", 
                        background=ERROR_COLOR, 
                        foreground="white", 
                        font=("Segoe UI", 12, "bold"),
                        borderwidth=0, focuscolor=ERROR_COLOR)
        style.map("Stop.TButton", background=[("active", "#d32f2f")])

    def build_ui(self):
        # --- HEADER ---
        header_frame = tk.Frame(self, bg=BG_COLOR, height=60)
        header_frame.pack(fill="x", padx=20, pady=(20, 10))
        tk.Label(header_frame, text="🧬 SDL-Nano Controller", bg=BG_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 18, "bold")).pack(side="left")
        
        status_frame = tk.Frame(header_frame, bg=BG_COLOR)
        status_frame.pack(side="right")
        self.status_lbl = tk.Label(status_frame, text="READY", bg=BG_COLOR, fg=SUCCESS_COLOR, font=("Segoe UI", 10, "bold"))
        self.status_lbl.pack()

        # --- SCROLLABLE CONFIG AREA ---
        # Using a panedwindow to split config and console
        paned = tk.PanedWindow(self, orient="vertical", bg=BG_COLOR, sashwidth=4, sashrelief="flat")
        paned.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Top Frame: Config
        config_frame = tk.Frame(paned, bg=BG_COLOR)
        paned.add(config_frame, minsize=400)

        # 1. MODE & TARGET
        self.create_card(config_frame, "🎯 Execution Target", [
            ("checkbox", "Simulation Mode (Smoke Test)", self.smoke_test_var),
            ("label", "Experiment Folder Name:", None),
            ("entry", self.exp_name_var, None),
        ])

        # 2. HARDWARE STATE
        self.create_card(config_frame, "🤖 Robot Hardware State", [
            ("row", [
                ("Start Plate Well", self.plate_well_var),
                ("Start Deep Well", self.deep_well_var)
            ]),
            ("separator", None, None),
            ("label", "Tip Tracking (Overrides Auto-Save)", None),
            ("row", [
                ("1000uL Rack", self.rack_id_var),
                ("1000uL Tip", self.tip_1000_var),
                ("50uL Tip", self.tip_50_var)
            ])
        ])

        # 3. OPTIMIZATION PARAMS
        self.create_card(config_frame, "🧪 Optimization Parameters", [
            ("row", [
                ("Batches", self.num_batches_var),
                ("Trials/Iter", self.trials_per_iter_var)
            ]),
            ("row", [
                ("Replicates", self.replicates_var),
                ("Abs. Thresh", self.absorbance_var)
            ]),
            ("row", [
                ("Surf. Vol Red.", self.surf_vol_red_var),
                ("Drugs", self.drug_choices_var)
            ])
        ])

        # Bottom Frame: Console
        console_frame = tk.Frame(paned, bg=BG_COLOR)
        paned.add(console_frame, minsize=200)
        
        tk.Label(console_frame, text="TERMINAL OUTPUT", bg=BG_COLOR, fg=SUBTEXT_COLOR, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(5,0))
        
        self.console = ScrolledText(console_frame, bg="#111", fg=TEXT_COLOR, font=font_mono, borderwidth=0, highlightthickness=0)
        self.console.pack(fill="both", expand=True, pady=5)
        self.console.tag_config("stderr", foreground="#ff6b6b")
        self.console.tag_config("info", foreground="#4ec9b0")

        # --- FOOTER BUTTONS ---
        btn_frame = tk.Frame(self, bg=BG_COLOR, pady=20)
        btn_frame.pack(fill="x", padx=20)
        
        self.launch_btn = ttk.Button(btn_frame, text="🚀 LAUNCH EXPERIMENT", style="Accent.TButton", command=self.launch_experiment)
        self.launch_btn.pack(side="left", fill="x", expand=True, padx=(0, 10), ipady=8)

        self.stop_btn = ttk.Button(btn_frame, text="🛑 STOP", style="Stop.TButton", command=self.stop_experiment, state="disabled")
        self.stop_btn.pack(side="left", fill="x", expand=True, padx=(10, 0), ipady=8)

    def create_card(self, parent, title, items):
        """Helper to create a unified 'Card' style group"""
        card = ttk.Frame(parent, style="Card.TFrame", padding=15)
        card.pack(fill="x", pady=10)
        
        # Card Title
        tk.Label(card, text=title.upper(), bg=PANEL_COLOR, fg=ACCENT_COLOR, font=("Segoe UI", 9, "bold")).pack(anchor="w", pady=(0, 10))
        
        for item in items:
            itype = item[0]
            
            if itype == "checkbox":
                ttk.Checkbutton(card, text=item[1], variable=item[2]).pack(anchor="w", pady=2)
                
            elif itype == "label":
                ttk.Label(card, text=item[1], style="Sub.TLabel").pack(anchor="w", pady=(5,0))
                
            elif itype == "entry":
                ttk.Entry(card, textvariable=item[1]).pack(fill="x", pady=2)
                
            elif itype == "row":
                row_f = tk.Frame(card, bg=PANEL_COLOR)
                row_f.pack(fill="x", pady=5)
                widgets = item[1]
                for i, (lbl, var) in enumerate(widgets):
                    f = tk.Frame(row_f, bg=PANEL_COLOR)
                    f.pack(side="left", fill="x", expand=True, padx=(0 if i==0 else 10, 0))
                    ttk.Label(f, text=lbl, style="Sub.TLabel").pack(anchor="w")
                    ttk.Entry(f, textvariable=var, width=8).pack(fill="x")
                    
            elif itype == "separator":
                tk.Frame(card, height=1, bg="#444").pack(fill="x", pady=8)

    def log(self, msg, tag=None):
        self.log_queue.put((msg, tag))

    def process_logs(self):
        while not self.log_queue.empty():
            msg, tag = self.log_queue.get()
            self.console.insert("end", msg, tag)
            self.console.see("end")
        self.after(100, self.process_logs)

    def launch_experiment(self):
        if self.running_process:
            return

        # 1. Harvest Env
        env = os.environ.copy()
        
        if self.smoke_test_var.get():
            env["SMOKE_TEST"] = "1"
        else:
            env["SMOKE_TEST"] = "0"
            folder = self.exp_name_var.get().strip()
            if not folder:
                messagebox.showerror("Error", "Experiment Folder Name is required!")
                return
            env["EXP_FOLDER_NAME"] = folder

        # Hardware
        env["START_PLATE_WELL"] = self.plate_well_var.get().strip()
        env["START_DEEP_WELL"] = self.deep_well_var.get().strip()
        env["TIP_RACK_ID"] = self.rack_id_var.get().strip()
        env["TIP_WELL_1000"] = self.tip_1000_var.get().strip()
        env["TIP_WELL_50"] = self.tip_50_var.get().strip()
        
        # Params
        env["NUM_BATCHES"] = self.num_batches_var.get().strip()
        env["TRIALS_PER_ITERATION"] = self.trials_per_iter_var.get().strip()
        env["REPLICATES"] = self.replicates_var.get().strip()
        env["SURFACTANT_VOL_REDUCTION"] = self.surf_vol_red_var.get().strip()
        env["DRUG_CHOICES"] = self.drug_choices_var.get().strip()
        env["ABSORBANCE_THRESHOLD"] = self.absorbance_var.get().strip()
        
        # Configure UI State
        self.launch_btn.config(state="disabled")
        self.stop_btn.config(state="normal")
        self.status_lbl.config(text="RUNNING...", fg="#FFA500")
        self.console.delete(1.0, "end")
        self.log(f"--- Starting Experiment: {env.get('EXP_FOLDER_NAME', 'Smoke Test')} ---\n", "info")

        # 2. Start Thread
        thread = threading.Thread(target=self.run_process, args=(env,))
        thread.start()

    def run_process(self, env):
        # We need to unbuffer output so it appears immediately
        env["PYTHONUNBUFFERED"] = "1"
        
        try:
            # We'll just read stdout line by line. Stderr is tricky in same loop.
            # Merging stderr to stdout for simplicity
            self.running_process = subprocess.Popen(
                [sys.executable, SCRIPT_PATH],
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr into stdout
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            for line in iter(self.running_process.stdout.readline, ''):
                if line:
                    self.log(line)
            
            rc = self.running_process.wait()
            if rc == 0:
                self.log(f"\n--- Process Finished Successfully (Exit Code {rc}) ---\n", "info")
            else:
                self.log(f"\n--- Process Failed (Exit Code {rc}) ---\n", "stderr")

        except Exception as e:
            self.log(f"Launch Error: {e}\n", "stderr")
        
        finally:
            self.running_process = None
            self.after(0, self.reset_ui_state)

    def reset_ui_state(self):
        self.launch_btn.config(state="normal")
        self.stop_btn.config(state="disabled")
        self.status_lbl.config(text="READY", fg=SUCCESS_COLOR)

    def stop_experiment(self):
        if self.running_process:
            self.log("\n--- Stopping Process... ---\n", "stderr")
            self.running_process.terminate()

if __name__ == "__main__":
    app = ModernLauncher()
    app.mainloop()
