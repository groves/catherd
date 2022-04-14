import importer
importer.reload_catherd_modules()
from log import logger
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_FKEY_UP, GLFW_MOD_CONTROL
from kittens.tui.handler import result_handler

l = logger('catherd.reterm')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        reterm(boss)
    except:
        l.exception("reterm blew chunks!")


keys = [KeyEvent(key=ord('c'), mods=GLFW_MOD_CONTROL),
    KeyEvent(key=GLFW_FKEY_UP),
    KeyEvent(key=GLFW_FKEY_ENTER)]

_id_attr = '_catherd.reterm.window_id'
def reterm(boss):
    win = boss.active_window
    tab = boss.active_tab
    window_id = getattr(tab, _id_attr, None)
    for possible in tab.windows:
        if possible.id == window_id:
            win = possible
            l.debug("Found previous win %s", win)
            break
    else:
        l.debug("Trying active win %s", win)
    if win is None:
        return
    setattr(tab, _id_attr, win.id)
    encoded_keys = b''.join(win.encoded_key(key) for key in keys)
    win.write_to_child(encoded_keys)
