import tkinter as tk
from tkinter import filedialog
import threading
from pynput import mouse, keyboard
from pynput.mouse import Button
import time
from pynput.keyboard import Listener as KeyListener, Key
import csv

# Global variable to control recording and replaying
control = {'record': False, 'replay': False, 'events': []}
expected_value = []
ctrl_pressed = False  # To keep track of whether 'ctrl' is currently being pressed

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
                clipboard_data = root.clipboard_get()
                log(f"clipboard data: {clipboard_data}")
                log(f"expected value: {expected_value[0]}")
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
    events_file = filedialog.asksaveasfilename(defaultextension=".txt")  # Save as text file
    if events_file:
        with open(events_file, 'w', newline='') as f:  # Open in write mode with 'newline'
            writer = csv.writer(f)
            writer.writerows(control['events'])  # Write the data to the file
        log(f"Events saved to {events_file}")

def select_and_replay_events_file():
    events_file = filedialog.askopenfilename(defaultextension=".txt")  # Select a text file
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


# Function to add an element to the expected_value list
def add_expected_value():
    value = expected_value_entry.get()
    if value.strip():
        expected_value.append(value)
        expected_value_entry.delete(0, tk.END)
        update_expected_value_list()

# Function to delete the last element from the expected_value list
def delete_last_expected_value():
    if expected_value:
        expected_value.pop()
        update_expected_value_list()

# Function to update the expected_value list in the display area
def update_expected_value_list():
    expected_value_text.config(state=tk.NORMAL)
    expected_value_text.delete('1.0', tk.END)
    for value in expected_value:
        expected_value_text.insert(tk.END, value + "\n")
    expected_value_text.config(state=tk.DISABLED)



root = tk.Tk()
root.geometry('400x600')  # Set the window size
record_button = tk.Button(root, text="Start Recording", command=start_recording)
record_button.pack()
stop_button = tk.Button(root, text="Stop Recording", command=stop_recording)
stop_button.pack()
save_button = tk.Button(root, text="Save Events", command=save_events)
save_button.pack()
select_button = tk.Button(root, text="Select and Replay Events File", command=select_and_replay_events_file)
select_button.pack()

# Entry for expected_value
expected_value_entry = tk.Entry(root)
expected_value_entry.pack()

# Buttons to add and delete elements from the expected_value list
add_button = tk.Button(root, text="Add Expected Value", command=add_expected_value)
add_button.pack()
delete_button = tk.Button(root, text="Delete Last Expected Value", command=delete_last_expected_value)
delete_button.pack()

# Text area to display the expected_value list
expected_value_text = tk.Text(root, state='disabled', height=10, width=30)
expected_value_text.pack()


console = tk.Text(root, state='disabled')
console.pack(expand=True, fill='both')

root.mainloop()
