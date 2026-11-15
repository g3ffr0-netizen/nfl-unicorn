import os
import re
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog
from datetime import datetime

CONFIG_FILE = "file_engine_config.txt"

def sanitize_filename(name: str) -> str:
    """Strips invalid characters to ensure the OS can save the file."""
    cleaned = re.sub(r'[<>:"/\\|?*]', '_', name).strip()
    return cleaned if cleaned else "untitled_file"

def manage_backups(file_path: str, max_backups: int = 3):
    """Keeps only the most recent N backups to prevent folder bloat."""
    try:
        parent_dir = os.path.dirname(file_path)
        base_name = os.path.basename(file_path)
        
        backups = [
            f for f in os.listdir(parent_dir) 
            if f.startswith(base_name + ".") and f.endswith(".bak")
        ]
        backups.sort()
        
        if len(backups) >= max_backups:
            for old_backup in backups[:len(backups) - max_backups + 1]:
                try:
                    os.remove(os.path.join(parent_dir, old_backup))
                except Exception:
                    pass
    except Exception:
        pass

def load_theme():
    """Remember the user's theme preference."""
    try:
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, "r") as f:
                return f.read().strip() == "dark"
    except Exception:
        pass
    return False

def save_theme(is_dark):
    try:
        with open(CONFIG_FILE, "w") as f:
            f.write("dark" if is_dark else "light")
    except Exception:
        pass

