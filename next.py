from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from log import logger
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER
from kittens.tui.handler import result_handler

l = logger('catherd.next')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        next_match(boss, args)
    except:
        l.exception('next blew chunks!')

def find_ate_window(boss):
    for possible in boss.active_tab.windows:
        if 'ate' in possible.title.split(' '):
            return possible
    return None

def next_match(boss, args):
    key = 'n' if args[1] == 'next' else 'N'
    if (win := find_ate_window(boss)) is None:
        l.warn("No ate, no next")
        return
    l.info("Sending %s to %s", key, win)
    win.write_to_child(win.encoded_key(KeyEvent(key=ord(key))))
    win.write_to_child(win.encoded_key(KeyEvent(key=GLFW_FKEY_ENTER)))
