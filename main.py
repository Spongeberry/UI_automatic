#使用了python pynput和tkinter的互动性制作的一款UI自动化屏幕录制工具
#到function replay events之前的function都是来处理录制逻辑的
#replay events之后的function是用来处理文件和目录的逻辑的
#tkinter是用来写一个最基础的UI，用来方便和脚本进行非代码端的互动
#每一个function都加了英文标注


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
import configparser
import Levenshtein
from datetime import datetime
import pytz


control = {'record': False, 'replay': False, 'events': []} # Global variable to control recording and replaying, events to record everything
expected_value = [] # After loading test file, the elements within the test file will be added to this list
ctrl_pressed = False # To keep track of whether 'ctrl' is currently being pressed
buffer_list = [] # Buffer list to store imported files
comparison_counter = 0 # sequence
config_file_path = "" # file path to the config file
record_expected_value = [] # load data into the list while recording
final_playlist = deque() # Final playlist (deque) to store the files to be played
binding_files = [] # files that bind to the current script
num_times = 1 # number of times the entire script should be run
allowed_difference = float() # the maximum tolerance avaiable for the comparison
program_start_time = time.time() # program start time
method = '' # comparison method
test_case_names = '' # the name for each test
directory_names = ['script', 'report', 'config', 'test'] # directorys should be created within the current working directory
for directory_name in directory_names:
    if not os.path.exists(directory_name):
        os.makedirs(directory_name)

config_file_path = os.path.join('config', 'config.txt')
config_content = """[tolerance]
value = 50

[default comparison]
value = =

[times]
value = 1

[mapping]
"""

if not os.path.exists(config_file_path):
    with open(config_file_path, 'w') as config_file:
        config_file.write(config_content)


