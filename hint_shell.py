import importer
importer.reload_catherd_modules()
from log import logger
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_FKEY_UP, GLFW_MOD_CONTROL
from kittens.tui.handler import result_handler
from nav import find_shell_window

l = logger('catherd.hint_shell')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        hint_shell(boss)
    except:
        l.exception("reterm blew chunks!")


def hint_shell(boss):
    win = find_shell_window(boss)
    args = ["--customize-processing", "hint_rg.py", "--alphabet", "abcdefghijklmnopqrstuvwxyz", "--hints-offset=0"]
    boss._run_kitten('hints',  args=args, window=win)
