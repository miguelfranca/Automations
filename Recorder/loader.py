from pynput import mouse
from pynput import keyboard
import subprocess
import platform
if platform.system() == 'Windows':
    from win10toast import ToastNotifier

from pynput.keyboard import Key

import os.path
import time
import sys
import re
import datetime
import ctypes

stop = False

# regexes
grouping_regex = r'^(.*) (.*): ([A-Za-z]*\_[A-Za-z]*) (.*)$'
coordinates_regex = r'^\((.*), (.*)\)$'
mouse_click_release_regex = r'^\((.*), (.*)\) with (.*)$'
mouse_scroll_regex = r'^\((.*), (.*)\)\((.*), (.*)\)$'

# grouping indexes
COORD_X = 1
COORD_Y = 2

MOUSE_BUTTON = 3

SCROLL_X = 3
SCROLL_Y = 4

DATE = 1
TIME = 2
OPERATION = 3
PARAM = 4

# inputs
count_down_seconds = 3
REPLAY_SPEED = 1.0
NUM_LOOPS = 1
filename = ""

# input controllers
keyboard_controller = keyboard.Controller()
mouse_controller = mouse.Controller()

def removeArgument(argv, a1, a2 = ""):
    try:
        argv.remove(argv[argv.index(a1) + 1])
        argv.remove(a1)
        return argv
    except IndexError as e:
        pass
    except ValueError as e:
        if(a2 != ''):
            try:
                argv.remove(argv[argv.index(a2) + 1])
                argv.remove(a2)
                return argv
            except ValueError as e:
                pass
            except IndexError as e:
                pass
    
    help()
    quit()

def getArgument(argv, param1, param2 = ''):
    try:
        arg = argv[argv.index(param1) + 1]
        return arg
    except IndexError as e:
        print('Option ' + param1 + ' misused...')
    except ValueError as e:
        if(param2 != ''):
            try:
                arg = argv[argv.index(param2) + 1]
                return arg
            except ValueError as e:
                pass
            except IndexError as e:
                print('Option ' + param2 + ' misused...')
    
    help()
    quit()

def optionsHandler(argv, num_required_arguments):
    global count_down_seconds, REPLAY_SPEED, NUM_LOOPS, filename

    if('-h' in argv or '--help' in argv):
        help()
        quit()
    
    if('-c' in argv or '--countdown_seconds' in argv):
        count_down_seconds = int(getArgument(argv, '-c', '--countdown_seconds'))
        argv = removeArgument(argv, '-c', '--countdown_seconds')

    if('-s' in argv or '--replay_speed' in argv):
        REPLAY_SPEED = float(getArgument(argv, '-s', '--replay_speed'))
        argv = removeArgument(argv, '-s', '--replay_speed')

    if('-l' in argv or '--loop' in argv):
        NUM_LOOPS = int(getArgument(argv, '-l', '--loop'))
        argv = removeArgument(argv, '-l', '--loop')

    if('-f' in argv or '--file' in argv):
        filename = getArgument(argv, '-f', '--file')
        argv = removeArgument(argv, '-f', '--file')

    if(len(argv) > num_required_arguments):
        c = [c for i, c in enumerate(argv) if c.find('-') != -1 and i > num_required_arguments - 1]
        if(len(c) != 0):
            print("invalid option(s) " + str(c))
        requestHelp()
        quit()

    if(len(argv) < num_required_arguments):
        print("Not enough arguments...\n")
        help()
        quit()

    return argv

def countDown(seconds):
    print("Starting in")
    
    print(seconds)
    for i in reversed(range(seconds)):
        time.sleep(1.0)
        print(i)

def sendNotification(message):
    if platform.system() == 'Windows':
        toaster = ToastNotifier()
        toaster.show_toast("Recorder", message, duration=5)
    else:
        subprocess.Popen(['notify-send', message])
    return

def handleSpecialKeys(key):
    return getattr(keyboard.Key, key.replace('Key.', ''))

def adjustMousePosition(x, y):
    if platform.system() == 'Windows':
        # Get the screen resolution on Windows
        user32 = ctypes.windll.user32
        screen_width = user32.GetSystemMetrics(0)
        screen_height = user32.GetSystemMetrics(1)
    else:
        # Get the screen resolution on Linux
        import subprocess
        output = subprocess.check_output(['xrandr']).decode('utf-8')
        for line in output.split('\n'):
            if '*' in line:
                screen_width, screen_height = map(int, line.split()[0].split('x'))
                break

    # Adjust the mouse position based on the screen resolution
    # This is a simple scaling example; you may need more complex logic
    x = int(x * screen_width / 1920)  # Assuming 1920x1080 as the reference resolution
    y = int(y * screen_height / 1200)

    return x, y

