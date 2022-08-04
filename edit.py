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
    fn = abspath_in_win(boss.active_window, args[1])
    edit(boss, fn)
