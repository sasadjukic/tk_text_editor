import tkinter as tk
from tkinter import filedialog, messagebox, font, ttk
import os

class ModernScrollbar(tk.Canvas):
    """A modern, minimalist scrollbar with hover effects"""
    def __init__(self, parent, **kwargs):
        self.command = kwargs.pop('command', None)
        bg = kwargs.pop('bg', '#1e1e1e')
        
        super().__init__(parent, bg=bg, highlightthickness=0, 
                        width=12, bd=0, **kwargs)
        
        # Colors
        self.bg_color = bg
        self.default_color = '#3a3a3a'  # Subtle by default
        self.hover_color = '#555555'    # More visible on hover
        self.active_color = '#666666'   # Even more visible when dragging
        
        # State
        self.thumb_top = 0
        self.thumb_height = 0
        self.is_hovering = False
        self.is_dragging = False
        self.drag_start_y = 0
        self.drag_start_top = 0
        
        # Create the scrollbar thumb (will be updated in redraw)
        self.thumb = None
        self.radius = 4  # Corner radius for rounded edges
        
        # Bind events
        self.bind('<Enter>', self.on_enter)
        self.bind('<Leave>', self.on_leave)
        self.bind('<Button-1>', self.on_press)
        self.bind('<B1-Motion>', self.on_drag)
        self.bind('<ButtonRelease-1>', self.on_release)
        self.bind('<Configure>', lambda e: self.redraw())
        
    def set(self, first, last):
        """Update scrollbar position (called by text widget)"""
        first, last = float(first), float(last)
        
        height = self.winfo_height()
        if height <= 1:
            return
            
        # Calculate thumb position and size
        self.thumb_top = int(first * height)
        self.thumb_height = max(int((last - first) * height), 30)  # Minimum height of 30px
        
        self.redraw()
    
    def create_rounded_rectangle(self, x1, y1, x2, y2, radius, **kwargs):
        """Create a rounded rectangle on the canvas"""
        points = [
            x1 + radius, y1,
            x2 - radius, y1,
            x2, y1,
            x2, y1 + radius,
            x2, y2 - radius,
            x2, y2,
            x2 - radius, y2,
            x1 + radius, y2,
            x1, y2,
            x1, y2 - radius,
            x1, y1 + radius,
            x1, y1
        ]
        return self.create_polygon(points, smooth=True, **kwargs)
    
    def redraw(self):
        """Redraw the scrollbar thumb"""
        height = self.winfo_height()
        if height <= 1:
            return
            
        # Ensure thumb stays within bounds
        if self.thumb_top + self.thumb_height > height:
            self.thumb_top = height - self.thumb_height
        if self.thumb_top < 0:
            self.thumb_top = 0
            
        # Choose color based on state
        if self.is_dragging:
            color = self.active_color
        elif self.is_hovering:
            color = self.hover_color
        else:
            color = self.default_color
            
        # Delete old thumb and create new one with rounded corners
        if self.thumb:
            self.delete(self.thumb)
        
        self.thumb = self.create_rounded_rectangle(
            2, self.thumb_top, 
            10, self.thumb_top + self.thumb_height,
            self.radius,
            fill=color,
            outline=''
        )
    
    def on_enter(self, event):
        """Handle mouse entering the scrollbar"""
        self.is_hovering = True
        self.redraw()
    
    def on_leave(self, event):
        """Handle mouse leaving the scrollbar"""
        if not self.is_dragging:
            self.is_hovering = False
            self.redraw()
    
    def on_press(self, event):
        """Handle mouse press on scrollbar"""
        self.is_dragging = True
        self.drag_start_y = event.y
        self.drag_start_top = self.thumb_top
        
        # Check if clicked on thumb or track
        if self.thumb_top <= event.y <= self.thumb_top + self.thumb_height:
            # Clicked on thumb - start dragging
            pass
        else:
            # Clicked on track - jump to position
            height = self.winfo_height()
            click_ratio = event.y / height
            if self.command:
                self.command('moveto', click_ratio)
        
        self.redraw()
    
    def on_drag(self, event):
        """Handle dragging the scrollbar thumb"""
        if not self.is_dragging:
            return
            
        delta = event.y - self.drag_start_y
        new_top = self.drag_start_top + delta
        
        height = self.winfo_height()
        max_top = height - self.thumb_height
        
        # Constrain to valid range
        new_top = max(0, min(new_top, max_top))
        
        # Calculate scroll position
        if height > self.thumb_height:
            scroll_ratio = new_top / (height - self.thumb_height)
        else:
            scroll_ratio = 0
            
        if self.command:
            self.command('moveto', scroll_ratio)
    
    def on_release(self, event):
        """Handle mouse release"""
        self.is_dragging = False
        if not self.is_hovering:
            self.redraw()


