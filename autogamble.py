import ctypes
import time
import win32api
import win32con
from ctypes import wintypes
import json
import threading

user32 = ctypes.WinDLL('user32', use_last_error=True)

# Virtual key codes for all keys we want to record
KEYS_TO_RECORD = {
    0x57: 'W',  # W
    0x41: 'A',  # A
    0x53: 'S',  # S
    0x44: 'D',  # D
    0x20: 'SPACE',  # Spacebar
    0x10: 'SHIFT',  # Shift
    0x11: 'CTRL',   # Control
    0x45: 'E',      # E
    0x51: 'Q',      # Q
    0x52: 'R',      # R
    0x46: 'F',      # F
}

class InputRecorder:
    def __init__(self):
        self.recorded_actions = []
        self.recording = False
        self.playing = False
        self.looping = False
        self.pressed_keys = set()
        
    def get_mouse_pos(self):
        return win32api.GetCursorPos()
        
    def set_mouse_pos(self, x, y):
        win32api.SetCursorPos((x, y))
        
    def mouse_event(self, flags, x=0, y=0, data=0):
        user32.mouse_event(flags, x, y, data, 0)
        
    def key_event(self, key, flags):
        user32.keybd_event(key, 0, flags, 0)
        
    def is_key_pressed(self, key):
        return win32api.GetAsyncKeyState(key) & 0x8000 != 0
        
    def record(self):
        print("Recording started (Press F5 to stop)...")
        self.recorded_actions = []
        self.recording = True
        last_pos = self.get_mouse_pos()
        
        while self.recording:
            # Check for keyboard inputs
            for key in KEYS_TO_RECORD:
                is_pressed = self.is_key_pressed(key)
                if is_pressed and key not in self.pressed_keys:
                    self.pressed_keys.add(key)
                    self.recorded_actions.append({
                        'type': 'key_down',
                        'key': key,
                        'name': KEYS_TO_RECORD[key],
                        'time': time.time()
                    })
                elif not is_pressed and key in self.pressed_keys:
                    self.pressed_keys.remove(key)
                    self.recorded_actions.append({
                        'type': 'key_up',
                        'key': key,
                        'name': KEYS_TO_RECORD[key],
                        'time': time.time()
                    })
                
            # Record mouse movement
            current_pos = self.get_mouse_pos()
            if current_pos != last_pos:
                self.recorded_actions.append({
                    'type': 'mouse_move',
                    'x': current_pos[0],
                    'y': current_pos[1],
                    'time': time.time()
                })
                last_pos = current_pos
            
            # Record mouse clicks
            left_click = self.is_key_pressed(win32con.VK_LBUTTON)
            right_click = self.is_key_pressed(win32con.VK_RBUTTON)
            
            if left_click:
                self.recorded_actions.append({
                    'type': 'mouse_click',
                    'button': 'left',
                    'time': time.time()
                })
            
            if right_click:
                self.recorded_actions.append({
                    'type': 'mouse_click',
                    'button': 'right',
                    'time': time.time()
                })
            
            time.sleep(0.01)
            
        print("Recording stopped!")
        
    def play(self):
        if not self.recorded_actions:
            print("No actions recorded!")
            return
        
        print(f"Playing recording (Press F6 to stop) - Loop mode: {'ON' if self.looping else 'OFF'}")
        self.playing = True
        
        while self.playing:  # Main loop for repeating playback
            start_time = time.time()
            action_time = self.recorded_actions[0]['time']
            
            # Reset all keys on start of each loop
            for key in self.pressed_keys:
                self.key_event(key, win32con.KEYEVENTF_KEYUP)
            self.pressed_keys.clear()
            
            for action in self.recorded_actions:
                if not self.playing:
                    # Release all pressed keys before stopping
                    for key in self.pressed_keys:
                        self.key_event(key, win32con.KEYEVENTF_KEYUP)
                    self.pressed_keys.clear()
                    break
                    
                # Wait for correct timing
                current_time = time.time()
                wait_time = (action['time'] - action_time) - (current_time - start_time)
                if wait_time > 0:
                    time.sleep(wait_time)
                
                # Perform action
                if action['type'] == 'mouse_move':
                    self.set_mouse_pos(action['x'], action['y'])
                
                elif action['type'] == 'mouse_click':
                    if action['button'] == 'left':
                        self.mouse_event(win32con.MOUSEEVENTF_LEFTDOWN)
                        time.sleep(0.01)
                        self.mouse_event(win32con.MOUSEEVENTF_LEFTUP)
                    else:
                        self.mouse_event(win32con.MOUSEEVENTF_RIGHTDOWN)
                        time.sleep(0.01)
                        self.mouse_event(win32con.MOUSEEVENTF_RIGHTUP)
                
                elif action['type'] == 'key_down':
                    self.key_event(action['key'], 0)
                    self.pressed_keys.add(action['key'])
                    print(f"Pressing {action['name']}")
                    
                elif action['type'] == 'key_up':
                    self.key_event(action['key'], win32con.KEYEVENTF_KEYUP)
                    self.pressed_keys.discard(action['key'])
                    print(f"Releasing {action['name']}")
            
            if not self.looping:
                break
            print("Loop complete, starting next iteration...")
                    
        self.playing = False
        print("Playback complete!")

def main():
    recorder = InputRecorder()
    print("Input Recorder started!")
    print("F5: Toggle Recording Start/Stop")
    print("F6: Toggle Playback Start/Stop")
    print("F7: Toggle Loop Mode ON/OFF")
    print("Recording these keys:", ', '.join(KEYS_TO_RECORD.values()))
    
    f5_was_pressed = False
    f6_was_pressed = False
    f7_was_pressed = False
    
    while True:
        f5_is_pressed = win32api.GetAsyncKeyState(win32con.VK_F5) & 0x8000
        f6_is_pressed = win32api.GetAsyncKeyState(win32con.VK_F6) & 0x8000
        f7_is_pressed = win32api.GetAsyncKeyState(win32con.VK_F7) & 0x8000
        
        # Handle F5 toggle (recording)
        if f5_is_pressed and not f5_was_pressed:
            if recorder.recording:
                recorder.recording = False
            else:
                thread = threading.Thread(target=recorder.record)
                thread.start()
        f5_was_pressed = f5_is_pressed
        
        # Handle F6 toggle (playback)
        if f6_is_pressed and not f6_was_pressed:
            if recorder.playing:
                recorder.playing = False
            else:
                thread = threading.Thread(target=recorder.play)
                thread.start()
        f6_was_pressed = f6_is_pressed
        
        # Handle F7 toggle (loop mode)
        if f7_is_pressed and not f7_was_pressed:
            recorder.looping = not recorder.looping
            print(f"Loop mode: {'ON' if recorder.looping else 'OFF'}")
        f7_was_pressed = f7_is_pressed
        
        time.sleep(0.01)

if __name__ == "__main__":
    main()