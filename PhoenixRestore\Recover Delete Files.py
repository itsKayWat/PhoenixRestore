import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import os
import shutil
from datetime import datetime
import json
import threading
import pystray
from PIL import Image
import sys
import win32gui
import win32con

class FileRecoveryApp:
    def __init__(self, root):
        self.root = root
        self.root.title("File Recovery Tool")
        self.root.geometry("1000x700")
        
        # Hide console window
        self.hide_console()
        
        # System tray setup
        self.setup_system_tray()
        
        # Minimize to tray when clicking close button
        self.root.protocol('WM_DELETE_WINDOW', self.minimize_to_tray)
        
        # Colors
        self.dark_bg = "#1a1a1a"
        self.emerald = "#50C878"
        self.button_bg = "#2E8B57"
        self.button_text = "#FFFFFF"
        
        self.root.configure(bg=self.dark_bg)
        self.deleted_files = []
        self.current_filter = "all"
        self.setup_gui()

    def hide_console(self):
        """Hide the console window"""
        console_window = win32gui.GetForegroundWindow()
        win32gui.ShowWindow(console_window, win32con.SW_HIDE)

    def setup_system_tray(self):
        """Setup system tray icon and menu"""
        # Create system tray icon
        image = Image.new('RGB', (64, 64), color = (50, 200, 120))
        menu = (
            pystray.MenuItem('Show', self.show_window),
            pystray.MenuItem('Exit', self.quit_window)
        )
        self.icon = pystray.Icon(
            "name",
            image,
            "File Recovery Tool",
            menu
        )
        
        # Run system tray icon in separate thread
        threading.Thread(target=self.icon.run, daemon=True).start()

    def show_window(self, icon=None, item=None):
        """Show the main window"""
        self.root.deiconify()
        self.root.state('normal')
        self.root.focus_force()

    def minimize_to_tray(self):
        """Minimize to system tray"""
        self.root.withdraw()

    def quit_window(self, icon=None, item=None):
        """Exit the application"""
        self.icon.stop()
        self.root.destroy()
        sys.exit()

    def setup_gui(self):
        # Title
        title = tk.Label(
            self.root,
            text="File Recovery Tool",
            font=("Helvetica", 24, "bold"),
            bg=self.dark_bg,
            fg=self.emerald
        )
        title.pack(pady=20)

        # File type buttons
        types_frame = tk.Frame(self.root, bg=self.dark_bg)
        types_frame.pack(fill=tk.X, padx=20)

        file_types = ["Documents", "Videos", "Images", "Emails", "Audio", "Other"]
        for ftype in file_types:
            btn = tk.Button(
                types_frame,
                text=ftype,
                bg=self.button_bg,
                fg=self.button_text,
                command=lambda t=ftype: self.filter_files(t.lower()),
                width=15
            )
            btn.pack(side=tk.LEFT, padx=5)

        # Search bar
        search_frame = tk.Frame(self.root, bg=self.dark_bg)
        search_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.search_entry = tk.Entry(search_frame, bg="#2D2D2D", fg="white", width=100)
        self.search_entry.pack(side=tk.LEFT, padx=5)
        
        search_btn = tk.Button(
            search_frame,
            text="Search",
            bg=self.button_bg,
            fg=self.button_text,
            command=self.search_files
        )
        search_btn.pack(side=tk.LEFT)

        # Main content area
        content_frame = tk.Frame(self.root, bg=self.dark_bg)
        content_frame.pack(fill=tk.BOTH, expand=True, padx=20)

        # Files listbox
        self.files_listbox = tk.Listbox(
            content_frame,
            bg="#2D2D2D",
            fg="white",
            selectmode=tk.MULTIPLE,
            width=70,
            height=20
        )
        self.files_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Scrollbar
        scrollbar = tk.Scrollbar(content_frame)
        scrollbar.pack(side=tk.LEFT, fill=tk.Y)
        
        self.files_listbox.config(yscrollcommand=scrollbar.set)
        scrollbar.config(command=self.files_listbox.yview)

        # Control buttons frame
        buttons_frame = tk.Frame(content_frame, bg=self.dark_bg)
        buttons_frame.pack(side=tk.LEFT, padx=20)

        # Control buttons
        buttons = [
            ("Quick Scan", self.quick_scan),
            ("Deep Scan", self.deep_scan),
            ("Restore Selected", self.restore_files),
            ("Choose Location", self.choose_restore_location),
            ("Preview File", self.preview_file),
            ("Recovery History", self.show_history)
        ]

        for text, command in buttons:
            btn = tk.Button(
                buttons_frame,
                text=text,
                bg=self.button_bg,
                fg=self.button_text,
                command=command,
                width=15
            )
            btn.pack(pady=5)

        # Add README button
        tk.Button(
            buttons_frame,
            text="README",
            bg=self.button_bg,
            fg=self.button_text,
            command=self.show_readme,
            width=15
        ).pack(pady=5)

        # Add Scan Info button
        tk.Button(
            buttons_frame,
            text="Scan Info",
            bg=self.button_bg,
            fg=self.button_text,
            command=self.show_scan_info,
            width=15
        ).pack(pady=5)

        # Status bar
        self.status_var = tk.StringVar()
        self.status_var.set("Ready")
        status_bar = tk.Label(
            self.root,
            textvariable=self.status_var,
            bg=self.dark_bg,
            fg="white"
        )
        status_bar.pack(side=tk.BOTTOM, fill=tk.X, pady=5)

        self.restore_location = os.path.expanduser("~/Desktop")

    def quick_scan(self):
        self.status_var.set("Performing quick scan...")
        self.files_listbox.delete(0, tk.END)
        
        # Scan common locations for recently deleted files
        locations = [
            os.path.expanduser("~/.Trash"),  # Mac
            os.path.expanduser("~/Recycle Bin"),  # Windows
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Downloads")
        ]
        
        for location in locations:
            if os.path.exists(location):
                for root, _, files in os.walk(location):
                    for file in files:
                        full_path = os.path.join(root, file)
                        self.deleted_files.append(full_path)
                        self.files_listbox.insert(tk.END, file)
        
        self.status_var.set(f"Quick scan complete. Found {len(self.deleted_files)} files.")

    def deep_scan(self):
        try:
            # Disable buttons during scan
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(state='disabled')

            self.status_var.set("Starting deep scan...")
            self.files_listbox.delete(0, tk.END)
            self.deleted_files = []  # Clear using a new list instead of clear()

            # Create progress window
            progress_window = tk.Toplevel(self.root)
            progress_window.title("Deep Scan Progress")
            progress_window.geometry("400x200")
            progress_window.configure(bg=self.dark_bg)
            
            # Labels
            tk.Label(
                progress_window,
                text="Deep Scan in Progress...",
                bg=self.dark_bg,
                fg=self.emerald,
                font=("Helvetica", 12, "bold")
            ).pack(pady=10)

            self.progress_label = tk.Label(
                progress_window,
                text="Scanning...",
                bg=self.dark_bg,
                fg=self.emerald
            )
            self.progress_label.pack(pady=5)

            self.files_count_label = tk.Label(
                progress_window,
                text="Files found: 0",
                bg=self.dark_bg,
                fg=self.emerald
            )
            self.files_count_label.pack(pady=5)

            # Progress bar
            self.progress_bar = ttk.Progressbar(
                progress_window,
                mode='indeterminate',
                length=300
            )
            self.progress_bar.pack(pady=10)
            self.progress_bar.start(10)

            # Cancel button
            self.scanning = True
            tk.Button(
                progress_window,
                text="Cancel Scan",
                bg=self.button_bg,
                fg=self.button_text,
                command=self.cancel_scan
            ).pack(pady=10)

            def safe_scan():
                try:
                    file_count = 0
                    batch = []  # Batch for updating listbox
                    batch_size = 100  # Update UI every 100 files

                    # Define scan locations
                    scan_paths = [
                        os.path.expanduser("~/Documents"),
                        os.path.expanduser("~/Downloads"),
                        os.path.expanduser("~/Desktop"),
                        os.path.expanduser("~/Pictures"),
                        os.path.expanduser("~/Videos")
                    ]

                    def update_ui():
                        if not self.scanning:
                            return
                        try:
                            if batch:
                                for item in batch:
                                    self.files_listbox.insert(tk.END, item)
                                    batch.clear()
                                    self.files_count_label.config(text=f"Files found: {file_count}")
                                    self.root.update()
                        except tk.TclError:
                            self.scanning = False

                    for scan_path in scan_paths:
                        if not self.scanning:
                            break

                        if not os.path.exists(scan_path):
                            continue

                        try:
                            for root, _, files in os.walk(scan_path):
                                if not self.scanning:
                                    break

                                self.progress_label.config(text=f"Scanning: {root}")
                                
                                for file in files:
                                    if not self.scanning:
                                        break

                                    try:
                                        full_path = os.path.join(root, file)
                                        if os.path.exists(full_path):
                                            self.deleted_files.append(full_path)
                                            batch.append(file)
                                            file_count += 1

                                            if len(batch) >= batch_size:
                                                self.root.after(0, update_ui)

                                    except (PermissionError, OSError):
                                        continue

                        except (PermissionError, OSError):
                            continue

                    # Final update for remaining files
                    if batch:
                        self.root.after(0, update_ui)

                    # Cleanup
                    if self.scanning:
                        self.root.after(0, lambda: self.status_var.set(f"Scan complete. Found {file_count} files."))
                    else:
                        self.root.after(0, lambda: self.status_var.set("Scan cancelled."))

                except Exception as e:
                    self.root.after(0, lambda: self.status_var.set(f"Scan error: {str(e)}"))
                finally:
                    # Re-enable buttons
                    self.root.after(0, self.enable_buttons)
                    try:
                        progress_window.destroy()
                    except tk.TclError:
                        pass

            # Start scan in separate thread
            scan_thread = threading.Thread(target=safe_scan, daemon=True)
            scan_thread.start()

        except Exception as e:
            messagebox.showerror("Error", f"Failed to start scan: {str(e)}")
            self.enable_buttons()

    def cancel_scan(self):
        """Cancel the scanning process"""
        self.scanning = False
        self.status_var.set("Cancelling scan...")

    def enable_buttons(self):
        """Re-enable all buttons"""
        try:
            for widget in self.root.winfo_children():
                if isinstance(widget, tk.Button):
                    widget.configure(state='normal')
        except tk.TclError:
            pass

    def filter_files(self, file_type):
        self.current_filter = file_type
        self.files_listbox.delete(0, tk.END)
        
        extensions = {
            'documents': ['.doc', '.docx', '.pdf', '.txt', '.rtf'],
            'videos': ['.mp4', '.avi', '.mov', '.wmv'],
            'images': ['.jpg', '.jpeg', '.png', '.gif', '.bmp'],
            'emails': ['.eml', '.msg'],
            'audio': ['.mp3', '.wav', '.ogg', '.m4a']
        }
        
        for file_path in self.deleted_files:
            file_name = os.path.basename(file_path)
            ext = os.path.splitext(file_name)[1].lower()
            
            if file_type == 'all' or (file_type in extensions and ext in extensions[file_type]):
                self.files_listbox.insert(tk.END, file_name)

    def search_files(self):
        search_term = self.search_entry.get().lower()
        self.files_listbox.delete(0, tk.END)
        
        for file_path in self.deleted_files:
            file_name = os.path.basename(file_path).lower()
            if search_term in file_name:
                self.files_listbox.insert(tk.END, os.path.basename(file_path))

    def restore_files(self):
        selections = self.files_listbox.curselection()
        if not selections:
            messagebox.showwarning("Warning", "Please select files to restore")
            return
            
        for index in selections:
            file_name = self.files_listbox.get(index)
            source_path = next((f for f in self.deleted_files if os.path.basename(f) == file_name), None)
            if source_path and os.path.exists(source_path):
                destination = os.path.join(self.restore_location, file_name)
                try:
                    shutil.copy2(source_path, destination)
                    self.status_var.set(f"Restored: {file_name}")
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to restore {file_name}: {str(e)}")

    def choose_restore_location(self):
        directory = filedialog.askdirectory(
            title="Choose Restore Location",
            initialdir=self.restore_location
        )
        if directory:
            self.restore_location = directory
            self.status_var.set(f"Restore location: {directory}")

    def preview_file(self):
        selection = self.files_listbox.curselection()
        if selection:
            file_name = self.files_listbox.get(selection[0])
            self.status_var.set(f"Previewing: {file_name}")
            # Here you would implement actual file preview functionality

    def show_history(self):
        history_window = tk.Toplevel(self.root)
        history_window.title("Recovery History")
        history_window.geometry("400x300")
        history_window.configure(bg=self.dark_bg)
        
        history_list = tk.Listbox(
            history_window,
            bg="#2D2D2D",
            fg="white"
        )
        history_list.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Add some dummy history items
        history_list.insert(tk.END, "No previous recovery history")

    def show_readme(self):
        """Display README information in a new window"""
        readme_window = tk.Toplevel(self.root)
        readme_window.title("File Recovery Tool - README")
        readme_window.geometry("800x600")
        readme_window.configure(bg="#1a1a1a")

        # Create text widget with white text on dark background
        text = tk.Text(
            readme_window,
            bg="#1a1a1a",  # Dark background
            fg="#50C878",  # Emerald green text
            font=("Courier", 12),
            wrap=tk.WORD,
            padx=20,
            pady=20
        )
        
        # Create and attach scrollbar
        scrollbar = tk.Scrollbar(readme_window, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text.config(yscrollcommand=scrollbar.set)

        readme_text = """FILE RECOVERY TOOL - USER GUIDE

QUICK SCAN
----------
• Fast scan of recently deleted files
• Checks common locations:
  - Recycle Bin
  - Desktop
  - Downloads
  - Documents
• Takes 1-2 minutes
• Best for recent deletions
• Lower system resource usage

DEEP SCAN
---------
• Thorough system-wide search
• Checks all accessible locations:
  - All user folders
  - System directories
  - Connected drives
• Takes 10-30 minutes
• Finds older deleted files
• Higher system resource usage

HOW TO USE
----------
1. Choose scan type:
   • Quick Scan for recent files
   • Deep Scan for thorough search

2. Wait for scan completion

3. Use filters to find files:
   • Documents
   • Videos
   • Images
   • Emails
   • Audio
   • Other

4. Select files to recover

5. Choose restore location

6. Click 'Restore Selected'

TIPS
----
• Start with Quick Scan
• Use Deep Scan if needed
• Filter results by type
• Preview before recovery
• Choose new location for recovery

WARNING
-------
• Don't save to original location
• Keep app running during scan
• Avoid disk writing during scan
• Success rate varies by file age"""

        # Insert the content
        text.insert("1.0", readme_text)
        
        # Make text read-only
        text.config(state='disabled')

        # Add close button
        close_button = tk.Button(
            readme_window,
            text="Close",
            bg="#2E8B57",
            fg="white",
            command=readme_window.destroy,
            font=("Helvetica", 10, "bold")
        )
        close_button.pack(side=tk.BOTTOM, pady=10)

    def show_scan_info(self):
        """Display detailed scan information"""
        scan_info_window = tk.Toplevel(self.root)
        scan_info_window.title("Scan Types Information")
        scan_info_window.geometry("700x800")
        scan_info_window.configure(bg=self.dark_bg)

        # Create frame with scrollbar
        frame = tk.Frame(scan_info_window, bg=self.dark_bg)
        frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)

        # Add scrollbar
        scrollbar = tk.Scrollbar(frame)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Create text widget
        text = tk.Text(
            frame,
            bg="#2D2D2D",
            fg=self.emerald,
            font=("Helvetica", 11),
            wrap=tk.WORD,
            padx=15,
            pady=15,
            selectbackground="#4A4A4A",
            selectforeground="#FFFFFF"
        )
        text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.config(command=text.yview)
        text.config(yscrollcommand=scrollbar.set)

        # Insert the scan content
        text.insert(tk.END, scan_content)
        text.config(state=tk.DISABLED)

        # Add close button
        close_button = tk.Button(
            scan_info_window,
            text="Close",
            bg=self.button_bg,
            fg=self.button_text,
            command=scan_info_window.destroy,
            width=15
        )
        close_button.pack(pady=10)

class RecoveryEngine:
    def __init__(self):
        self.encryption_support = ['BitLocker', 'FileVault', 'VeraCrypt']
        self.raid_support = ['RAID0', 'RAID1', 'RAID5', 'RAID6', 'RAID10']
        
    def handle_encrypted_data(self, file_path, encryption_type):
        # Add encryption handling
        pass

    def recover_raid_data(self, raid_config):
        # Add RAID recovery logic
        pass

if __name__ == "__main__":
    # Hide console on startup
    if sys.executable.endswith("pythonw.exe"):
        sys.stdout = open(os.devnull, "w")
        sys.stderr = open(os.devnull, "w")
    
    root = tk.Tk()
    app = FileRecoveryApp(root)
    root.mainloop()