def executeOp(op_str):
    matcher = lineMatcher(op_str)
    op = matcher.group(OPERATION)
    param = matcher.group(PARAM)
    param = param.strip("'")

    try:
        if(param == "<65437>"): # numpad number 5 for some reason
            param = "5"
        if(param == "<65027>"): # alt_gr
            param = Key.alt_gr
        param = handleSpecialKeys(param)
    except:
        pass

    if(op == "key_released"):
        keyboard_controller.release(param)
        return
    if(op == "key_pressed"):
        keyboard_controller.press(param)
        return

    if(op == "Mouse_moved"):
        matcher = re.search(coordinates_regex, param)
        pos_x = int(matcher.group(COORD_X))
        pos_y = int(matcher.group(COORD_Y))
        pos_x, pos_y = adjustMousePosition(pos_x, pos_y)
        mouse_controller.position = (pos_x, pos_y)
        time.sleep(0.01)  # Small delay to keep the cursor visible
    
        return

    if(op == "Mouse_scrolled"):
        matcher = re.search(mouse_scroll_regex, param)
        pos_x = int(int(matcher.group(COORD_X)))
        pos_y = int(matcher.group(COORD_Y))
        scroll_x = int(matcher.group(SCROLL_X))
        scroll_y = int(matcher.group(SCROLL_Y))
        pos_x, pos_y = adjustMousePosition(pos_x, pos_y)
        mouse_controller.position = (pos_x, pos_y)
        mouse_controller.scroll(scroll_x, scroll_y)
        time.sleep(0.01)  # Small delay to keep the cursor visible
    
        return

    matcher = re.search(mouse_click_release_regex, param)
    pos_x = int(matcher.group(COORD_X))
    pos_y = int(matcher.group(COORD_Y))
    mouse_button = matcher.group(MOUSE_BUTTON)
    
    if(mouse_button == "Button.left"):
        mouse_button = mouse.Button.left
    elif(mouse_button == "Button.right"):
        mouse_button = mouse.Button.right
    elif(mouse_button == "Button.middle"):
        mouse_button = mouse.Button.middle
    
    pos_x, pos_y = adjustMousePosition(pos_x, pos_y)
    mouse_controller.position = (pos_x, pos_y)
    if(op == "Mouse_clicked"):
        mouse_controller.press(mouse_button)
    elif(op == "Mouse_released"):
        mouse_controller.release(mouse_button)
    
    return
    

def lineMatcher(line_str):
    return re.search(grouping_regex, line_str)

def parseTimeString(time_str):
    return datetime.datetime.strptime(time_str, '%H:%M:%S,%f')

def replay(lines):
    keyboard_listener = keyboard.Listener(on_press=on_press)
    keyboard_listener.start()

    num_lines = len(lines)
    
    first_line = lines[0]
    matcher = lineMatcher(first_line)

    first_line_time_str = matcher.group(TIME)
    first_line_time = parseTimeString(first_line_time_str)

    line_time = first_line_time

    init = datetime.datetime.now()

    i = 0
    while(i < num_lines and not stop):
        line = lines[i]
        matcher = lineMatcher(line)
        line_time_str = matcher.group(TIME)
        line_time = parseTimeString(line_time_str)
        while(datetime.datetime.now() - init < (line_time - first_line_time) / REPLAY_SPEED and not stop):
            # waiting for correct timing
            continue

        executeOp(line)
        i += 1   
        
    keyboard_listener.stop()
    keyboard_listener.join() 

def on_press(key):
    global stop
    if key == Key.esc:
        stop = True
        return False
    return True

def main(argv):
    global file, filename
    
    argv = optionsHandler(argv, 0)

    if(filename == ""):
        file = "log_1.txt"
        counter = 1
        while (os.path.isfile(file)):
            filename = file
            counter += 1
            file = "log_" + str(counter) + ".txt"
    else:
        filename = os.path.join(os.path.dirname(os.path.abspath(__file__)), filename)

    log_file = open(filename, 'r')
    log_lines = log_file.readlines()
    
    print("Replaying " + filename + ", " + str(NUM_LOOPS) + " times at " + str(REPLAY_SPEED) + "x speed")
    countDown(count_down_seconds)

    if(NUM_LOOPS == -1):
        while not stop:
            replay(log_lines)
    else:
        for i in range(0, NUM_LOOPS):
            replay(log_lines)

    log_file.close()

    sendNotification("Finished playback.")

def requestHelp():
    print("Use loader.py -h/--help to get help")

def help():
    print("Usage: script.py <filename> [OPTIONS]...")
    print("Playback all user input (mouse + keyboard) stored in a file")
    print()
    print("   -c\t--countdown_seconds\tspecify the number of seconds for countdown before replay starts")
    print("   -s\t--replay_speed\t\t")
    print("   -l\t--loop\t\t\tthe number of replays, -1 for infinite replays")
    print("   -f\t--file\t\t\tspecify the file that contains the replay")
    print()
    print("If -f is omitted the replay file will be the last 'log_X.txt'")
    print("Example: loader.py -s 1.7 -l -1 -f replay.txt")
    print("")

if __name__ == "__main__":
    main(sys.argv[1:])