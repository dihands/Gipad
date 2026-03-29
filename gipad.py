import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser, font
import requests
import urllib.parse

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("dark-blue")

class Gipad(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Gipad - Advanced Notepad")
        self.geometry("1100x720")

        self.tabs = {}
        self.file_paths = {}

        # Layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Sidebar
        self.sidebar = ctk.CTkFrame(self, width=140)
        self.sidebar.grid(row=0, column=0, sticky="ns")

        self.create_sidebar_buttons()

        # Tab System
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=1, sticky="nsew")

        self.new_tab()

        # Status Bar
        self.status = ctk.CTkLabel(self, text="Ready", anchor="w")
        self.status.grid(row=1, column=0, columnspan=2, sticky="ew")

        # Shortcuts
        self.bind_shortcuts()

    # ================= UI =================
    def create_sidebar_buttons(self):
        buttons = [
            ("New", self.new_tab),
            ("Open", self.open_file),
            ("Save", self.save_file),
            ("Save As", self.save_as),
            ("Font", self.change_font),
            ("Text Color", self.change_text_color),
            ("BG Color", self.change_bg_color),
            ("Ask AI", self.ask_ai)
        ]

        for text, cmd in buttons:
            ctk.CTkButton(self.sidebar, text=text, command=cmd).pack(pady=8, padx=10, fill="x")

    def bind_shortcuts(self):
        self.bind("<Control-n>", lambda e: self.new_tab())
        self.bind("<Control-o>", lambda e: self.open_file())
        self.bind("<Control-s>", lambda e: self.save_file())

    # ================= Tabs =================
    def current_tab(self):
        return self.tabview.get()

    def current_textbox(self):
        return self.tabs[self.current_tab()]

    def new_tab(self):
        name = f"Tab {len(self.tabs)+1}"
        self.tabview.add(name)
        frame = self.tabview.tab(name)

        textbox = tk.Text(
            frame,
            undo=True,
            bg="#0d0d0d",
            fg="#ff8800",
            insertbackground="white",
            font=("Consolas", 12)
        )
        textbox.pack(fill="both", expand=True)

        self.tabs[name] = textbox
        self.file_paths[name] = None
        self.tabview.set(name)

    # ================= File =================
    def open_file(self):
        file = filedialog.askopenfilename()
        if not file:
            return

        self.new_tab()
        textbox = self.current_textbox()

        try:
            with open(file, "r", encoding="utf-8") as f:
                textbox.insert("1.0", f.read())

            self.file_paths[self.current_tab()] = file
            self.status.configure(text=f"Opened: {file}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def save_file(self):
        tab = self.current_tab()
        textbox = self.current_textbox()

        if self.file_paths[tab]:
            self.write_file(self.file_paths[tab], textbox)
        else:
            self.save_as()

    def save_as(self):
        file = filedialog.asksaveasfilename(defaultextension=".txt")
        if not file:
            return

        self.file_paths[self.current_tab()] = file
        self.write_file(file, self.current_textbox())

    def write_file(self, path, textbox):
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(textbox.get("1.0", tk.END))
            self.status.configure(text="Saved")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    # ================= Font & Colors =================
    def change_font(self):
        font_window = tk.Toplevel(self)
        font_window.title("Choose Font")
        font_window.configure(bg="#1e1e1e")

        fonts = list(font.families())
        font_list = tk.Listbox(font_window, listvariable=tk.StringVar(value=fonts), height=10)
        font_list.pack(fill=tk.BOTH, expand=True)

        def apply_font():
            try:
                chosen = font_list.get(font_list.curselection())
                self.current_textbox().config(font=(chosen, 12))
            except:
                pass

        tk.Button(font_window, text="Apply", command=apply_font).pack()

    def change_text_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_textbox().config(fg=color)

    def change_bg_color(self):
        color = colorchooser.askcolor()[1]
        if color:
            self.current_textbox().config(bg=color)

    # ================= AI (Robust Wikipedia AI - FIXED) =================
    def ask_ai(self):
        def fetch():
            query = entry.get().strip()
            if not query:
                return

            try:
                headers = {
                    "User-Agent": "Gipad/1.0 (https://example.com)"
                }

                # Step 1: Search Wikipedia
                search_url = "https://en.wikipedia.org/w/api.php"
                params = {
                    "action": "query",
                    "list": "search",
                    "srsearch": query,
                    "format": "json"
                }

                search_res = requests.get(search_url, params=params, headers=headers, timeout=8)
                search_res.raise_for_status()
                search_data = search_res.json()

                results = search_data.get("query", {}).get("search", [])
                if not results:
                    messagebox.showinfo("AI", "No results found. Try simpler keywords.")
                    return

                final_text = ""

                for item in results[:3]:
                    title = item.get("title")
                    if not title:
                        continue

                    try:
                        encoded = urllib.parse.quote(title)
                        summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{encoded}"

                        res = requests.get(summary_url, headers=headers, timeout=8)
                        if res.status_code != 200:
                            continue

                        data = res.json()
                        extract = data.get("extract")

                        if extract:
                            final_text += f"\n\n[{title}]\n{extract}\n"

                    except:
                        continue

                if not final_text:
                    final_text = "No detailed information available."

                self.current_textbox().insert(tk.END, f"\n\n[AI RESULT]\n{final_text}\n")
                self.status.configure(text="AI response added")

            except requests.exceptions.RequestException:
                messagebox.showerror("AI Error", "Network error. Check your internet.")
            except Exception as e:
                messagebox.showerror("AI Error", f"Unexpected error: {str(e)}")

        top = ctk.CTkToplevel(self)
        top.title("Ask AI")
        top.geometry("320x140")

        entry = ctk.CTkEntry(top, placeholder_text="Ask anything...")
        entry.pack(padx=10, pady=10, fill="x")

        ctk.CTkButton(top, text="Ask", command=fetch).pack(pady=5)


if __name__ == "__main__":
    app = Gipad()
    app.mainloop()
