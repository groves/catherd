from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from re import finditer
from log import logger
from nav import abspath_in_win, edit, find_shell_window
from kittens.tui.handler import result_handler

l = logger('catherd.linky')

OSC_8_REGEX = '\x1b]8;(?P<params>.*?);(?P<url>.+?)(?:#(?P<fragment>.*?))?\x1b\\\\(?P<contents>(?:.|\n)*?)\x1b]8;;\x1b\\\\'

def main(args) -> str:
    pass

def mark(text):
    last_line = -1
    for m in finditer(OSC_8_REGEX, text):
        l.info(m.groups())
        params, url, fragment, contents = m.group('params', 'url', 'fragment', 'contents')
        if url.startswith('file://'):
            fn_start = url.find('/', len('file://'))
            fn = url[fn_start:]
        elif url.startswith('delta://'):
            fn = url[len('delta://'):]
            # Only step to added lines i.e. ones with this green text
            if not contents.startswith('\x1b[38:5:28m '):
                continue
        else:
            l.info('Unknown url "%s", skipping', url)
            continue
        if fragment:
            line = int(fragment)
            # Skip over sequential lines
            sequential = last_line == line - 1
            if sequential:
                continue
            last_line = line
        else:
            line = 0
        yield {'line':line, 'fn':fn, 'col': 0}

@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    try:
        edit_next_link(boss)
    except:
        l.exception('Chunks blown!')

_last_marks_attr = '_catherd.hint_edit.last_marks'
_last_mark_idx_attr = '_catherd.hint_edit.last_mark_idx'
def edit_next_link(boss):
    win = find_shell_window(boss)
    marks = list(mark(win.as_text(as_ansi=True)))
    if len(marks) == 0:
        return
    last_marks = getattr(win, _last_marks_attr, [])
    last_mark_idx = getattr(win, _last_mark_idx_attr, 0)
    if last_marks == marks:
        l.info("Same marks, going to next from %s", last_mark_idx)
        mark_idx = last_mark_idx + 1
        if mark_idx == len(marks):
            mark_idx = 0
    else:
        l.info("%s new marks", len(marks))
        mark_idx = 0
    result = marks[mark_idx]
    fn = abspath_in_win(win, result['fn'])
    edit(boss, fn, result['line'], result['col'])
    setattr(win, _last_marks_attr, marks)
    setattr(win, _last_mark_idx_attr, mark_idx)