# This function is called when a mouse action (click) occurs and logs the event.
def on_action(x, y, button, pressed):
    event = ('click', x, y, button, pressed, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse clicked at ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse clicked at ({x}, {y}) time {time.time() - program_start_time}')
    return True


# This function handles the mouse scroll event, logging the action and returning the recording status.
def on_scroll(x, y, dx, dy):
    event = ('scroll', x, y, dx, dy, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse scrolled at ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse scrolled at ({x}, {y}) time {time.time() - program_start_time}')
    return control['record']


# This function is called when the mouse is moved. It logs the movement and returns the recording status.
def on_move(x, y):
    event = ('move', x, y, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Mouse moved to ({x}, {y}) time {time.time() - program_start_time}')
    log(f'Mouse moved to ({x}, {y}) time {time.time() - program_start_time}')
    return control['record']


# This function handles key presses, capturing specific keys and logging the events.
def on_press(key):
    global ctrl_pressed, record_expectede_value
    try:
        if key.vk == 67 and control['record'] and ctrl_pressed:
            time.sleep(0.1)
            record_expected_value.append(root.clipboard_get())
            print(record_expected_value)
    except:
        pass
    if key == Key.esc:
        return control['record']
    if not control['record']:
        return False
    if key == Key.ctrl_l or key == Key.ctrl_r:
        ctrl_pressed = True
    event = ('key_press', key, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Key {key} pressed at time {time.time() - program_start_time}')
    log(f'Key {key} pressed at time {time.time() - program_start_time}')
    return control['record']


# This function is triggered on key release, logging the event and managing 'ctrl' key status.
def on_release(key):
    global ctrl_pressed
    if key == Key.ctrl_l or key == Key.ctrl_r:
        ctrl_pressed = False
    event = ('key_release', key, time.time() - program_start_time)
    control['events'].append(event)
    print(f'Key {key} released time {time.time() - program_start_time}')
    log(f'Key {key} released time {time.time() - program_start_time}')
    return control['record']


# This function listens for the 'esc' key press to interrupt the replay.
def on_press_esc(key):
    if key == Key.esc:
        control['replay'] = False
        log("Replay interrupted by pressing Esc key.")


# This function listens for the 'esc' key press to stop the recording.
def on_press_esc_1(key):
    if key == Key.esc:
        control['record'] = False
        log("Recording stopped by pressing Esc key.")
        root.deiconify()  # Show the window again


# This function runs in a separate thread to listen for the 'esc' key press.
def listen_for_esc():
    with KeyListener(on_press=on_press_esc_1) as listener:
        listener.join()


# This function starts the recording process by setting control variables and initiating event listeners.
def start_recording():
    global expected_value_list
    expected_value_list = []
    control['record'] = True
    control['events'] = [('start', time.time() - program_start_time)]
    threading.Thread(target=record_events).start()
    log("Recording started...")
    root.withdraw()  # Hide the window
    threading.Thread(target=listen_for_esc).start()  # Start listening for 'esc'


# This function stops the recording process and restores the main window.
def stop_recording():
    control['record'] = False
    log("Recording stopped...")
    root.deiconify()  # Show the window again


# This function records mouse and keyboard events, using listeners that run as long as recording is enabled.
def record_events():
    with mouse.Listener(on_move=on_move, on_click=on_action, on_scroll=on_scroll) as mouse_listener:
        with keyboard.Listener(on_press=on_press, on_release=on_release) as keyboard_listener:
            while control['record']:  # Keep running as long as record is True
                time.sleep(0.01)  # Add some sleep to prevent busy-waiting

            mouse_listener.stop()
            keyboard_listener.stop()


# This function clears the recorded events list.
def clear_recordings():
    control['events'] = []


# This function logs messages to a GUI console, managing the text display state and scrolling.
def log(message):
    console.config(state=tk.NORMAL)
    console.insert(tk.END, message + "\n")
    console.see(tk.END)  # Auto-scroll
    console.config(state=tk.DISABLED)


# This function open the test file and manages file dialog and data processing according to the config file.
def save_config_to_csv():
    global expected_value, config_file_path, binding_files, num_times, allowed_difference, final_playlist, buffer_list, method, test_case_names
    current_directory = os.path.dirname(os.path.abspath(__file__))
    test_directory = os.path.join(current_directory, 'test')

    test_file_path = filedialog.askopenfilename(initialdir=test_directory, title="Select Test File")
    if test_file_path:
        binding_files, num_times, expected_value, allowed_difference, method, test_case_names = read_expected_values_from_csv(test_file_path)
        update_expected_value_list()
        number_entry.insert(0, num_times)
        buffer_list = []
        final_playlist = deque()
        for file in binding_files:
            try:
                buffer_list.append(file)
            except:
                pass
        update_buffer_display() # updatet he buffer dispaly
        submit_to_playlist()  # load the buffer into the final playlist
        number_entry.delete(0, tk.END)


# This function acts like a helper function and it return the expected value to the caller.
def read_expected_values_from_csv(file_path):
    script_file_value = []
    times_value = ''

    # Lists to hold the values for the sequence, expected value, method, tolerance, and test case name
    expected_values = []
    methods = ''
    tolerances = ''
    test_case_names = ''

    with open(file_path, 'r') as f:
        # Reading the script file value
        line = f.readline().strip()
        if line.startswith("[script file]"):
            script_file_value.append(f.readline().strip().split('=')[-1].strip())
        line = f.readline()
        # Reading the times value
        line = f.readline().strip()
        if line.startswith("[times]"):
            times_value = f.readline().strip().split('=')[-1].strip()
        # Reading the CSV part
        while not f.readline().startswith('sequence'):
            pass
        reader = csv.reader(f)
        for row in reader:
            if row: # Check if the row is not empty
                sequence, value, method, tolerance, test_case_name = row
                expected_values.append(value)
                methods = method
                tolerances = (tolerance.strip("%"))
                test_case_names = test_case_name
    return script_file_value, times_value, expected_values, tolerances, methods, test_case_names


# This function calculates the Levenshtein distance between two strings as a percentage.
def string_difference(str1, str2):
    distance = Levenshtein.distance(str1, str2)
    length = max(len(str1), len(str2))
    if length == 0:
        return 0
    return (distance / length) * 100


# This function compares two strings based on the Levenshtein distance and a given percentage tolerance.
def string_difference_percentage(str1, str2, percentage):
    distance = Levenshtein.distance(str1, str2)
    length = max(len(str1), len(str2))
    if length == 0:
        return True
    difference_percentage = (distance / length) * 100
    return difference_percentage <= float(percentage)


# This function updates the expected_value list displayed in the GUI.
def update_expected_value_list():
    expected_value_text.config(state=tk.NORMAL)
    expected_value_text.delete('1.0', tk.END)
    for value in expected_value:
        expected_value_text.insert(tk.END, value + "\n")
    expected_value_text.config(state=tk.DISABLED)


# This function saves recorded events to a file, using a file dialog and CSV writer.
def save_events():
    global record_expected_value
    config_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config', 'config.txt')
    config = configparser.ConfigParser()
    config.read(config_path)
    tolerance = config['tolerance']['value'] #get the value by parsing the config file
    default_comparison = config['default comparison']['value'] #get the value by parsing the config file
    times_value = config['times']['value'] #get the value by parsing the config file
    current_directory = os.path.dirname(os.path.abspath(__file__))
    script_directory = os.path.join(current_directory, 'script')
    test_directory = os.path.join(current_directory, 'test')
    events_file = filedialog.asksaveasfilename(defaultextension=".txt", title="save script file", initialdir=script_directory)
    if events_file:
        with open(events_file, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerows(control['events'])  # Write the data to the file
        log(f"Events saved to {events_file}")

    if record_expected_value:
        test_file = filedialog.asksaveasfilename(defaultextension=".txt", title="save test file", initialdir=test_directory)
        if test_file:
            with open(test_file, 'w') as f:
                # Write the [script file] section
                f.write("[script file]\n")
                f.write(f"{events_file}\n")

                # Write the [times] section
                f.write(f"[times]\n{times_value}\n")
                # Write the header line
                header = "sequence, expected value, method, tolerance(%), test case name\n"
                f.write(header)

                # Write the data lines
                for index, value in enumerate(record_expected_value):
                    sequence = index + 1
                    expected_value = value
                    method = default_comparison
                    test_case_name = f"case{sequence}" # Modify this according to your naming scheme
                    line = f"{sequence},{expected_value},{method},{tolerance},{test_case_name}\n"
                    f.write(line)

    # Add the mapping
    mappings = dict(config['mapping'])
    max_mapping_number = max(int(key.replace('mapping', '')) for key in mappings.keys()) if mappings else 0
    next_mapping_key = f"mapping{max_mapping_number + 1}"
    with open(config_path, 'a') as f:
        f.write(f"{next_mapping_key} = {test_file} <===> {events_file}\n")


# Selects a specific script file and replays the events in it.
def select_and_replay_events_file():
    global comparison_counter
    current_directory = os.path.dirname(os.path.abspath(__file__))
    script_directory = os.path.join(current_directory, 'script')

    events_file = filedialog.askopenfilename(defaultextension=".txt", title="Select script to run", initialdir=script_directory)
    if events_file:
        control['replay'] = True
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]
        tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(tz)
        filename = current_time.strftime("report  %Y-%m-%d  %H_%M_%S.txt")
        comparison_counter = 0
        threading.Thread(target=replay_events, args=(events_data, filename)).start()
        log(f"Replaying events from {events_file}...")


# Replays the given events from a data file, performing actions such as mouse movement, clicks, and keyboard inputs.
def replay_events(events_data, filename):
    if not events_data[-1]:  # Check if the last element is empty
        events_data.pop()
    global ctrl_pressed, expected_value, comparison_counter, method

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
                clipboard_data = ''
                try:
                    clipboard_data = root.clipboard_get()
                    log(f"clipboard data: {clipboard_data}")
                except:
                    log("nothing in the clipboard")
                log(f"expected value: {expected_value[0]}")
                with open(filename, "a", newline='') as report:
                    actual_value = clipboard_data
                    comparison_time = time.time()
                    tz = pytz.timezone('Asia/Shanghai')
                    current_time = datetime.now(tz)
                    current_time = current_time.strftime("comparison time: %Y-%m-%d %H-%M-%S")
                    row = [comparison_counter, "expected value:" + expected_value[0], "actual value:" + actual_value, "string difference:" + str(round(string_difference(expected_value[0], clipboard_data), 2)) + "%", "comparison method:" + method, "test name:" + test_case_names,  current_time]
                    write_to_specific_row(filename, comparison_counter, row )
                    comparison_counter += 1
                if string_difference_percentage(expected_value[0], clipboard_data, allowed_difference):
                    expected_value.pop(0)
                    root.clipboard_clear()  # Clear the clipboard for future comparison (expected_value[1])
                    update_expected_value_list()
                else:
                    messagebox.showinfo("Replay Stopped", "Maximum tolerance has exceeded\nReplaying has stopped.")
                    control["replay"] = False
                    return
            elif event[1] == '\'\\x01\'' and control['replay'] and ctrl_pressed: # need a better logic for this part, I just can't find any better way to do this without manual inputs
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


# Writes a specific row to a CSV file. If the row number is greater than the length of the file, it appends empty rows.
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


# Updates the display of the playlist listbox in the GUI.
def update_playlist_display():
    playlist_listbox.delete(0, tk.END)
    for file in final_playlist:
        playlist_listbox.insert(tk.END, file)


# Updates the display of the buffer listbox in the GUI.
def update_buffer_display():
    buffer_listbox.delete(0, tk.END)
    for file in buffer_list:
        buffer_listbox.insert(tk.END, file)


# Adds a selected script file to the buffer list.
def add_to_buffer():
    current_directory = os.path.dirname(os.path.abspath(__file__))
    script_directory = os.path.join(current_directory, 'script')

    events_file = filedialog.askopenfilename(defaultextension=".txt", title="Select script to add to the buffer", initialdir=script_directory)
    if events_file:
        buffer_list.append(events_file)
        update_buffer_display()
        log(f"Added {events_file} to the buffer.")


# Removes a selected script file from the buffer list based on the given index.
def remove_from_buffer(index):
    if 0 <= index < len(buffer_list):
        removed_file = buffer_list.pop(index)
        update_buffer_display()
        log(f"Removed {removed_file} from the buffer.")


# Removes a selected file from the final playlist based on the given index.
def remove_from_playlist(index):
    if 0 <= index < len(final_playlist):
        removed_file = final_playlist[index]
        final_playlist.remove(final_playlist[index])
        update_playlist_display()
        log(f"Removed {removed_file} from the final playlist.")


# Removes the selected file from the final playlist based on the user's selection in the listbox.
def remove_selected_from_playlist():
    try:
        index = playlist_listbox.curselection()[0]
        remove_from_playlist(index)
    except IndexError:
        log("No item selected or other error occurred")


# Submits the contents of the buffer to the final playlist a specified number of times.
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


# Starts playing the final playlist by calling the playback_process function in a new thread.
def play_playlist():
    if not final_playlist:
        log("Final playlist is empty.")
        return
    threading.Thread(target=playback_process).start()


# The actual playback process for the final playlist, reading each event file and replaying the events.
def playback_process():
    global comparison_counter
    log("Starting to play the final playlist...")
    control['replay'] = True
    tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(tz)
    report_dir = os.path.join(os.getcwd(), "report")
    filename = os.path.join(report_dir, current_time.strftime("report  %Y-%m-%d  %H_%M_%S.txt"))
    comparison_counter = 0
    root.withdraw()
    while final_playlist and control['replay']:
        events_file = final_playlist.popleft()
        with open(events_file, 'r') as f:  # Open in read mode
            reader = csv.reader(f)
            events_data = [row for row in reader]
        # Call a function to handle the replaying of events_data here
        log(f"Replaying events from {events_file}...")
        replay_events(events_data, filename)
        update_playlist_display()
    root.deiconify()
    control['replay'] = False
    log("Playback of the final playlist completed.")

# Create the tkinter interface
root = tk.Tk()
root.geometry('600x750')  # Set the window size

# First column: start recording, stop recording, save events, and select and replay event file
record_button = tk.Button(root, text="Start Recording", command=start_recording)
record_button.grid(row=0, column=1, padx=10, pady=10)

save_button = tk.Button(root, text="Save Events", command=save_events)
save_button.grid(row=1, column=1, padx=10, pady=10)
select_button = tk.Button(root, text="Simply play script", command=select_and_replay_events_file)
select_button.grid(row=2, column=1, padx=10, pady=10)

load_config_button = tk.Button(root, text="Load Test", command=save_config_to_csv)
load_config_button.grid(row=3, column=1, padx=10, pady=10)

expected_value_text = tk.Text(root, state='disabled', height=10, width=30)
expected_value_text.grid(row=4, column=1, padx=10, pady=10)

# Second column: buffer display and number of times to submit to playlist
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

# Third column: final playlist and play playlist
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