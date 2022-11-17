from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from log import logger
from kittens.tui.handler import result_handler
from nav import abspath_in_win, edit

l = logger('catherd.edit')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        open_editor(boss, args)
    except:
        l.exception('edit blew chunks!')

def open_editor(boss, args):
    fn = args[1]
    line = 1
    col = 1
    if fn.startswith("file://"):
        fn = fn[len("file://"):]
        fn = fn[fn.index("/"):]
        anchor_idx = fn.find('#')
        if anchor_idx != -1:
            anchor = fn[anchor_idx + 1:]
            if ':' in anchor:
                line, col = [int(s) for s in anchor.split(':')]
            else:
                line = int(anchor)
            fn = fn[:anchor_idx]
    l.info("%s %s %s, %s", args, fn, line, col)
    fn = abspath_in_win(boss.active_window, fn)
    edit(boss, fn, line, col)
