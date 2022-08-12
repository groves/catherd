from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from re import finditer
from log import logger
from nav import abspath_in_win, edit
from kittens.hints.main import DEFAULT_LINENUM_REGEX
from kittens.tui.handler import result_handler
from sys import stdin

l = logger('catherd.hint_edit')

PATH_LINE_COL_REGEX = rf'{DEFAULT_LINENUM_REGEX}(:(?P<col>\d+))'

def main(args) -> str:
    try:
        return list(mark())
    except:
        l.exception('Chunks blown!')

def mark():
    for m in finditer(PATH_LINE_COL_REGEX, stdin.read()):
        path, line, col = m.group('path', 'line', 'col')
        yield {'line':int(line), 'fn':path, 'col': int(col) if col is not None else 0}

@result_handler(type_of_input='output')
def handle_result(args, data, target_window_id, boss):
    try:
        edit_next_pathlike(data, target_window_id, boss)
    except:
        l.exception('Chunks blown!')

from kitten_in_shell import get_previous_window_id
_last_marks_attr = '_catherd.hint_edit.last_marks'
_last_mark_idx_attr = '_catherd.hint_edit.last_mark_idx'
def edit_next_pathlike(marks, target_window_id, boss):
    if len(marks) == 0:
        previous_active_window = get_previous_window_id(boss)
        l.info("No marks, restoring window %s", previous_active_window)
        if previous_active_window is not None:
            boss.switch_focus_to(previous_active_window)
        return
    tab = boss.active_tab
    last_marks = getattr(tab, _last_marks_attr, [])
    last_mark_idx = getattr(tab, _last_mark_idx_attr, 0)
    if last_marks == marks:
        l.info("Same marks, going to next from %s", last_mark_idx)
        mark_idx = last_mark_idx + 1
        if mark_idx == len(marks):
            mark_idx = 0
    else:
        l.info("New marks %s Old marks %s", marks, last_marks)
        mark_idx = 0
    win = boss.window_id_map[target_window_id]
    result = marks[mark_idx]
    fn = abspath_in_win(win, result['fn'])
    edit(boss, fn, result['line'], result['col'])
    setattr(tab, _last_marks_attr, marks)
    setattr(tab, _last_mark_idx_attr, mark_idx)
