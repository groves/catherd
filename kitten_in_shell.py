import importer
importer.reload_catherd_modules()
from log import logger
from kittens.tui.handler import result_handler
from nav import find_shell_window

l = logger('catherd.kitten_in_shell')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        kitten_in_shell(args, target_window_id, boss)
    except:
        l.exception("Chunks blown!")

_pre_shell_win_id = '_catherd.kitten_in_shell.previous_window_id'

def get_previous_window_id(boss):
    return getattr(boss, _pre_shell_win_id, None)

def kitten_in_shell(args, target_window_id, boss):
    setattr(boss, _pre_shell_win_id, target_window_id)
    win = find_shell_window(boss)
    boss.run_kitten_with_metadata(args[1], window=win)