def create_file():
    root = tk.Tk()
    root.withdraw()

    def clean_exit():
        try:
            if os.path.exists("autosave_temp.tmp"):
                os.remove("autosave_temp.tmp")
        except Exception:
            pass
        try:
            root.quit()
            root.destroy()
        except Exception:
            pass

    # 1. Ask for file name
    raw_name = simpledialog.askstring("File Generator", "Enter the file name (e.g., patent_spec, week10_data, notes):", parent=root)
    if not raw_name:
        clean_exit()
        return
    file_name = sanitize_filename(raw_name)

    # 2. Ask for file extension
    file_type = simpledialog.askstring("File Type", "Enter the file extension (e.g., .txt, .csv, .py, .md):", initialvalue=".txt", parent=root)
    if not file_type:
        file_type = ".txt"
    file_type = file_type.strip()
    if not file_type.startswith("."):
        file_type = "." + file_type

    # 3. Ask where to save it
    file_path = filedialog.asksaveasfilename(
        parent=root,
        initialfile=f"{file_name}{file_type}",
        defaultextension=file_type,
        filetypes=[("Target File", f"*{file_type}"), ("All Files", "*.*")],
        title="Save File As"
    )
    if not file_path:
        clean_exit()
        return

    # 4. Overwrite Warning & Auto-Backup Safety Net
    if os.path.exists(file_path):
        if not messagebox.askyesno("Overwrite Warning", f"The file '{os.path.basename(file_path)}' already exists. Do you want to overwrite it?", parent=root):
            clean_exit()
            return
        else:
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = f"{file_path}.{timestamp}.bak"
                shutil.copy2(file_path, backup_path)
                manage_backups(file_path)
            except Exception as e:
                if not messagebox.askyesno("Backup Failed", f"Could not create a backup of the file. Do you still want to overwrite it?\nError: {e}", parent=root):
                    clean_exit()
                    return

    # 5. Content Editor Window (Apex Sovereign UI)
    content_window = tk.Toplevel(root)
    content_window.title(f"Editing: {os.path.basename(file_path)}")
    content_window.geometry("740x540")
    content_window.protocol("WM_DELETE_WINDOW", clean_exit)

    top_frame = tk.Frame(content_window)
    top_frame.pack(fill="x", padx=12, pady=(8, 2))

    tk.Label(top_frame, text=f"Target: {file_path}", fg="#333333", font=("Segoe UI", 9, "bold")).pack(side="left")

    is_dark_mode = tk.BooleanVar(value=load_theme())

    def toggle_theme():
        if is_dark_mode.get():
            text_area.config(bg="#1e1e1e", fg="#d4d4d4", insertbackground="white")
            theme_btn.config(text="☀️ Light Mode")
        else:
            text_area.config(bg="white", fg="black", insertbackground="black")
            theme_btn.config(text="🌙 Dark Mode")
        save_theme(is_dark_mode.get())

    theme_btn = tk.Button(top_frame, text="Toggle Theme", command=lambda: [is_dark_mode.set(not is_dark_mode.get()), toggle_theme()], font=("Segoe UI", 8))
    theme_btn.pack(side="right")

    tk.Label(content_window, text="Paste or type your content below:").pack(anchor="w", padx=14, pady=(0, 2))

    text_frame = tk.Frame(content_window)
    text_frame.pack(expand=True, fill="both", padx=12, pady=5)

    scrollbar = tk.Scrollbar(text_frame)
    scrollbar.pack(side="right", fill="y")

    text_area = tk.Text(text_frame, wrap="word", yscrollcommand=scrollbar.set, font=("Consolas", 10))
    text_area.pack(side="left", expand=True, fill="both")
    scrollbar.config(command=text_area.yview)
    text_area.focus_set()
    
    toggle_theme() # Apply initial theme

    # Recovery Check
    if os.path.exists("autosave_temp.tmp"):
        try:
            with open("autosave_temp.tmp", "r", encoding="utf-8") as tmp:
                recovered_data = tmp.read()
                if recovered_data and messagebox.askyesno("Recovery Found", "An unsaved session was detected. Restore it?", parent=content_window):
                    text_area.insert("1.0", recovered_data)
                else:
                    os.remove("autosave_temp.tmp")
        except Exception:
            pass

    status_var = tk.StringVar(value="Characters: 0 | Lines: 0")
    tk.Label(content_window, textvariable=status_var, fg="#555555").pack(anchor="e", padx=14)

    # Debounce timer for autosave
    autosave_timer = None

    def perform_autosave():
        try:
            content = text_area.get("1.0", "end-1c")
            with open("autosave_temp.tmp", "w", encoding="utf-8") as tmp:
                tmp.write(content)
        except Exception:
            pass

    def update_metrics(event=None):
        content = text_area.get("1.0", "end-1c")
        chars = len(content)
        lines = content.count("\n") + (1 if chars > 0 else 0)
        status_var.set(f"Characters: {chars:,} | Lines: {lines:,}")
        
        nonlocal autosave_timer
        if autosave_timer is not None:
            content_window.after_cancel(autosave_timer)
        autosave_timer = content_window.after(2000, perform_autosave)

    text_area.bind("<KeyRelease>", update_metrics)
    text_area.bind("<ButtonRelease-1>", update_metrics)

    def save_and_close():
        content = text_area.get("1.0", "end-1c")
        if not content.strip():
            if not messagebox.askyesno("Empty File", "The text box is empty. Save anyway?", parent=content_window):
                return
        try:
            parent_dir = os.path.dirname(file_path)
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            with open(file_path, "w", encoding="utf-8", newline="") as f:
                f.write(content)
            if os.path.exists("autosave_temp.tmp"):
                os.remove("autosave_temp.tmp")
            messagebox.showinfo("Success", f"File saved to:\n{file_path}", parent=content_window)
            clean_exit()
        except Exception as e:
            messagebox.showerror("Error", f"Could not save file:\n{e}", parent=content_window)

    btn_frame = tk.Frame(content_window)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="💾 Save File", command=save_and_close, bg="#1e7e34", fg="white", font=("Segoe UI", 10, "bold"), padx=16, pady=5).pack(side="left", padx=8)
    tk.Button(btn_frame, text="Cancel", command=clean_exit, padx=12, pady=5).pack(side="left", padx=8)

    root.mainloop()

if __name__ == "__main__":
    create_file()
