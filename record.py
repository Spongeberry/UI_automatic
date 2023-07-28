import tkinter as tk
from tkinter import filedialog
import threading
from pynput import mouse, keyboard
from pynput.mouse import Button
import time
from pynput.keyboard import Listener as KeyListener, Key
import csv
from collections import deque
import os

# Global variable to control recording and replaying
control = {'record': False, 'replay': False, 'events': []}
expected_value = []
ctrl_pressed = False  # To keep track of whether 'ctrl' is currently being pressed
# Buffer list to store imported files
buffer_list = []

# Final playlist (deque) to store the files to be played
final_playlist = deque()


# Record handler
def on_action(x, y, button, pressed):
    event = ('click', x, y, button, pressed, time.time())
    control['events'].append(event)
    print(f'Mouse clicked at ({x}, {y}) time {time.time()}')
    log(f'Mouse clicked at ({x}, {y}) time {time.time()}')
    return control['record']

def on_scroll(x, y, dx, dy):
    event = ('scroll', x, y, dx, dy, time.time())
    control['events'].append(event)
    print(f'Mouse scrolled at ({x}, {y}) time {time.time()}')
    log(f'Mouse scrolled at ({x}, {y}) time {time.time()}')
    return control['record']

def on_move(x, y):
    event = ('move', x, y, time.time())
    control['events'].append(event)
    print(f'Mouse moved to ({x}, {y}) time {time.time()}')
    log(f'Mouse moved to ({x}, {y}) time {time.time()}')
    return control['record']

def on_press(key):
    global ctrl_pressed
    event = ('key_press', key, time.time())
    control['events'].append(event)
    print(f'Key {key} pressed at time {time.time()}')
    log(f'Key {key} pressed at time {time.time()}')
    return control['record']

def on_release(key):
    global ctrl_pressed
    event = ('key_release', key, time.time())
    control['events'].append(event)
    print(f'Key {key} released time {time.time()}')
    log(f'Key {key} released time {time.time()}')
    return control['record']

def on_press_esc(key):
    if key == Key.esc:
        control['replay'] = False
        log("Replay interrupted by pressing Esc key.")

def replay_events(events_data):
    global ctrl_pressed

    mouse_controller = mouse.Controller()
    keyboard_controller = keyboard.Controller()

    # Start a listener for the escape key in a new thread
    escape_listener = KeyListener(on_press=on_press_esc)
    escape_listener.start()

    start_time = float(events_data[0][-1])
    program_start_time = time.time()

    for event in events_data:
        if not control['replay']:
            break

        event_time = program_start_time + float(event[-1]) - start_time
        time.sleep(max(0, event_time - time.time()))
        event_type = event[0]

        if event_type == 'move':
            mouse_controller.position = (int(event[1]), int(event[2]))
            log(f'Mouse moved to ({event[1]}, {event[2]}) at time {time.time()}')
        elif event_type == 'click':
            if event[4] == 'True':
                mouse_controller.press(eval(event[3]))
                log(f'Mouse button {event[3]} pressed at ({event[1]}, {event[2]}) at time {time.time()}')
            else:
                mouse_controller.release(eval(event[3]))
                log(f'Mouse button {event[3]} released at ({event[1]}, {event[2]}) at time {time.time()}')
        elif event_type == 'scroll':
            mouse_controller.scroll(int(event[3]), int(event[4]))
            log(f'Mouse scrolled at ({event[1]}, {event[2]}) at time {time.time()}')
        elif event_type == 'key_press':
            keyboard_controller.press(eval(event[1]))
            log(f'Key {event[1]} pressed at time {time.time()}')
            if event[1] == 'Key.ctrl_l':
                print("setting ctrl press to True")
                ctrl_pressed = True
            if event[1] == '\'\\x03\'' and control['replay'] and ctrl_pressed:
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
                print(f"clipboard data: {clipboard_data}")
                log(f"expected value: {expected_value[0]}")
                print(f"expected value: {expected_value[0]}")
                if expected_value[0] == clipboard_data:
                    expected_value.pop(0)
                    root.clipboard_clear()  # Clear the clipboard for future comparison (expected_value[1])
                else:
                    print("Clipboard content does not match. Closing the application.")
                    root.destroy()
            elif event[1] == '\'\\x03\'' and control['replay'] and ctrl_pressed:
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
            log(f'Key {event[1]} released at time {time.time()}')
            key = event[1]
            if key == 'Key.ctrl_l':
                print("setting ctrl press to false")
                ctrl_pressed = False
            
    escape_listener.stop()

