#!/usr/bin/env python3
import sys
import tkinter as tk
from tkinter import simpledialog, messagebox, ttk
import json
import os
import tkinter.filedialog as filedialog
import tkinter.colorchooser as colorchooser
import re

try:
    import jdatetime
except ImportError:
    root = tk.Tk()
    root.withdraw()
    messagebox.showerror(
        "Missing Dependency",
        "The 'jdatetime' module is not installed.\nPlease install it using:\npip install jdatetime"
    )
    sys.exit(1)

# Constants
EVENTS_FILE = "events.json"
SETTINGS_FILE = "settings.json"
events = {}

def load_events():
    global events
    if os.path.exists(EVENTS_FILE):
        try:
            with open(EVENTS_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                events = {tuple(map(int, k.split("-"))): v for k, v in raw.items()}
        except (IOError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Failed to load events: {e}")

def save_events():
    try:
        with open(EVENTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"-".join(map(str, k)): v for k, v in events.items()}, f, indent=2, ensure_ascii=False)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save events: {e}")

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data.get("last_year"), data.get("last_month")
        except (IOError, json.JSONDecodeError) as e:
            messagebox.showerror("Error", f"Failed to load settings: {e}")
    return None, None

def save_settings(year, month):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_year": year, "last_month": month}, f)
    except IOError as e:
        messagebox.showerror("Error", f"Failed to save settings: {e}")

def get_event_color(event_count, event_color=None):
    default_color = '#cccccc'
    shades = [
        "#cce5ff", "#99ccff", "#66b3ff", "#3399ff", "#1a8cff",
        "#0073e6", "#0059b3", "#004080", "#00264d", "#001a33"
    ]
    index = min(event_count, 10) - 1
    return event_color or shades[index] if event_count > 0 else default_color

def validate_time(time_str):
    """Validate time format (HH:MM, 24-hour)."""
    if not time_str:
        return True  # Allow empty time
    pattern = r'^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$'
    return bool(re.match(pattern, time_str))

def priority_to_str(priority):
    """Convert priority integer to string."""
    return {1: "High", 2: "Medium", 3: "Low"}.get(priority, "Unknown")

def str_to_priority(priority_str):
    """Convert priority string to integer."""
    return {"High": 1, "Medium": 2, "Low": 3}.get(priority_str, 2)

today_jdate = jdatetime.date.today()

def add_event(year, month, day):
    key = (year, month, day)
    event = simpledialog.askstring("Add Event", f"Enter event for {day}/{month}/{year}:")
    if event:
        time = simpledialog.askstring("Event Time", "Enter time (HH:MM, 24-hour, optional):")
        if time and not validate_time(time):
            messagebox.showerror("Error", "Invalid time format. Use HH:MM (24-hour).")
            return
        priority = simpledialog.askinteger("Event Priority", "Enter priority (1=High, 2=Medium, 3=Low):", minvalue=1, maxvalue=3)
        if priority is None:
            return
        color_code = colorchooser.askcolor(title="Pick a color")[1]
        events.setdefault(key, []).append((event, color_code, time or "", priority))
        save_events()
        set_calendar()
        messagebox.showinfo("Success", "Event added.")

def view_events(year, month, day):
    key = (year, month, day)
    day_events = events.get(key, [])
    if day_events:
        msg = "\n".join(f"- {e[0]} (Time: {e[2] or 'N/A'}, Priority: {priority_to_str(e[3])}, Color: {e[1]})" for e in day_events)
        messagebox.showinfo(f"Events for {day}/{month}/{year}", msg)
    else:
        messagebox.showinfo("No Events", f"No events for {day}/{month}/{year}.")

def edit_event_panel(year, month, day, idx):
    """Open a panel to edit all event details at once."""
    key = (year, month, day)
    day_events = events.get(key, [])
    if not day_events or idx < 0 or idx >= len(day_events):
        messagebox.showinfo("No Events", "No event to edit.")
        return

    event = day_events[idx]
    edit_window = tk.Toplevel(root)
    edit_window.title(f"Edit Event for {day}/{month}/{year}")
    edit_window.geometry("400x300")
    edit_window.config(bg=theme["root_bg"])

    # Create a frame for the form
    form_frame = tk.Frame(edit_window, bg=theme["root_bg"])
    form_frame.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

    # Event text
    tk.Label(form_frame, text="Event:", bg=theme["root_bg"], fg=theme["label_fg"]).grid(row=0, column=0, sticky="e", pady=5)
    event_entry = tk.Entry(form_frame, width=30, bg=theme["entry_bg"], fg=theme["entry_fg"])
    event_entry.insert(0, event[0])
    event_entry.grid(row=0, column=1, sticky="w", pady=5)

    # Time
    tk.Label(form_frame, text="Time (HH:MM, optional):", bg=theme["root_bg"], fg=theme["label_fg"]).grid(row=1, column=0, sticky="e", pady=5)
    time_entry = tk.Entry(form_frame, width=30, bg=theme["entry_bg"], fg=theme["entry_fg"])
    time_entry.insert(0, event[2])
    time_entry.grid(row=1, column=1, sticky="w", pady=5)

    # Priority
    tk.Label(form_frame, text="Priority:", bg=theme["root_bg"], fg=theme["label_fg"]).grid(row=2, column=0, sticky="e", pady=5)
    priority_var = tk.StringVar(value=priority_to_str(event[3]))
    priority_menu = ttk.Combobox(form_frame, textvariable=priority_var, values=["High", "Medium", "Low"], state="readonly", width=27)
    priority_menu.grid(row=2, column=1, sticky="w", pady=5)

    # Color
    tk.Label(form_frame, text="Color:", bg=theme["root_bg"], fg=theme["label_fg"]).grid(row=3, column=0, sticky="e", pady=5)
    color_var = tk.StringVar(value=event[1])
    color_button = tk.Button(form_frame, text="Pick Color", command=lambda: color_var.set(colorchooser.askcolor(title="Pick a color")[1] or color_var.get()), 
                             bg=theme["button_bg"], fg=theme["button_fg"])
    color_button.grid(row=3, column=1, sticky="w", pady=5)

    def save_changes():
        new_text = event_entry.get().strip()
        new_time = time_entry.get().strip()
        new_priority = str_to_priority(priority_var.get())
        new_color = color_var.get()

        if not new_text:
            messagebox.showerror("Error", "Event description cannot be empty.")
            return
        if new_time and not validate_time(new_time):
            messagebox.showerror("Error", "Invalid time format. Use HH:MM (24-hour).")
            return

        day_events[idx] = (new_text, new_color, new_time or "", new_priority)
        save_events()
        set_calendar()
        edit_window.destroy()
        messagebox.showinfo("Success", "Event updated.")

    def delete_event():
        choice = messagebox.askyesno("Delete Event", "Are you sure you want to delete this event?")
        if choice:
            day_events.pop(idx)
            save_events()
            set_calendar()
            edit_window.destroy()
            messagebox.showinfo("Deleted", "Event deleted.")

    # Buttons
    button_frame = tk.Frame(form_frame, bg=theme["root_bg"])
    button_frame.grid(row=4, column=0, columnspan=2, pady=10)
    tk.Button(button_frame, text="Save", command=save_changes, bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Delete", command=delete_event, bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Cancel", command=edit_window.destroy, bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=tk.LEFT, padx=5)

    edit_window.protocol("WM_DELETE_WINDOW", edit_window.destroy)

def edit_events(year, month, day):
    key = (year, month, day)
    day_events = events.get(key, [])
    if not day_events:
        messagebox.showinfo("No Events", "No events to edit.")
        return
    list_text = "\n".join(f"{i+1}: {e[0]} (Time: {e[2] or 'N/A'}, Priority: {priority_to_str(e[3])})" for i, e in enumerate(day_events))
    selected = simpledialog.askinteger("Edit Event", f"Select event index to edit:\n{list_text}")
    if selected is None or not (1 <= selected <= len(day_events)):
        return
    idx = selected - 1
    edit_event_panel(year, month, day, idx)

def delete_all_events():
    if events:
        choice = messagebox.askyesno("Delete All Events", "Are you sure you want to delete all events?")
        if choice:
            events.clear()
            save_events()
            set_calendar()
            messagebox.showinfo("Success", "All events have been deleted.")
    else:
        messagebox.showinfo("No Events", "No events to delete.")

def on_day_click(year, month, day):
    view_day_page(year, month, day)

def is_leap_year(year):
    try:
        jdatetime.date(year, 12, 30)
        return True
    except ValueError:
        return False

def get_days_in_month(year, month):
    return 31 if month <= 6 else 30 if month <= 11 else (30 if is_leap_year(year) else 29)

def add_tooltip(widget, text):
    def on_enter(e):
        widget.tooltip = tk.Toplevel(widget)
        widget.tooltip.wm_overrideredirect(True)
        x = widget.winfo_rootx() + 50
        y = widget.winfo_rooty() + 10
        widget.tooltip.wm_geometry(f"+{x}+{y}")
        label = tk.Label(widget.tooltip, text=text, justify='left', background='lightyellow',
                         relief='solid', borderwidth=1, font=("Arial", 9))
        label.pack(ipadx=1)
    def on_leave(e):
        if hasattr(widget, 'tooltip'):
            widget.tooltip.destroy()
            del widget.tooltip
    widget.bind("<Enter>", on_enter)
    widget.bind("<Leave>", on_leave)

def show_calendar(year, month):
    for widget in calendar_frame.winfo_children():
        widget.destroy()
    # Create a centered frame to hold the calendar grid
    centered_frame = tk.Frame(calendar_frame, bg=theme["calendar_bg"])
    centered_frame.pack(expand=True, anchor="center")
    
    month_name = jdatetime.date(year, month, 1).strftime('%B')
    tk.Label(centered_frame, text=f"{month_name} {year}", font=("Arial", 16), bg=theme["calendar_bg"]).grid(row=0, column=0, columnspan=7)
    weekdays = ['Sat', 'Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri']
    for i, name in enumerate(weekdays):
        tk.Label(centered_frame, text=name, font=("Arial", 10, "bold"), bg=theme["calendar_bg"]).grid(row=1, column=i)
    first_weekday = (jdatetime.date(year, month, 1).togregorian().weekday() + 2) % 7
    row, col = 2, first_weekday
    for day in range(1, get_days_in_month(year, month) + 1):
        key = (year, month, day)
        miladi_str = jdatetime.date(year, month, day).togregorian().strftime('%m/%d')
        is_today = (year, month, day) == (today_jdate.year, today_jdate.month, today_jdate.day)
        event_count = len(events.get(key, []))
        event_colors = [e[1] for e in events.get(key, [])]
        bg_color = 'red' if is_today else (event_colors[0] if event_colors and event_colors[0] != '#cccccc' else get_event_color(event_count))
        fg_color = 'white' if is_today else None
        btn = tk.Button(centered_frame, text=f"{day}\n({miladi_str})", width=6, bg=bg_color, fg=fg_color,
                        command=lambda d=day: on_day_click(year, month, d))
        btn.grid(row=row, column=col, padx=2, pady=2)
        tooltip_text = "\n".join(f"{e[0]} (Time: {e[2] or 'N/A'}, Priority: {priority_to_str(e[3])})" for e in events.get(key, [])) or "No events"
        add_tooltip(btn, tooltip_text)
        col += 1
        if col > 6:
            col, row = 0, row + 1

def show_full_year_calendar(year):
    for widget in calendar_frame.winfo_children():
        widget.destroy()
    # Create a frame to hold the canvas and scrollbar
    canvas_frame = tk.Frame(calendar_frame, bg=theme["calendar_bg"])
    canvas_frame.pack(expand=True, fill="both", padx=10, pady=10)
    
    canvas = tk.Canvas(canvas_frame, highlightthickness=0, bg=theme["calendar_bg"])
    scrollbar = tk.Scrollbar(canvas_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = tk.Frame(canvas, bg=theme["calendar_bg"])
    
    # Bind configure to update scroll region
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    
    # Create window in canvas, centered horizontally
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Create a frame to hold the grid of months
    months_frame = tk.Frame(scrollable_frame, bg=theme["calendar_bg"])
    months_frame.pack(expand=True, fill="x", padx=20, pady=20)
    
    for m in range(1, 13):
        frame = tk.LabelFrame(months_frame, text=jdatetime.date(year, m, 1).strftime('%B'),
                              padx=5, pady=5,
                              bg=theme["calendar_bg"],
                              fg=theme["label_fg"],
                              font=("Arial", 10))
        frame.grid(row=(m - 1) // 3, column=(m - 1) % 3, padx=10, pady=10, sticky="n")
        for i, name in enumerate(['S', 'S', 'M', 'T', 'W', 'T', 'F']):
            tk.Label(frame, text=name, font=("Arial", 8, "bold"),
                     width=3, bg=theme["calendar_bg"], fg=theme["label_fg"]).grid(row=0, column=i)
        first_weekday = (jdatetime.date(year, m, 1).togregorian().weekday() + 2) % 7
        r, c = 1, first_weekday
        for day in range(1, get_days_in_month(year, m) + 1):
            key = (year, m, day)
            miladi_day = jdatetime.date(year, m, day).togregorian().strftime('%d')
            label = f"{day}\n({miladi_day})"
            is_today = (year, m, day) == (today_jdate.year, today_jdate.month, today_jdate.day)
            event_count = len(events.get(key, []))
            event_colors = [e[1] for e in events.get(key, [])]
            bg_color = 'red' if is_today else (event_colors[0] if event_colors and event_colors[0] != '#cccccc' else get_event_color(event_count))
            fg_color = 'white' if is_today else None
            btn = tk.Button(frame, text=label, width=4, bg=bg_color, fg=fg_color,
                            command=lambda y=year, mo=m, d=day: on_day_click(y, mo, d))
            btn.grid(row=r, column=c)
            tooltip_text = "\n".join(f"{e[0]} (Time: {e[2] or 'N/A'}, Priority: {priority_to_str(e[3])})" for e in events.get(key, [])) or "No events"
            add_tooltip(btn, tooltip_text)
            c += 1
            if c > 6:
                c, r = 0, r + 1

def change_month(delta):
    try:
        y = int(year_entry.get())
        m = int(month_entry.get()) + delta
        if m < 1:
            m = 12
            y -= 1
        elif m > 12:
            m = 1
            y += 1
        year_entry.delete(0, tk.END)
        year_entry.insert(0, str(y))
        month_entry.delete(0, tk.END)
        month_entry.insert(0, str(m))
        set_calendar()
        save_settings(y, m)
    except ValueError:
        messagebox.showerror("Error", "Please enter valid numbers.")

def set_calendar():
    try:
        y, m = int(year_entry.get()), int(month_entry.get())
        if not (1 <= m <= 12):
            raise ValueError("Month must be between 1 and 12.")
        save_settings(y, m)
        if view_mode.get() == "year":
            show_full_year_calendar(y)
        else:
            show_calendar(y, m)
    except ValueError as e:
        messagebox.showerror("Error", f"Invalid input: {e}")

def toggle_dark_mode():
    global theme
    current_mode = dark_mode_var.get()
    theme = dark_theme if current_mode else light_theme
    style.theme_use("clam" if current_mode else "default")
    root.config(bg=theme["root_bg"])
    top_frame.config(bg=theme["top_bg"])
    calendar_frame.config(bg=theme["calendar_bg"])
    for widget in root.winfo_children():
        try:
            widget.config(bg=theme["top_bg"], fg=theme["label_fg"])
        except:
            pass

def view_day_page(year, month, day):
    day_window = tk.Toplevel(root)
    day_window.title(f"Events for {day}/{month}/{year}")
    day_window.geometry("600x500")  # Increased size for better visibility
    day_window.config(bg=theme["root_bg"])
    key = (year, month, day)
    day_events = events.get(key, [])

    header_label = tk.Label(day_window, text=f"Events for {day}/{month}/{year}", font=("Arial", 16), bg=theme["root_bg"], fg=theme["label_fg"])
    header_label.pack(pady=10)

    # Create a frame for the Listbox and scrollbar
    list_frame = tk.Frame(day_window, bg=theme["root_bg"])
    list_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

    # Create Listbox to display events
    event_listbox = tk.Listbox(list_frame, bg=theme["entry_bg"], fg=theme["entry_fg"], font=("Arial", 12), selectbackground="#a6a6a6")
    event_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    # Add scrollbar
    scrollbar = tk.Scrollbar(list_frame, orient=tk.VERTICAL, command=event_listbox.yview)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    event_listbox.config(yscrollcommand=scrollbar.set)

    # Populate Listbox with events
    def populate_listbox():
        event_listbox.delete(0, tk.END)
        for event in day_events:
            display_text = f"{event[0]} (Time: {event[2] or 'N/A'}, Priority: {priority_to_str(event[3])})"
            event_listbox.insert(tk.END, display_text)

    populate_listbox()

    # Variables for drag-and-drop
    drag_index = None

    def start_drag(event):
        nonlocal drag_index
        # Get the index of the item under the cursor
        drag_index = event_listbox.nearest(event.y)
        if drag_index >= 0:
            event_listbox.select_clear(0, tk.END)
            event_listbox.select_set(drag_index)

    def drag_motion(event):
        nonlocal drag_index
        if drag_index is None:
            return
        # Get the index where the mouse is currently
        current_index = event_listbox.nearest(event.y)
        if current_index >= 0 and current_index != drag_index:
            # Move the item in the Listbox
            item = event_listbox.get(drag_index)
            event_listbox.delete(drag_index)
            event_listbox.insert(current_index, item)
            # Update the events list
            day_events.insert(current_index, day_events.pop(drag_index))
            drag_index = current_index
            event_listbox.select_clear(0, tk.END)
            event_listbox.select_set(drag_index)

    def end_drag(event):
        nonlocal drag_index
        if drag_index is not None:
            # Save the reordered events
            events[key] = day_events[:]
            save_events()
            set_calendar()
            drag_index = None

    # Bind drag-and-drop events
    event_listbox.bind("<Button-1>", start_drag)
    event_listbox.bind("<B1-Motion>", drag_motion)
    event_listbox.bind("<ButtonRelease-1>", end_drag)

    # Sorting functions
    def sort_by_time():
        nonlocal day_events
        # Sort events: events with time first (chronologically), then events without time
        day_events.sort(key=lambda e: (e[2] == "", e[2] or "25:00"))
        events[key] = day_events[:]
        save_events()
        populate_listbox()
        messagebox.showinfo("Sorted", "Events sorted by time.")

    def sort_by_priority():
        nonlocal day_events
        # Sort events by priority (1=High, 2=Medium, 3=Low)
        day_events.sort(key=lambda e: e[3])
        events[key] = day_events[:]
        save_events()
        populate_listbox()
        messagebox.showinfo("Sorted", "Events sorted by priority.")

    # Key bindings for sorting
    day_window.bind("<Control-t>", lambda e: sort_by_time())
    day_window.bind("<Control-p>", lambda e: sort_by_priority())

    if not day_events:
        no_events_label = tk.Label(day_window, text="No events for this day", bg=theme["root_bg"], fg=theme["label_fg"], font=("Arial", 12))
        no_events_label.pack(pady=20)

    # Button frame for sorting and other actions
    button_frame = tk.Frame(day_window, bg=theme["root_bg"])
    button_frame.pack(fill=tk.X, pady=10)

    def add_event_button():
        event = simpledialog.askstring("Add Event", f"Enter event for {day}/{month}/{year}:")
        if event:
            time = simpledialog.askstring("Event Time", "Enter time (HH:MM, 24-hour, optional):")
            if time and not validate_time(time):
                messagebox.showerror("Error", "Invalid time format. Use HH:MM (24-hour).")
                return
            priority = simpledialog.askinteger("Event Priority", "Enter priority (1=High, 2=Medium, 3=Low):", minvalue=1, maxvalue=3)
            if priority is None:
                return
            color_code = colorchooser.askcolor(title="Pick a color")[1]
            events.setdefault(key, []).append((event, color_code, time or "", priority))
            save_events()
            set_calendar()
            day_window.destroy()
            view_day_page(year, month, day)
    
    def edit_event_button():
        edit_events(year, month, day)
        day_window.destroy()
        view_day_page(year, month, day)
    
    def delete_event_button():
        key = (year, month, day)
        day_events = events.get(key, [])
        if day_events:
            choice = messagebox.askyesno("Delete All Events", f"Are you sure you want to delete all events for {day}/{month}/{year}?")
            if choice:
                events[key] = []
                save_events()
                day_window.destroy()
                set_calendar()
                messagebox.showinfo("Success", f"All events for {day}/{month}/{year} have been deleted.")
            else:
                messagebox.showinfo("Cancel", "No events were deleted.")
        else:
            messagebox.showinfo("No Events", f"No events for {day}/{month}/{year} to delete.")
    
    # Add sorting buttons
    sort_time_btn = tk.Button(button_frame, text="Sort by Time (Ctrl+T)", command=sort_by_time, bg=theme["button_bg"], fg=theme["button_fg"])
    sort_time_btn.pack(side=tk.LEFT, padx=5)
    sort_priority_btn = tk.Button(button_frame, text="Sort by Priority (Ctrl+P)", command=sort_by_priority, bg=theme["button_bg"], fg=theme["button_fg"])
    sort_priority_btn.pack(side=tk.LEFT, padx=5)
    # Add existing buttons
    add_event_btn = tk.Button(button_frame, text="Add Event", command=add_event_button, bg=theme["button_bg"], fg=theme["button_fg"])
    add_event_btn.pack(side=tk.LEFT, padx=5)
    edit_event_btn = tk.Button(button_frame, text="Edit Events", command=edit_event_button, bg=theme["button_bg"], fg=theme["button_fg"])
    edit_event_btn.pack(side=tk.LEFT, padx=5)
    delete_event_btn = tk.Button(button_frame, text="Delete All Events", command=delete_event_button, bg=theme["button_bg"], fg=theme["button_fg"])
    delete_event_btn.pack(side=tk.LEFT, padx=5)
    
    day_window.protocol("WM_DELETE_WINDOW", day_window.destroy)

def export_events():
    filepath = filedialog.asksaveasfilename(defaultextension=".json", filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
    if filepath:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump({"-".join(map(str, k)): v for k, v in events.items()}, f, indent=2, ensure_ascii=False)
            messagebox.showinfo("Success", "Events exported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to export events: {e}")

def import_events():
    filepath = filedialog.askopenfilename(filetypes=[("JSON Files", "*.json"), ("All Files", "*.*")])
    if filepath:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                raw = json.load(f)
                imported_events = {}
                for key, value in raw.items():
                    imported_events[tuple(map(int, key.split("-")))] = [
                        (
                            event[0], 
                            event[1] if isinstance(event, (list, tuple)) and len(event) > 1 else '#cccccc',
                            event[2] if isinstance(event, (list, tuple)) and len(event) > 2 else "",
                            event[3] if isinstance(event, (list, tuple)) and len(event) > 3 else 2
                        )
                        for event in value
                    ]
                events.update(imported_events)
                save_events()
                set_calendar()
                messagebox.showinfo("Success", "Events imported successfully.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to import events: {e}")

# GUI Setup
root = tk.Tk()
root.title("Shamsi Calendar")
root.geometry("1000x700")

# Themes
light_theme = {
    "root_bg": "#f0f0f0",
    "top_bg": "#ffffff",
    "calendar_bg": "#f9f9f9",
    "button_bg": "#dddddd",
    "button_fg": "black",
    "entry_bg": "white",
    "entry_fg": "black",
    "label_bg": "#f0f0f0",
    "label_fg": "black"
}
dark_theme = {
    "root_bg": "#2e2e2e",
    "top_bg": "#3c3f41",
    "calendar_bg": "#2e2e2e",
    "button_bg": "#4d4d4d",
    "button_fg": "white",
    "entry_bg": "#4d4d4d",
    "entry_fg": "white",
    "label_bg": "#3c3f41",
    "label_fg": "white"
}

theme = light_theme
style = ttk.Style()
dark_mode_var = tk.BooleanVar(value=False)

container = tk.Frame(root)
container.pack(expand=True, fill="both")

calendar_frame = tk.Frame(container, bg=theme["calendar_bg"])
calendar_frame.pack(expand=True, fill="both")

top_frame = tk.Frame(container, bg=theme["top_bg"])
top_frame.pack(pady=10)

tk.Label(top_frame, text="Year:", bg=theme["top_bg"], fg=theme["label_fg"]).pack(side=tk.LEFT)
year_entry = tk.Entry(top_frame, width=6, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground="white")
year_entry.pack(side=tk.LEFT)

tk.Label(top_frame, text="Month:", bg=theme["top_bg"], fg=theme["label_fg"]).pack(side=tk.LEFT)
month_entry = tk.Entry(top_frame, width=4, bg=theme["entry_bg"], fg=theme["entry_fg"], insertbackground="white")
month_entry.pack(side=tk.LEFT)

view_mode = tk.StringVar(value="month")
tk.Radiobutton(top_frame, text="Single Month", variable=view_mode, value="month",
               bg=theme["top_bg"], fg=theme["label_fg"], selectcolor=theme["calendar_bg"]).pack(side=tk.LEFT, padx=10)
tk.Radiobutton(top_frame, text="Full Year", variable=view_mode, value="year",
               bg=theme["top_bg"], fg=theme["label_fg"], selectcolor=theme["calendar_bg"]).pack(side=tk.LEFT)

tk.Button(top_frame, text="Show Calendar", command=set_calendar, bg=theme["button_bg"], fg=theme["button_fg"]).pack(side=tk.LEFT, padx=10)

tk.Checkbutton(top_frame, text="Dark Mode", variable=dark_mode_var, command=toggle_dark_mode,
               bg=theme["top_bg"], fg=theme["label_fg"], selectcolor=theme["calendar_bg"], activebackground=theme["top_bg"], activeforeground=theme["label_fg"]).pack(side=tk.LEFT, padx=10)

# Create a menu bar
menubar = tk.Menu(root)
root.config(menu=menubar)

# Create a File menu
file_menu = tk.Menu(menubar, tearoff=0)
menubar.add_cascade(label="File", menu=file_menu)

# Add Import, Export, and Delete All Events options to the File menu
file_menu.add_command(label="Import Events", command=import_events)
file_menu.add_command(label="Export Events", command=export_events)
file_menu.add_command(label="Delete All Events", command=delete_all_events)

load_events()
last_year, last_month = load_settings()
if last_year and last_month:
    year_entry.insert(0, str(last_year))
    month_entry.insert(0, str(last_month))
else:
    year_entry.insert(0, str(today_jdate.year))
    month_entry.insert(0, str(today_jdate.month))

set_calendar()

root.bind("<Left>", lambda e: change_month(-1))
root.bind("<Right>", lambda e: change_month(1))

root.mainloop()