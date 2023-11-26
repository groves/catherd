# ruff: noqa: E402
import importer

importer.reload_catherd_modules()
from log import logger
from nav import send_control_c
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_FKEY_UP
from kittens.tui.handler import result_handler

l = logger("catherd.reterm")  # noqa: E741


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        reterm(boss)
    except Exception:
        l.exception("reterm blew chunks!")


keys = [KeyEvent(key=GLFW_FKEY_UP), KeyEvent(key=GLFW_FKEY_ENTER)]

_id_attr = "_catherd.reterm.window_id"


def reterm(boss):
    tab = boss.active_tab
    win = None
    window_id = getattr(tab, _id_attr, None)
    if boss.active_window.at_prompt:
        win = boss.active_window
        l.debug("At prompt %s", win)
    else:
        for possible in tab.windows:
            if possible.id == window_id:
                win = possible
                l.debug("Found previous win %s", win)
                break
        if win is None:
            l.warn("No window with known id, not at prompt, can't reterm")
            return
    setattr(tab, _id_attr, win.id)
    if boss.active_window.id != win.id:
        l.info("Blinking focus on %s", boss.active_window)
        # Sending focus lost and gained codes to get Helix to autosave
        # https://terminalguide.namepad.de/mode/p1004/
        boss.active_window.write_to_child(b"\x1b[O\x1b[I")
    send_control_c(win)
    encoded_keys = b"".join(win.encoded_key(key) for key in keys)
    win.write_to_child(encoded_keys)
