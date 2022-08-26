from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from re import finditer, search
from log import logger
from nav import abspath_in_win, edit, find_shell_window
from kittens.tui.handler import result_handler

l = logger('catherd.linky')

OSC_START = '\x1b]'
ST = '\x1b\\\\'
OSC_8_OPEN = f'{OSC_START}8;(?P<params>.*?);(?P<url>.+?)(?:#(?P<fragment>.*?))?{ST}'
OSC_8_CONTENT = f'(?P<contents>(?:.|\n)*?)(?:{OSC_START}8;|$)'
OSC_133 = f'{OSC_START}133;(?P<command_type>[ACD]){ST}'

def main(args) -> str:
    pass

def mark_commands(text):
    pos = 0
    results = []
    def add_marks(subtext):
        marks = list(mark_command(subtext))
        if len(marks) > 0:
            results.append(marks)
    for m in finditer(OSC_133, text):
        command_type = m.group('command_type')
        if command_type == 'C':
            pos = m.end()
            l.info("Found C, moving to %s", pos)
        else:
            l.info("Found %s, marking to %s", command_type, m.start())
            add_marks(text[pos:m.start()])
            pos = m.end()
    if pos < len(text):
        l.info("Found end at %s, marking from %s", len(text), pos)
        add_marks(text[pos:])
    return results

def mark_command(text):
    last_line = -1
    for m in finditer(OSC_8_OPEN, text):
        params, url, fragment = m.group('params', 'url', 'fragment')
        contents = search(OSC_8_CONTENT, text[m.end():]).group('contents')
        if url.startswith('file://'):
            fn_start = url.find('/', len('file://'))
            fn = url[fn_start:]
        elif url.startswith('delta://'):
            fn = url[len('delta://'):]
            # Only step to chunk headers i.e. ones with this blue text
            if not contents.startswith('\x1b[34m'):
                l.info("Skipping %s", repr(contents))
                continue
        else:
            l.info('Unknown url "%s", skipping', url)
            continue
        if fragment:
            line = int(fragment)
            # Skip over sequential lines
            sequential = last_line == line - 1
            last_line = line
            if sequential:
                continue
        else:
            line = 0
        yield {'line':line, 'fn':fn, 'col': 0}

@result_handler(no_ui=True)
def handle_result(args, data, target_window_id, boss):
    try:
        edit_next_link(boss)
    except:
        l.exception('Chunks blown!')

_linky_attr = '_catherd.linky'
def edit_next_link(boss):
    win = find_shell_window(boss)
    # TODO - get full history, not just visible. add_history does that, but it doesn't include links.
    # Possible kitty bug?
    command_links = mark_commands(win.as_text(as_ansi=True))#, add_history=True))
    if len(command_links) == 0:
        return
    marks = command_links[-1]
    last_marks, last_mark_idx = getattr(win, _linky_attr, ([], 0))
    # TODO - continue walk if last_marks is a prefix of marks
    if last_marks == marks:
        l.info("Same marks, going to next from %s", last_mark_idx)
        mark_idx = last_mark_idx + 1
        if mark_idx == len(marks):
            mark_idx = 0
    else:
        l.info("%s new marks", len(marks))
        mark_idx = 0
    # TODO - scroll terminal to have this visible
    result = marks[mark_idx]
    fn = abspath_in_win(win, result['fn'])
    edit(boss, fn, result['line'], result['col'])
    setattr(win, _linky_attr, (marks, mark_idx))
