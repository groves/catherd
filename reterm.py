from logging import basicConfig, DEBUG, getLogger
from os import makedirs
from os.path import expanduser
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_FKEY_UP, GLFW_MOD_CONTROL
from kittens.tui.handler import result_handler

log_dir = expanduser('~/.cache/catherd')
makedirs(log_dir, exist_ok=True)

basicConfig(filename=f'{log_dir}/log', filemode='a', format='%(asctime)s %(message)s',
    datefmt='%H:%M:%S', level=DEBUG)
logger = getLogger('catherd.reterm')
logger.debug('Loaded')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        reterm(boss)
    except:
        logger.exception("reterm blew chunks!")


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
            logger.debug("Found previous win %s", win)
            break
    else:
        logger.debug("Trying active win %s", win)
    if win is None:
        return
    setattr(tab, _id_attr, win.id)
    encoded_keys = b''.join(win.encoded_key(key) for key in keys)
    win.write_to_child(encoded_keys)
    logger.debug("Wrote keys")
