import re
from logging import basicConfig, DEBUG, getLogger
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER
from os import makedirs, environ
from os.path import exists, expanduser

log_dir = expanduser('~/.cache/catherd')
makedirs(log_dir, exist_ok=True)

basicConfig(filename=f'{log_dir}/log', filemode='a', format='%(asctime)s %(name)s %(message)s',
    datefmt='%H:%M:%S', level=DEBUG)

l = getLogger('catherd.hint_rg')

def mark(text, args, Mark, extra_cli_args, *a):
    idx = 0
    fn = None
    for m in re.finditer('((?P<linenum>\d+):.*|.*)', text):
        line = m.group().replace('\0', '')
        if exists(line):
            fn = line
        elif fn and m.group('linenum'):
            start, end = m.span()
            yield Mark(idx, start, end, line, {'linenum':int(m.group('linenum')), 'fn':fn})
            idx += 1

def find_window(boss):
    tab = boss.active_tab
    for possible in boss.active_tab.windows:
        if is_vis_window(possible):
            return possible
    return None

def handle_result(args, data, target_window_id, boss, extra_cli_args, *a):
    try:
        w = find_window(boss)
        l.info("Found %s", w)
        edit(boss, w, **data['groupdicts'][0])
    except:
        l.exception('hint_rg blew chunks!')

enter = KeyEvent(key=GLFW_FKEY_ENTER)

def send_command(w, command):
    keys = b''.join(w.encoded_key(KeyEvent(key=ord(c))) for c in 'o' + command)
    w.write_to_child(keys)
    w.write_to_child(w.encoded_key(enter))

def is_vis_window(w):
    if len(w.child.foreground_processes) != 1:
        if len(w.child.foreground_processes) > 1:
            l.info('Found window with multiple foreground_processes, assuming not vis w=%s fp=%s', w, w.child.foreground_processes)
        return
    process = w.child.foreground_processes[0]
    return process['cmdline'][0].endswith('/vis')
    
def edit(boss, w, fn, linenum=None):
    if w is not None:
        l.info("Editing %s in existing vis", fn)
        send_command(w, 'w')
        send_command(w, f'e {fn}')
        if linenum:
            send_command(w, f'{linenum}')
        return
    l.info('Not spawning new window for now, no good way to have it in a shell')
    return
    l.info("Editing %s in new vis", fn)
    linenum_cmd = '' if linenum is None else f'+{linenum} '
    boss.active_tab.new_window(cmd=[environ['SHELL'], "--command", f"vise {linenum_cmd}{fn}"])
