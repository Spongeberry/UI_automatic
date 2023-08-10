import tkinter as tk
from tkinter import filedialog
import tkinter.messagebox as messagebox
import threading
from pynput import mouse, keyboard
import time
from pynput.keyboard import Listener as KeyListener, Key
from pynput.mouse import Button
import csv
from collections import deque
import os
import random
import configparser
import Levenshtein
from datetime import datetime
import pytz

# Global variable to control recording and replaying
control = {'record': False, 'replay': False, 'events': []}
expected_value = []
ctrl_pressed = False  # To keep track of whether 'ctrl' is currently being pressed
# Buffer list to store imported files
buffer_list = []
split_character = "@.@"
comparison_counter = 0
config_file_path = ""

# Final playlist (deque) to store the files to be played
final_playlist = deque()

binding_files = []
num_times = 1
allowed_difference = float()
program_start_time = time.time()

# Record handler
def on_action(x, y, button, pressed):
    event = ('click', x, y, button, pressed, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse clicked at ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse clicked at ({x}, {y}) time {time.time() - program_start_time}')
    return True

def on_scroll(x, y, dx, dy):
    event = ('scroll', x, y, dx, dy, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse scrolled at ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse scrolled at ({x}, {y}) time {time.time() - program_start_time}')
    return control['record']

def on_move(x, y):
    event = ('move', x, y, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse moved to ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse moved to ({x}, {y}) time {time.time() - program_start_time}')
    return control['record']

def on_press(key):
    global ctrl_pressed
    event = ('key_press', key, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Key {key} pressed at time {time.time() - program_start_time}')
    log(f'Key {key} pressed at time {time.time() - program_start_time}')
    return control['record']

def on_release(key):
    global ctrl_pressed
    event = ('key_release', key, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Key {key} released time {time.time() - program_start_time}')
    log(f'Key {key} released time {time.time() - program_start_time}')
    return control['record']

def on_press_esc(key):
    if key == Key.esc:
        control['replay'] = False
        log("Replay interrupted by pressing Esc key.")

def start_recording():
    control['record'] = True
    control['events'] = [('start', time.time() - program_start_time)]
    threading.Thread(target=record_events).start()
    log("Recording started...")

def stop_recording():
    control['record'] = False
    log("Recording stopped...")

def record_events():
    with mouse.Listener(on_move=on_move, on_click=on_action, on_scroll=on_scroll) as mouse_listener:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
            while control['record']:  # Keep running as long as record is True
                time.sleep(0.01)  # Add some sleep to prevent busy-waiting

            mouse_listener.stop()
            keyboard_listener.stop()

def clear_recordings():
    control['events'] = []


def log(message):
    console.config(state=tk.NORMAL)
    console.insert(tk.END, message + "\n")
    console.see(tk.END)  # Auto-scroll
    console.config(state=tk.DISABLED)

def save_config_to_csv():
    global expected_value, config_file_path, binding_files, num_times, allowed_difference, final_playlist, buffer_list
    current_directory = os.path.dirname(os.path.abspath(__file__))
    config_file_path = filedialog.askopenfilename(initialdir=current_directory, title="Select Config File", filetypes=[("CSV files", "*.txt")])
    if config_file_path:
        binding_files, num_times, expected_value, allowed_difference = read_expected_values_from_csv(config_file_path)
        update_expected_value_list()
        number_entry.insert(0, num_times)
        buffer_list = []
        final_playlist = deque()
        for file in binding_files:
            try:
                buffer_list.append(file)
            except:
                pass
        update_buffer_display()
        submit_to_playlist()
        number_entry.delete(0, tk.END)
        #somefunction

def read_expected_values_from_csv(csv_file):
    config = configparser.ConfigParser(interpolation=None) # Add this argument
    config.read(csv_file)

    binding_files = [value for key, value in config['binding'].items() if key.startswith('value')]
    num_times = int(config['times']['value'])
    allowed_difference = config['allowed difference']['value'].strip("%")

    # Extracting expected values and appending to a list
    expected_values = [value for key, value in config['value'].items() if key.startswith('expected value')]

    print("Binding file:", binding_files)
    print("Number of times:", num_times)
    print("Expected values:", expected_values)
    print("Allowed difference:", allowed_difference, "%")
    return binding_files, num_times, expected_values, allowed_difference


def string_difference_percentage(str1, str2, percentage):
    distance = Levenshtein.distance(str1, str2)
    length = max(len(str1), len(str2))
    if length == 0:
        return True
    difference_percentage = (distance / length) * 100

    return difference_percentage <= float(percentage)

# Function to update the expected_value list in the display area
def update_expected_value_list():
    expected_value_text.config(state=tk.NORMAL)
    expected_value_text.delete('1.0', tk.END)
    for value in expected_value:
        expected_value_text.insert(tk.END, value + "\n")
    expected_value_text.config(state=tk.DISABLED)

    
def save_events():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    events_file = filedialog.asksaveasfilename(defaultextension=".txt", initialdir=current_directory)
    if events_file:
        with open(events_file, 'w', newline='') as f:  # Open in write mode with 'newline'
            writer = csv.writer(f)
            writer.writerows(control['events'])  # Write the data to the file
        log(f"Events saved to {events_file}")

def select_and_replay_events_file():
    global comparison_counter
    current_directory = os.path.dirname(os.path.abspath(__file__))
    events_file = filedialog.askopenfilename(defaultextension=".txt", initialdir=current_directory)
    if events_file:
        control['replay'] = True
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]
        tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(tz)
        filename = current_time.strftime("report-%Y-%m-%d   %H_%M_%S.txt")
        comparison_counter = 0
        threading.Thread(target=replay_events, args=(events_data, filename)).start()
        log(f"Replaying events from {events_file}...")

def replay_events(events_data, filename):
    
    if not events_data[-1]:  # Check if the last element is empty
        events_data.pop()
    global ctrl_pressed, expected_value, comparison_counter


    mouse_controller = mouse.Controller()
    keyboard_controller = keyboard.Controller()

    # Start a listener for the escape key in a new thread
    escape_listener = KeyListener(on_press=on_press_esc)
    escape_listener.start()

    old_time = float(events_data[0][-1])
    
    for event in events_data:
        if not control['replay']:
            break

        time_difference = float(event[-1]) - old_time
        print("time difference:", time_difference)
        time.sleep(max(0, time_difference))
        old_time = float(event[-1])
        event_type = event[0]

        if event_type == 'move':
            mouse_controller.position = (int(event[1]), int(event[2]))
            log(f'Mouse moved to ({event[1]}, {event[2]}) at time {time.time() - program_start_time}')
        elif event_type == 'click':
            if event[4] == 'True':
                mouse_controller.press(eval(event[3]))
                log(f'Mouse button {event[3]} pressed at ({event[1]}, {event[2]}) at time {time.time() - program_start_time}')
            else:
                mouse_controller.release(eval(event[3]))
                log(f'Mouse button {event[3]} released at ({event[1]}, {event[2]}) at time {time.time() - program_start_time}')
        elif event_type == 'scroll':
            mouse_controller.scroll(int(event[3]), int(event[4]))
            log(f'Mouse scrolled at ({event[1]}, {event[2]}) at time {time.time() - program_start_time}')
        elif event_type == 'key_press':
            keyboard_controller.press(eval(event[1]))
            log(f'Key {event[1]} pressed at time {time.time() - program_start_time}')
            if event[1] == 'Key.ctrl_l':
                ctrl_pressed = True
            if event[1] == '\'\\x03\'' and control['replay'] and ctrl_pressed:
                try:
                    expected_value[0]
                except:
                    result = messagebox.askyesno("Error", "You have not enter or the expected value has run out, do you wish to continue?")
                    if result:
                        keyboard_controller.press(Key.ctrl)
                        keyboard_controller.press('c')
                        keyboard_controller.release('c')
                        keyboard_controller.release(Key.ctrl)
                        continue
                    else:
                        messagebox.showinfo("Error", "Replay stopped")
                        control["replay"] = False
                        return
                keyboard_controller.press(Key.ctrl)
                keyboard_controller.press('c')
                keyboard_controller.release('c')
                keyboard_controller.release(Key.ctrl)
                time.sleep(0.1)
                try:
                    clipboard_data = root.clipboard_get()
                except:
                    log("nothing in the clipboard")
                log(f"clipboard data: {clipboard_data}")
                log(f"expected value: {expected_value[0]}")
                with open(filename, "a", newline='') as report:
                    actual_value = clipboard_data
                    comparison_time = time.time()
                    row = [comparison_counter, expected_value[0], actual_value, comparison_time - program_start_time, str(allowed_difference) + "%"]
                    write_to_specific_row(filename, comparison_counter, row)
                    comparison_counter += 1
                if string_difference_percentage(expected_value[0], clipboard_data, allowed_difference):
                    expected_value.pop(0)
                    root.clipboard_clear()  # Clear the clipboard for future comparison (expected_value[1])
                    update_expected_value_list()
                else:
                    messagebox.showinfo("Replay Stopped", "Clipboard content does not match.\nOr maximum tolerance has exceeded\nReplaying has stopped.")
                    control["replay"] = False
                    return
            elif event[1] == '\'\\x01\'' and control['replay'] and ctrl_pressed:
                keyboard_controller.press(Key.ctrl)
                keyboard_controller.press('a')
                keyboard_controller.release('a')
                keyboard_controller.release(Key.ctrl)
            elif event[1] == '\'\\x16\'' and control['replay'] and ctrl_pressed:
                keyboard_controller.press(Key.ctrl)
                keyboard_controller.press('v')
                keyboard_controller.release('v')
                keyboard_controller.release(Key.ctrl)

        elif event_type == 'key_release':
            keyboard_controller.release(eval(event[1]))
            log(f'Key {event[1]} released at time {time.time() - program_start_time}')
            key = event[1]
            if key == 'Key.ctrl_l':
                ctrl_pressed = False
            
    escape_listener.stop()

def write_to_specific_row(file_path, row_number, data):
    # Read all the rows
    rows = []
    with open(file_path, 'r') as file:
        reader = csv.reader(file)
        rows = list(reader)

    # If the row number is greater than the length of the file, append empty rows.
    while len(rows) <= (row_number):
        rows.append([''] * len(data))

    # Replace the specific row with new data
    rows[row_number] = data

    # Write back the updated rows
    with open(file_path, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

    with open(file_path, "w", newline='') as file:
        writer = csv.writer(file)
        writer.writerows(rows)

def update_playlist_display():
    playlist_listbox.delete(0, tk.END)
    for file in final_playlist:
        playlist_listbox.insert(tk.END, file)

def update_buffer_display():
    buffer_listbox.delete(0, tk.END)
    for file in buffer_list:
        buffer_listbox.insert(tk.END, file)

def add_to_buffer():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    events_file = filedialog.askopenfilename(defaultextension=".txt", initialdir=current_directory)
    if events_file:
        buffer_list.append(events_file)
        update_buffer_display()
        log(f"Added {events_file} to the buffer.")

def remove_from_buffer(index):
    if 0 <= index < len(buffer_list):
        removed_file = buffer_list.pop(index)
        update_buffer_display()
        log(f"Removed {removed_file} from the buffer.")

def remove_from_playlist(index):
    if 0 <= index < len(final_playlist):
        removed_file = final_playlist[index]
        final_playlist.remove(final_playlist[index])
        update_playlist_display()
        log(f"Removed {removed_file} from the final playlist.")

def remove_selected_from_playlist():
    try:
        index = playlist_listbox.curselection()[0]
        remove_from_playlist(index)
    except IndexError:
        log("No item selected or other error occurred")

def submit_to_playlist():
    try:
        num_times = int(number_entry.get())
    except:
        num_times = 1
    for _ in range(num_times):
        final_playlist.extend(buffer_list)
    update_playlist_display()
    buffer_list.clear()
    update_buffer_display()
    log("Submitted buffer to the final playlist.")

def play_playlist():
    if not final_playlist:
        log("Final playlist is empty.")
        return
    threading.Thread(target=playback_process).start()

def playback_process():
    global comparison_counter
    log("Starting to play the final playlist...")
    control['replay'] = True
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(tz)
    filename = current_time.strftime("report  %Y-%m-%d  %H_%M_%S.txt")
    comparison_counter = 0
    while final_playlist and control['replay']:
        events_file = final_playlist.popleft()
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]
        # Call a function to handle the replaying of events_data here
        log(f"Replaying events from {events_file}...")
        replay_events(events_data, filename)
        update_playlist_display()
    control['replay'] = False
    log("Playback of the final playlist completed.")

# Create the tkinter interface
root = tk.Tk()
root.geometry('800x800')  # Set the window size

# First column: start recording, stop recording, save events, and select and replay event file
record_button = tk.Button(root, text="Start Recording", command=start_recording)
record_button.grid(row=0, column=0, padx=10, pady=10)
stop_button = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_button.grid(row=1, column=0, padx=10, pady=10)
save_button = tk.Button(root, text="Save Events", command=save_events)
save_button.grid(row=2, column=0, padx=10, pady=10)
select_button = tk.Button(root, text="Select and Replay Events File", command=select_and_replay_events_file)
select_button.grid(row=3, column=0, padx=10, pady=10)

load_config_button = tk.Button(root, text="Load Config", command=save_config_to_csv)
load_config_button.grid(row=3, column=1, padx=10, pady=10)

expected_value_text = tk.Text(root, state='disabled', height=10, width=30)
expected_value_text.grid(row=4, column=1, padx=10, pady=10)

# Third column: buffer display and number of times to submit to playlist
buffer_listbox = tk.Listbox(root, selectmode=tk.SINGLE)
buffer_listbox.grid(row=4, column=2, padx=10, pady=10, rowspan=4)

add_to_buffer_button = tk.Button(root, text="Add File to Buffer", command=add_to_buffer)
add_to_buffer_button.grid(row=0, column=2, padx=10, pady=10)

remove_from_buffer_button = tk.Button(root, text="Remove File from Buffer", command=lambda: remove_from_buffer(buffer_listbox.curselection()[0]))
remove_from_buffer_button.grid(row=1, column=2, padx=10, pady=10)

number_entry_label = tk.Label(root, text="Number of Times to Play:")
number_entry_label.grid(row=2, column=2, padx=10, pady=10)

number_entry = tk.Entry(root)
number_entry.grid(row=3, column=2, padx=10, pady=10)

# Fourth column: final playlist and play playlist
submit_to_playlist_button = tk.Button(root, text="Submit to Playlist", command=submit_to_playlist)
submit_to_playlist_button.grid(row=0, column=3, padx=10, pady=10)

playlist_listbox = tk.Listbox(root, selectmode=tk.SINGLE)
playlist_listbox.grid(row=4, column=3, padx=10, pady=10, rowspan=4)

remove_from_playlist_button = tk.Button(root, text="Remove File from Playlist", command=remove_selected_from_playlist)
remove_from_playlist_button.grid(row=1, column=3, padx=10, pady=10)


play_playlist_button = tk.Button(root, text="Play Playlist", command=play_playlist)
play_playlist_button.grid(row=2, column=3, padx=10, pady=10)

# Log area at the bottom
console = tk.Text(root, state='disabled')
console.grid(row=8, column=0, columnspan=4, padx=10, pady=10, sticky="we")

root.mainloop()