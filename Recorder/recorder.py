from pynput import mouse
from pynput import keyboard
from pynput.keyboard import Key
import subprocess

import os.path
import sys
import time

import logging

import argparse

file = ""
filename_set = False
stop = False
count_down_seconds = 3
exit_key = "ctrl_r"

def removeArgument(argv, a1, a2 = ""):
    try:
        argv.remove(argv[argv.index(a1) + 1])
        argv.remove(a1)
        return argv
    except IndexError as e:
        argv.remove(a1)
        return argv
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

def optionsHandler(argv, required_arguments):
    global file, filename_set, count_down_seconds, stdout

    if('-h' in argv or '--help' in argv):
        help()
        quit()

    if('-o' in argv or '--save_as' in argv):
        filename_set = True
        file = getArgument(argv, '-o', '--save_as')
        argv = removeArgument(argv, '-o', '--save_as')


    if('-k' in argv or '--exit-key' in argv):
        exit_key = getArgument(argv, '-k', '--exit-key')
        argv = removeArgument(argv, '-k', '--exit-key')


    if('-c' in argv or '--countdown_seconds' in argv):
        count_down_seconds = int(getArgument(argv, '-c', '--countdown_seconds'))
        argv = removeArgument(argv, '-c', '--countdown_seconds')


    if('-stdout' in argv):
        filename_set = True
        file = ""
        argv = removeArgument(argv, '-stdout')

    if(len(argv) > required_arguments):
        c = [c for i, c in enumerate(argv) if c.find('-') != -1 and i > required_arguments - 1]
        if(len(c) != 0):
            print("invalid option(s) " + str(c))
        requestHelp()
        quit()

    if(len(argv) < required_arguments):
        print("Not enough arguments...")
        print()
        help()
        quit()

    return argv

def countDown(seconds):
    print("Starting recording in...")
    
    print(seconds)
    for i in reversed(range(seconds)):
        time.sleep(1.0)
        print(i)

def main(argv):
    global stop, file

    argv = optionsHandler(argv, 0)

    if(not filename_set):
        file = "log_1.txt"
        counter = 1;
        while (os.path.isfile(file)):
            counter += 1
            file = "log_" + str(counter) + ".txt"
    
    if os.path.exists(file):
        os.remove(file)

    logging.basicConfig(filename=file, level=logging.DEBUG, format='%(asctime)s: %(message)s')

    stop = False;

    mouse_listener = mouse.Listener(on_move=on_move, on_click=on_click, on_scroll=on_scroll)
    keyboard_listener = keyboard.Listener(on_press=on_press, on_release=on_release)

    if(file != ""):
        print("Writing to " + file)
        countDown(count_down_seconds)

    mouse_listener.start()
    keyboard_listener.start()

    keyboard_listener.join()
    if(stop):
        mouse_listener.stop()
    mouse_listener.join()

    sendNotification("Stopped recording.")
    print("Recording stopped.")

def sendNotification(message):
    subprocess.Popen(['notify-send', message])
    return

def on_release(key):
    logging.info('key_released {0}'.format(key))

def on_press(key):
    global stop
    if key == getattr(Key, exit_key):
        stop = True

        sendNotification("Stopped recording.")
        return False
    
    logging.info('key_pressed {0}'.format(key))


def on_move(x, y):
    if stop:
        return False;

    logging.info("Mouse_moved ({0}, {1})".format(x, y))

def on_click(x, y, button, pressed):
    if stop:
        return False;

    if pressed:
        logging.info('Mouse_clicked ({0}, {1}) with {2}'.format(x, y, button))
    if not pressed:
        logging.info('Mouse_released ({0}, {1}) with {2}'.format(x, y, button))

def on_scroll(x, y, dx, dy):
    if stop:
        return False;

    logging.info('Mouse_scrolled ({0}, {1})({2}, {3})'.format(x, y, dx, dy))

def requestHelp():
    print("Use recorder.py -h/--help to get help")

def help():
    print("Usage: script.py [OPTIONS]...")
    print("Record user input (mouse + keyboard)")
    print()
    print("   -o\t--save_as\t\tspecify the name of the file to write recordings to")
    print("   -stdout\t\t\t\tthe same as -o \"\", prints output to console")
    print("   -k\t--exit-key\t\tspecify the key that stops the recording")
    print("   -c\t--countdown_seconds\tset the number of seconds before starting to record")
    print("   \t\t\t\t(default is 1.0)")
    print()
    print("If -o is omitted the recording will be saved to a file like 'log_1.txt'")
    print("Examples: recorder.py -o recording.txt -c 2 -k ctrl_r")
    print("https://pythonhosted.org/pynput/_modules/pynput/keyboard/_base.html#Key")
    
if __name__ == "__main__":
    main(sys.argv[1:])