def start_recording():
    control['record'] = True
    control['events'] = [('start', time.time())]
    threading.Thread(target=record_events).start()
    log("Recording started...")

def stop_recording():
    control['record'] = False
    log("Recording stopped...")

def save_events():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    events_file = filedialog.asksaveasfilename(defaultextension=".txt", initialdir=current_directory)
    if events_file:
        with open(events_file, 'w', newline='') as f:  # Open in write mode with 'newline'
            writer = csv.writer(f)
            writer.writerows(control['events'])  # Write the data to the file
        log(f"Events saved to {events_file}")

def select_and_replay_events_file():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    events_file = filedialog.askopenfilename(defaultextension=".txt", initialdir=current_directory)
    if events_file:
        control['replay'] = True
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]

        # Print events_data to see its contents
        print("Events data:", events_data)

        threading.Thread(target=replay_events, args=(events_data,)).start()
        log(f"Replaying events from {events_file}...")


def record_events():
    with mouse.Listener(on_move=on_move, on_click=on_action, on_scroll=on_scroll) as mouse_listener, \
        keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
            mouse_listener.join()
            keyboard_listener.join()

def log(message):
    console.config(state=tk.NORMAL)
    console.insert(tk.END, message + "\n")
    console.see(tk.END)  # Auto-scroll
    console.config(state=tk.DISABLED)

def load_config():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    config_file_path = filedialog.askopenfilename(initialdir=current_directory, title="Select Config File", filetypes=[("Text files", "*.txt")])
    if config_file_path:
        expected_value.clear()
        read_expected_values_from_config(config_file_path)

def read_expected_values_from_config(config_file_path):
    if os.path.exists(config_file_path):
        with open(config_file_path, 'r') as f:
            sections = f.read().split('@.@')  # Split the file content based on '@.@' separator and empty line
            for section in sections:
                # Remove leading/trailing whitespaces and append the section to expected_value list
                expected_value.append(section.strip())
            update_expected_value_list()

# Function to update the expected_value list in the display area
def update_expected_value_list():
    expected_value_text.config(state=tk.NORMAL)
    expected_value_text.delete('1.0', tk.END)
    for value in expected_value:
        expected_value_text.insert(tk.END, value + "\n")
    expected_value_text.config(state=tk.DISABLED)

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

def submit_to_playlist():
    num_times = int(number_entry.get())
    for _ in range(num_times):
        final_playlist.extend(buffer_list)
    update_playlist_display()
    buffer_list.clear()
    update_buffer_display()
    log("Submitted buffer to the final playlist.")

def remove_from_playlist(index):
    if 0 <= index < len(final_playlist):
        removed_file = final_playlist.pop(index)
        update_playlist_display()
        log(f"Removed {removed_file} from the final playlist.")

def play_playlist():
    if not final_playlist:
        log("Final playlist is empty.")
        return

    log("Starting to play the final playlist...")
    control['replay'] = True
    while final_playlist and control['replay']:
        events_file = final_playlist.popleft()
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]
        replay_events(events_data)
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

load_config_button = tk.Button(root, text="Load Config", command=load_config)
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

remove_from_playlist_button = tk.Button(root, text="Remove File from Playlist", command=lambda: remove_from_playlist(playlist_listbox.curselection()[0]))
remove_from_playlist_button.grid(row=1, column=3, padx=10, pady=10)

play_playlist_button = tk.Button(root, text="Play Playlist", command=play_playlist)
play_playlist_button.grid(row=2, column=3, padx=10, pady=10)

# Log area at the bottom
console = tk.Text(root, state='disabled')
console.grid(row=8, column=0, columnspan=4, padx=10, pady=10, sticky="we")

root.mainloop()