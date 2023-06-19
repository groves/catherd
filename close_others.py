from sys import path

if len(path) == 0 or path[0] != "/Users/groves/.config/kitty":
    path.insert(0, "/Users/groves/.config/kitty")
import importer

importer.reload_catherd_modules()
from log import logger
from kittens.tui.handler import result_handler
from nav import abspath_in_win, edit

l = logger("catherd.close_others")


def main():
    pass


@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        close_others(boss)
    except:
        l.exception("close_others blew chunks!")


def close_others(boss):
    for tab in boss.active_tab_manager:
        if tab is not boss.active_tab:
            boss.close_tab_no_confirm(tab)
    for os_window_id, tm in boss.os_window_map.items():
        if tm != boss.active_tab_manager:
            boss.mark_os_window_for_close(os_window_id)
