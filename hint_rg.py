from sys import path
if len(path) == 0 or path[0] != '/Users/groves/.config/kitty':
    path.insert(0, '/Users/groves/.config/kitty')
import importer
importer.reload_catherd_modules()
from re import finditer
from log import logger
from nav import abspath_in_win, edit

l = logger('catherd.hint_rg')

def mark(text, args, Mark, extra_cli_args, *a):
    idx = 0
    fn = None
    prev_line = None
    for m in finditer('(?P<line>((?P<line_num>\d+)(?P<line_type>:|-)|(?P<separator>--))?.*?)\0*\n', text):
        line = m.group('line')
        if m.group('line_num'):
            if prev_line is not None:
                fn = prev_line
                prev_line = None
            if fn and m.group('line_type') == ':':
                start, end = m.span()
                yield Mark(idx, start, end, line, {'line':int(m.group('line_num')), 'fn':fn})
                idx += 1
        elif m.group('separator'):
            continue
        else:
            prev_line = line

def handle_result(args, data, target_window_id, boss, extra_cli_args, *a):
    try:
        win = boss.window_id_map[target_window_id]
        result = data['groupdicts'][0]
        result['fn'] = abspath_in_win(win, result['fn'])
        edit(boss, **result)
    except:
        l.exception('hint_rg blew chunks!')
