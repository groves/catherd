from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from re import finditer
from log import logger
from nav import edit
from os.path import abspath, exists

l = logger('catherd.hint_rg')

def mark(text, args, Mark, extra_cli_args, *a):
    idx = 0
    fn = None
    for m in finditer('((?P<line>\d+):.*|.*)', text):
        line = m.group().replace('\0', '')
        if exists(line):
            fn = abspath(line)
        elif fn and m.group('line'):
            start, end = m.span()
            yield Mark(idx, start, end, line, {'line':int(m.group('line')) - 1, 'fn':fn})
            idx += 1

def handle_result(args, data, target_window_id, boss, extra_cli_args, *a):
    try:
        edit(boss, **data['groupdicts'][0])
    except:
        l.exception('hint_rg blew chunks!')
