import customtkinter as ctk
from pynput import keyboard, mouse
import threading
import time
import json
import os

# =================== CONFIG ===================
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")
CONFIG_FILE = "autoclicker_config.json"

class AutoClickerApp:
    def __init__(self):
        self.window = ctk.CTk()
        self.window.geometry("350x500")
        self.window.title("LilNerox Auto Clicker")
        self.window.resizable(False, False)

        try:
            self.window.iconbitmap("favicon.ico")
        except:
            pass

        # Variables
        self.running = False
        self.click_delay = ctk.StringVar(value="10")
        self.keybind = "<f6>"
        self.best_cps = 0

        self.load_config()

        self.mouse_controller = mouse.Controller()

        self.create_widgets()

        self.listener_thread = threading.Thread(target=self.listen_keybind, daemon=True)
        self.listener_thread.start()

        self.window.mainloop()

    def create_widgets(self):
        ctk.CTkLabel(self.window, text="LILNEROX AUTO CLICKER", font=("Arial Black", 16)).pack(pady=20)

        btn_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        btn_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text=f"START ({self.keybind.upper().strip('<>')})", command=self.start_clicking)
        self.start_btn.grid(row=0, column=0, padx=10, pady=10)

        self.stop_btn = ctk.CTkButton(btn_frame, text=f"STOP ({self.keybind.upper().strip('<>')})", command=self.stop_clicking)
        self.stop_btn.grid(row=0, column=1, padx=10, pady=10)

        entry_frame = ctk.CTkFrame(self.window, fg_color="transparent")
        entry_frame.pack(pady=10)

        ctk.CTkLabel(entry_frame, text="TIME (ms):").grid(row=0, column=0, padx=5)
        self.time_entry = ctk.CTkEntry(entry_frame, textvariable=self.click_delay, width=100)
        self.time_entry.grid(row=0, column=1, padx=5)

        self.keybind_btn = ctk.CTkButton(self.window, text="KEYBIND", command=self.change_keybind)
        self.keybind_btn.pack(pady=20)

        self.clicktest_btn = ctk.CTkButton(self.window, text="CLICK TEST", command=self.start_click_test)
        self.clicktest_btn.pack(pady=10)

        self.best_label = ctk.CTkLabel(self.window, text=f"Best: {self.best_cps} CPS")
        self.best_label.pack(pady=5)

    def start_clicking(self):
        if not self.running:
            self.running = True
            threading.Thread(target=self.click_loop, daemon=True).start()

    def stop_clicking(self):
        self.running = False

    def click_loop(self):
        try:
            delay = int(self.click_delay.get()) / 1000.0
        except ValueError:
            delay = 0.01
        while self.running:
            self.mouse_controller.click(mouse.Button.left)
            time.sleep(delay)

    def listen_keybind(self):
        def on_press(key):
            try:
                if key == keyboard.Key[self.keybind.replace("<", "").replace(">", "")]:
                    if self.running:
                        self.stop_clicking()
                    else:
                        self.start_clicking()
            except:
                pass

        with keyboard.Listener(on_press=on_press) as listener:
            listener.join()

    def change_keybind(self):
        top = ctk.CTkToplevel(self.window)
        top.geometry("300x150")
        top.title("Set New Keybind")
        top.transient(self.window)
        top.grab_set()

        self.window.update_idletasks()
        x = self.window.winfo_x() + (self.window.winfo_width() // 2) - 150
        y = self.window.winfo_y() + (self.window.winfo_height() // 2) - 75
        top.geometry(f"+{x}+{y}")

        label = ctk.CTkLabel(top, text="Press a new key...")
        label.pack(pady=10)

        key_var = {"key": None}

        def on_key(event):
            key_var["key"] = f"<{event.keysym.lower()}>"
            label.configure(text=f"New Keybind: {key_var['key'].upper()}")

        top.bind("<Key>", on_key)
        top.focus_force()

        def confirm():
            if key_var["key"]:
                self.keybind = key_var["key"]
                self.start_btn.configure(text=f"START ({self.keybind.upper().strip('<>')})")
                self.stop_btn.configure(text=f"STOP ({self.keybind.upper().strip('<>')})")
                self.save_config()
            top.destroy()

        def cancel():
            top.destroy()

        btn_frame = ctk.CTkFrame(top)
        btn_frame.pack(pady=10)

        ctk.CTkButton(btn_frame, text="Confirm", command=confirm).grid(row=0, column=0, padx=10)
        ctk.CTkButton(btn_frame, text="Cancel", command=cancel).grid(row=0, column=1, padx=10)

    def start_click_test(self):
        test_win = ctk.CTkToplevel(self.window)
        test_win.geometry("300x200")
        test_win.title("Click Test")
        test_win.transient(self.window)
        test_win.grab_set()

        ctk.CTkLabel(test_win, text="Click as fast as you can!").pack(pady=10)

        counter = {"clicks": 0, "started": False}

        click_area = ctk.CTkButton(test_win, text="CLICK HERE", height=100, width=200)
        click_area.pack(pady=10)

        def on_click(event):
            if not counter["started"]:
                counter["started"] = True
                threading.Thread(target=countdown).start()
            counter["clicks"] += 1

        def countdown():
            time.sleep(10)
            cps = counter["clicks"] / 10
            test_win.destroy()
            if cps > self.best_cps:
                self.best_cps = round(cps, 2)
                self.best_label.configure(text=f"Best: {self.best_cps} CPS")
                self.save_config()

        click_area.bind("<Button-1>", on_click)
        test_win.focus_force()

    def save_config(self):
        config = {
            "keybind": self.keybind,
            "click_delay": self.click_delay.get(),
            "best_cps": self.best_cps
        }
        with open(CONFIG_FILE, "w") as f:
            json.dump(config, f)

    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    config = json.load(f)
                    self.keybind = config.get("keybind", self.keybind)
                    self.click_delay.set(config.get("click_delay", "10"))
                    self.best_cps = config.get("best_cps", 0)
            except:
                pass

if __name__ == "__main__":
    AutoClickerApp()