class EditorTab:
    """Represents a single editor tab with its own text widget and state"""
    def __init__(self, parent, editor, bg_color, text_color, menu_bg, selection_bg):
        self.parent = parent
        self.editor = editor  # Reference to main editor
        self.current_file = None
        self.is_modified = False
        self.show_line_numbers = False
        
        # Colors
        self.bg_color = bg_color
        self.text_color = text_color
        self.menu_bg = menu_bg
        self.selection_bg = selection_bg
        
        # Create the tab frame
        self.frame = tk.Frame(parent, bg=bg_color)
        
        # Text widget with scrollbar
        text_frame = tk.Frame(self.frame, bg=bg_color)
        text_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Line numbers widget
        self.line_numbers = tk.Text(
            text_frame,
            width=4,
            padx=5,
            pady=10,
            bg=bg_color,
            fg="#858585",
            font=font.Font(family="Consolas", size=11),
            state=tk.DISABLED,
            relief=tk.FLAT,
            takefocus=0,
            cursor="arrow",
            borderwidth=0,
            highlightthickness=0
        )
        
        # Modern Scrollbar with hover effects
        scrollbar = ModernScrollbar(text_frame, bg=bg_color, command=self.on_scrollbar)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Text widget
        self.text_font = font.Font(family="Consolas", size=11)
        self.text_area = tk.Text(
            text_frame,
            wrap=tk.WORD,
            undo=True,
            font=self.text_font,
            bg=bg_color,
            fg=text_color,
            insertbackground=text_color,
            selectbackground=selection_bg,
            selectforeground="white",
            relief=tk.FLAT,
            padx=10,
            pady=10,
            yscrollcommand=scrollbar.set,
            borderwidth=0,
            highlightthickness=0
        )
        self.text_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Store scrollbar reference for line numbers sync
        self.scrollbar = scrollbar
        
        # Track modifications
        self.text_area.bind('<<Modified>>', self.on_text_change)
        
        # Update line numbers on content changes
        self.text_area.bind('<KeyRelease>', self.update_line_numbers, add='+')
        self.text_area.bind('<<Modified>>', self.update_line_numbers, add='+')
        
        # Bind undo/redo directly to text area
        self.text_area.bind('<Control-z>', lambda e: self.text_area.event_generate('<<Undo>>'))
        self.text_area.bind('<Control-y>', lambda e: self.text_area.event_generate('<<Redo>>'))
        
    def on_text_change(self, event=None):
        if self.text_area.edit_modified():
            self.is_modified = True
            self.editor.update_tab_title(self)
            self.text_area.edit_modified(False)
    
    def on_scrollbar(self, *args):
        """Synchronize scrolling for both text area and line numbers"""
        self.text_area.yview(*args)
        if self.show_line_numbers:
            self.line_numbers.yview(*args)
    
    def update_line_numbers(self, event=None):
        """Update the line numbers display"""
        if not self.show_line_numbers:
            return
        
        # Get the number of lines
        line_count = self.text_area.index('end-1c').split('.')[0]
        
        # Generate line numbers
        line_numbers_text = "\n".join(str(i) for i in range(1, int(line_count) + 1))
        
        # Update line numbers widget
        self.line_numbers.config(state=tk.NORMAL)
        self.line_numbers.delete(1.0, tk.END)
        self.line_numbers.insert(1.0, line_numbers_text)
        self.line_numbers.config(state=tk.DISABLED)
    
    def toggle_line_numbers(self):
        """Toggle the visibility of line numbers"""
        self.show_line_numbers = not self.show_line_numbers
        
        if self.show_line_numbers:
            self.line_numbers.pack(side=tk.LEFT, fill=tk.Y, before=self.text_area)
            self.update_line_numbers()
        else:
            self.line_numbers.pack_forget()
    
    def get_title(self):
        """Get the title for this tab"""
        filename = os.path.basename(self.current_file) if self.current_file else "Untitled"
        return f"*{filename}" if self.is_modified else filename
    
    def focus(self):
        """Focus on this tab's text area"""
        self.text_area.focus()


class ModernTextEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Modern Text Editor")
        self.root.geometry("900x600")
        
        # Configure color scheme (modern dark theme)
        self.bg_color = "#1e1e1e"
        self.text_color = "#d4d4d4"
        self.menu_bg = "#2d2d2d"
        self.menu_fg = "#cccccc"
        self.selection_bg = "#264f78"
        
        # Tab management
        self.tabs = []
        self.untitled_counter = 1
        
        self.setup_ui()
        self.bind_shortcuts()
        
    def setup_ui(self):
        # Configure root background
        self.root.configure(bg=self.bg_color)
        
        # Top bar frame for custom menu and hamburger
        top_bar = tk.Frame(self.root, bg=self.bg_color, height=40)
        top_bar.pack(side=tk.TOP, fill=tk.X)
        top_bar.pack_propagate(False)  # Maintain fixed height

        # Style for Menubuttons
        menu_btn_style = {
            "bg": self.bg_color,
            "fg": self.menu_fg,
            "activebackground": "#094771",
            "activeforeground": "white",
            "relief": tk.FLAT,
            "font": ("Segoe UI", 10),
            "padx": 10,
            "pady": 5,
            "cursor": "hand2"
        }

        # Header Title (optional, or just for spacing if needed, but let's stick to buttons)
        # We can put the buttons in a frame on the left
        menu_frame = tk.Frame(top_bar, bg=self.bg_color)
        menu_frame.pack(side=tk.LEFT, padx=2)

        # File Menu
        file_btn = tk.Menubutton(menu_frame, text="File", **menu_btn_style)
        file_btn.pack(side=tk.LEFT)
        
        file_menu = tk.Menu(file_btn, tearoff=0, bg=self.menu_bg, fg=self.menu_fg)
        file_menu.add_command(label="New Tab", command=self.new_tab, accelerator="Ctrl+T")
        file_menu.add_command(label="New File", command=self.new_file, accelerator="Ctrl+N")
        file_menu.add_command(label="Open...", command=self.open_file, accelerator="Ctrl+O")
        file_menu.add_command(label="Save", command=self.save_file, accelerator="Ctrl+S")
        file_menu.add_command(label="Save As...", command=self.save_as_file, accelerator="Ctrl+Shift+S")
        file_menu.add_separator()
        file_menu.add_command(label="Close Tab", command=self.close_tab, accelerator="Ctrl+W")
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.exit_editor, accelerator="Ctrl+Q")
        
        file_btn.config(menu=file_menu)

        # Edit Menu
        edit_btn = tk.Menubutton(menu_frame, text="Edit", **menu_btn_style)
        edit_btn.pack(side=tk.LEFT)
        
        edit_menu = tk.Menu(edit_btn, tearoff=0, bg=self.menu_bg, fg=self.menu_fg)
        edit_menu.add_command(label="Undo", command=self.undo, accelerator="Ctrl+Z")
        edit_menu.add_command(label="Redo", command=self.redo, accelerator="Ctrl+Y")
        edit_menu.add_separator()
        edit_menu.add_command(label="Cut", command=self.cut, accelerator="Ctrl+X")
        edit_menu.add_command(label="Copy", command=self.copy, accelerator="Ctrl+C")
        edit_menu.add_command(label="Paste", command=self.paste, accelerator="Ctrl+V")
        edit_menu.add_separator()
        edit_menu.add_command(label="Select All", command=self.select_all, accelerator="Ctrl+A")
        edit_menu.add_command(label="Find...", command=self.find_text, accelerator="Ctrl+F")
        
        edit_btn.config(menu=edit_menu)
        
        # Hamburger menu button in upper right corner of the SAME top_bar
        hamburger_btn = tk.Button(
            top_bar,
            text="☰",
            command=self.show_hamburger_menu,
            bg=self.bg_color,
            fg=self.menu_fg,
            activebackground="#094771",
            activeforeground="white",
            relief=tk.FLAT,
            font=("Segoe UI", 16),
            padx=15,
            pady=0,
            cursor="hand2",
            highlightthickness=0,
            bd=0
        )
        hamburger_btn.pack(side=tk.RIGHT, padx=5)
        self.hamburger_btn = hamburger_btn
        
        # Settings button - placed to the left of hamburger (packed after hamburger with side=RIGHT)
        settings_btn = tk.Button(
            top_bar,
            text="⚙",
            command=self.show_settings,
            bg=self.bg_color,
            fg=self.menu_fg,
            activebackground="#094771",
            activeforeground="white",
            relief=tk.FLAT,
            font=("Segoe UI", 16),
            padx=15,
            pady=0,
            cursor="hand2",
            highlightthickness=0,
            bd=0
        )
        settings_btn.pack(side=tk.RIGHT)
        
        # Create tooltip label for "Main Menu" (hidden by default)
        self.menu_tooltip = tk.Label(
            top_bar,
            text="Main Menu",
            bg=self.menu_bg,
            fg=self.menu_fg,
            font=("Segoe UI", 10)
        )
        # Don't pack it yet - it will show on hover
        
        # Bind hover events to show/hide tooltip
        hamburger_btn.bind('<Enter>', self.show_menu_tooltip)
        hamburger_btn.bind('<Leave>', self.hide_menu_tooltip)
        
        # Main container frame
        main_frame = tk.Frame(self.root, bg=self.bg_color)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create Notebook for tabs
        style = ttk.Style()
        style.theme_use('default')
        
        # Style the notebook
        style.configure('TNotebook', background=self.bg_color, borderwidth=0)
        style.configure('TNotebook.Tab', 
                       background=self.menu_bg, 
                       foreground=self.menu_fg,
                       padding=[20, 10], # Increased padding for wider tabs
                       font=("Segoe UI", 10), # Increased font size
                       borderwidth=0)
        style.map('TNotebook.Tab',
                 background=[('selected', self.menu_bg)],
                 foreground=[('selected', 'white')])
        
        self.notebook = ttk.Notebook(main_frame, style='TNotebook')
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.notebook.bind('<<NotebookTabChanged>>', self.on_tab_changed)
        
        # Enable close button on tabs
        self.notebook.bind('<Button-1>', self.on_tab_click)
        
    def create_tab_header(self, title, tab_index):
        """Create a tab header with a close button"""
        frame = tk.Frame(self.notebook, bg=self.menu_bg, padx=2, pady=2)
        
        # Tab label
        label = tk.Label(
            frame, 
            text=title,
            bg=self.menu_bg,
            fg=self.menu_fg,
            padx=5
        )
        label.pack(side=tk.LEFT)
        
        # Close button
        close_btn = tk.Label(
            frame,
            text="×",
            bg=self.menu_bg,
            fg=self.menu_fg,
            padx=3,
            cursor="hand2",
            font=("Segoe UI", 10, "bold")
        )
        close_btn.pack(side=tk.LEFT)
        
        # Bind close button click
        close_btn.bind('<Button-1>', lambda e: self.close_tab_by_index(tab_index))
        
        # Bind hover effects
        def on_enter(e):
            close_btn.config(fg="red")
        def on_leave(e):
            close_btn.config(fg=self.menu_fg)
        
        close_btn.bind('<Enter>', on_enter)
        close_btn.bind('<Leave>', on_leave)
        
        return frame
    
    def on_tab_click(self, event):
        """Handle clicks on tab area to close tab when clicking the × symbol"""
        try:
            # Identify which tab was clicked
            clicked_tab = self.notebook.tk.call(self.notebook._w, "identify", "tab", event.x, event.y)
            
            if clicked_tab != '':
                tab_index = int(clicked_tab)
                
                # Get the tab's bounding box to determine if click was on the right side (close button area)
                tab_bbox = self.notebook.bbox(tab_index)
                if tab_bbox:
                    tab_x, tab_y, tab_width, tab_height = tab_bbox
                    # If click is in the rightmost 25 pixels of the tab, treat it as a close button click
                    if event.x > (tab_x + tab_width - 25):
                        self.close_tab_by_index(tab_index)
                        return "break"  # Prevent tab selection
        except Exception as e:
            pass
        
        # Status Bar
        status_frame = tk.Frame(self.root, bg=self.menu_bg)
        status_frame.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_bar = tk.Label(
            status_frame,
            text="Line 1, Col 1  |  0 words  |  0 characters",
            anchor=tk.W,
            bg=self.menu_bg,
            fg=self.menu_fg,
            padx=10,
            pady=5,
            font=("Segoe UI", 9)
        )
        self.status_bar.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        

        
        # Create first tab after all UI is ready
        self.new_tab()
        
    def bind_shortcuts(self):
        self.root.bind('<Control-t>', lambda e: self.new_tab())
        self.root.bind('<Control-n>', lambda e: self.new_file())
        self.root.bind('<Control-o>', lambda e: self.open_file())
        self.root.bind('<Control-s>', lambda e: self.save_file())
        self.root.bind('<Control-S>', lambda e: self.save_as_file())
        self.root.bind('<Control-w>', lambda e: self.close_tab())
        self.root.bind('<Control-q>', lambda e: self.exit_editor())
        self.root.bind('<Control-f>', lambda e: self.find_text())
        
        # Tab navigation
        self.root.bind('<Control-Tab>', lambda e: self.next_tab())
        self.root.bind('<Control-Shift-ISO_Left_Tab>', lambda e: self.prev_tab())
        
        # Zoom bindings
        self.root.bind('<Control-plus>', lambda e: self.zoom_in())
        self.root.bind('<Control-equal>', lambda e: self.zoom_in())
        self.root.bind('<Control-KP_Add>', lambda e: self.zoom_in())
        
        self.root.bind('<Control-minus>', lambda e: self.zoom_out())
        self.root.bind('<Control-KP_Subtract>', lambda e: self.zoom_out())
        
        self.root.bind('<Control-0>', lambda e: self.reset_zoom())
        
        # Toggle line numbers
        self.root.bind('<Control-L>', lambda e: self.toggle_line_numbers())
    
    def get_active_tab(self):
        """Get the currently active editor tab"""
        if not self.tabs:
            return None
        selected_index = self.notebook.index(self.notebook.select())
        return self.tabs[selected_index]
    
    def new_tab(self):
        """Create a new empty tab"""
        tab = EditorTab(self.notebook, self, self.bg_color, self.text_color, 
                       self.menu_bg, self.selection_bg)
        self.tabs.append(tab)
        
        # Set title
        title = f"Untitled {self.untitled_counter}" if self.untitled_counter > 1 else "Untitled"
        self.untitled_counter += 1
        
        # Add tab with close button symbol
        tab_index = len(self.tabs) - 1
        self.notebook.add(tab.frame, text=f"{title}  ×")
        
        self.notebook.select(tab.frame)
        
        # Bind status update events
        tab.text_area.bind('<KeyRelease>', self.update_status, add='+')
        tab.text_area.bind('<ButtonRelease-1>', self.update_status, add='+')
        
        tab.focus()
        self.update_title()
        return tab
    
    def close_tab_by_index(self, index):
        """Close tab at specified index"""
        if 0 <= index < len(self.tabs):
            tab = self.tabs[index]
            if self.check_save_changes(tab):
                self.notebook.forget(index)
                self.tabs.remove(tab)
                
                # If no tabs left, create a new one
                if not self.tabs:
                    self.new_tab()
                
                self.update_title()
    
    def new_file(self):
        """Clear current tab for a new file"""
        tab = self.get_active_tab()
        if tab and self.check_save_changes(tab):
            tab.text_area.delete(1.0, tk.END)
            tab.current_file = None
            tab.is_modified = False
            self.update_tab_title(tab)
            
    def open_file(self):
        """Open a file in a new tab"""
        filepath = filedialog.askopenfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("All Files", "*.*")
            ]
        )
        if filepath:
            # Create new tab for this file
            tab = self.new_tab()
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                tab.text_area.delete(1.0, tk.END)
                tab.text_area.insert(1.0, content)
                tab.current_file = filepath
                tab.is_modified = False
                self.update_tab_title(tab)
            except Exception as e:
                messagebox.showerror("Error", f"Could not open file:\\n{e}")
                
    def save_file(self):
        """Save the current tab's file"""
        tab = self.get_active_tab()
        if not tab:
            return False
            
        if tab.current_file:
            try:
                content = tab.text_area.get(1.0, tk.END)[:-1]
                with open(tab.current_file, 'w', encoding='utf-8') as f:
                    f.write(content)
                tab.is_modified = False
                self.update_tab_title(tab)
                return True
            except Exception as e:
                messagebox.showerror("Error", f"Could not save file:\\n{e}")
                return False
        else:
            return self.save_as_file()
            
    def save_as_file(self):
        """Save the current tab's file with a new name"""
        tab = self.get_active_tab()
        if not tab:
            return False
            
        filepath = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[
                ("Text Files", "*.txt"),
                ("Python Files", "*.py"),
                ("All Files", "*.*")
            ]
        )
        if filepath:
            tab.current_file = filepath
            return self.save_file()
        return False
    
    def close_tab(self):
        """Close the current tab"""
        tab = self.get_active_tab()
        if not tab:
            return
        
        if not self.check_save_changes(tab):
            return
        
        # Remove the tab
        tab_index = self.tabs.index(tab)
        self.notebook.forget(tab_index)
        self.tabs.remove(tab)
        
        # If no tabs left, create a new one
        if not self.tabs:
            self.new_tab()
        
        self.update_title()
    
    def next_tab(self):
        """Switch to the next tab"""
        if len(self.tabs) <= 1:
            return
        current = self.notebook.index(self.notebook.select())
        next_index = (current + 1) % len(self.tabs)
        self.notebook.select(next_index)
    
    def prev_tab(self):
        """Switch to the previous tab"""
        if len(self.tabs) <= 1:
            return
        current = self.notebook.index(self.notebook.select())
        prev_index = (current - 1) % len(self.tabs)
        self.notebook.select(prev_index)
    
    def on_tab_changed(self, event=None):
        """Handle tab change event"""
        tab = self.get_active_tab()
        if tab:
            tab.focus()
            self.update_status()
            self.update_title()
    
    def check_save_changes(self, tab):
        """Check if tab has unsaved changes"""
        if tab.is_modified:
            response = messagebox.askyesnocancel(
                "Unsaved Changes",
                f"Do you want to save changes to {tab.get_title()}?"
            )
            if response:  # Yes
                return self.save_file()
            elif response is None:  # Cancel
                return False
        return True
        
    def exit_editor(self):
        """Exit the editor, checking all tabs for unsaved changes"""
        for tab in self.tabs:
            if not self.check_save_changes(tab):
                return
        self.root.quit()
    
    def update_tab_title(self, tab):
        """Update the title of a specific tab"""
        tab_index = self.tabs.index(tab)
        self.notebook.tab(tab_index, text=f"{tab.get_title()}  ×")
        self.update_title()
    
    def update_title(self):
        """Update the window title based on active tab"""
        tab = self.get_active_tab()
        if tab:
            filename = tab.get_title().lstrip('*')
            self.root.title(f"{tab.get_title()} - Modern Text Editor")
        else:
            self.root.title("Modern Text Editor")
    
    def update_status(self, event=None):
        """Update the status bar based on active tab"""
        tab = self.get_active_tab()
        if not tab:
            return
        
        # Get cursor position
        cursor_pos = tab.text_area.index(tk.INSERT)
        line, col = cursor_pos.split('.')
        
        # Get text statistics
        content = tab.text_area.get(1.0, tk.END)
        words = len(content.split())
        chars = len(content) - 1
        
        self.status_bar.config(
            text=f"Line {line}, Col {int(col)+1}  |  {words} words  |  {chars} characters"
        )
    
    # Edit commands - route to active tab
    def undo(self):
        tab = self.get_active_tab()
        if tab:
            try:
                tab.text_area.edit_undo()
            except:
                pass
        return 'break'
    
    def redo(self):
        tab = self.get_active_tab()
        if tab:
            try:
                tab.text_area.edit_redo()
            except:
                pass
        return 'break'
    
    def cut(self):
        tab = self.get_active_tab()
        if tab:
            tab.text_area.event_generate("<<Cut>>")
    
    def copy(self):
        tab = self.get_active_tab()
        if tab:
            tab.text_area.event_generate("<<Copy>>")
    
    def paste(self):
        tab = self.get_active_tab()
        if tab:
            tab.text_area.event_generate("<<Paste>>")
    
    def select_all(self):
        tab = self.get_active_tab()
        if tab:
            tab.text_area.tag_add(tk.SEL, "1.0", tk.END)
            tab.text_area.mark_set(tk.INSERT, "1.0")
            tab.text_area.see(tk.INSERT)
        return 'break'
    
    def find_text(self):
        tab = self.get_active_tab()
        if not tab:
            return
        
        search_window = tk.Toplevel(self.root)
        search_window.title("Find")
        search_window.geometry("350x100")
        search_window.configure(bg=self.bg_color)
        
        def on_close():
            tab.text_area.tag_remove('found', '1.0', tk.END)
            search_window.destroy()
        
        search_window.protocol("WM_DELETE_WINDOW", on_close)
        
        tk.Label(search_window, text="Find:", bg=self.bg_color, fg=self.text_color).pack(pady=5)
        search_entry = tk.Entry(search_window, width=40)
        search_entry.pack(pady=5)
        search_entry.focus()
        
        def find():
            search_text = search_entry.get()
            if search_text:
                tab.text_area.tag_remove('found', '1.0', tk.END)
                start = '1.0'
                while True:
                    pos = tab.text_area.search(search_text, start, tk.END)
                    if not pos:
                        break
                    end = f"{pos}+{len(search_text)}c"
                    tab.text_area.tag_add('found', pos, end)
                    start = end
                tab.text_area.tag_config('found', background='yellow', foreground='black')
        
        tk.Button(search_window, text="Find All", command=find).pack(pady=5)
    
    def zoom_in(self):
        tab = self.get_active_tab()
        if tab:
            current_size = tab.text_font['size']
            tab.text_font.configure(size=current_size + 1)
    
    def zoom_out(self):
        tab = self.get_active_tab()
        if tab:
            current_size = tab.text_font['size']
            if current_size > 6:
                tab.text_font.configure(size=current_size - 1)
    
    def reset_zoom(self):
        tab = self.get_active_tab()
        if tab:
            tab.text_font.configure(size=11)
    
    def toggle_line_numbers(self):
        tab = self.get_active_tab()
        if tab:
            tab.toggle_line_numbers()
    
    def show_menu_tooltip(self, event=None):
        """Show the Main Menu tooltip on hover"""
        self.menu_tooltip.pack(side=tk.RIGHT, padx=(0, 5))
    
    def hide_menu_tooltip(self, event=None):
        """Hide the Main Menu tooltip when not hovering"""
        self.menu_tooltip.pack_forget()
    
    def show_hamburger_menu(self):
        """Display the hamburger menu with View options"""
        # Create popup menu
        hamburger_menu = tk.Menu(self.root, tearoff=0, bg=self.menu_bg, fg=self.menu_fg)
        
        # Add View menu items
        hamburger_menu.add_command(label="Zoom In", command=self.zoom_in, accelerator="Ctrl++")
        hamburger_menu.add_command(label="Zoom Out", command=self.zoom_out, accelerator="Ctrl+-")
        hamburger_menu.add_command(label="Reset Zoom", command=self.reset_zoom, accelerator="Ctrl+0")
        
        # Get button position to display menu below it
        x = self.hamburger_btn.winfo_rootx()
        y = self.hamburger_btn.winfo_rooty() + self.hamburger_btn.winfo_height()
        
        # Display the menu using tk_popup (handles auto-close properly)
        try:
            hamburger_menu.tk_popup(x, y)
        finally:
            hamburger_menu.grab_release()
    
    def show_settings(self):
        """Display the settings dialog"""
        tab = self.get_active_tab()
        if not tab:
            return
        
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("400x200")
        settings_window.configure(bg=self.bg_color)
        settings_window.resizable(False, False)
        
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        title_label = tk.Label(
            settings_window,
            text="Settings",
            font=("Segoe UI", 14, "bold"),
            bg=self.bg_color,
            fg=self.text_color
        )
        title_label.pack(pady=20)
        
        settings_frame = tk.Frame(settings_window, bg=self.bg_color)
        settings_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=10)
        
        line_numbers_var = tk.BooleanVar(value=tab.show_line_numbers)
        
        def on_line_numbers_toggle():
            if line_numbers_var.get() != tab.show_line_numbers:
                tab.toggle_line_numbers()
        
        line_numbers_check = tk.Checkbutton(
            settings_frame,
            text="Show Line Numbers",
            variable=line_numbers_var,
            command=on_line_numbers_toggle,
            bg=self.bg_color,
            fg=self.text_color,
            selectcolor=self.menu_bg,
            activebackground=self.bg_color,
            activeforeground=self.text_color,
            font=("Segoe UI", 10),
            cursor="hand2"
        )
        line_numbers_check.pack(anchor=tk.W, pady=5)
        
        close_btn = tk.Button(
            settings_window,
            text="Close",
            command=settings_window.destroy,
            bg=self.menu_bg,
            fg=self.menu_fg,
            activebackground="#094771",
            activeforeground="white",
            relief=tk.FLAT,
            font=("Segoe UI", 10),
            padx=20,
            pady=5,
            cursor="hand2"
        )
        close_btn.pack(pady=10)

if __name__ == "__main__":
    root = tk.Tk()
    editor = ModernTextEditor(root)
    root.mainloop()