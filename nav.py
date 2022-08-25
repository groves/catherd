from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_MOD_CONTROL
from kitty.utils import path_from_osc7_url
from log import logger
from os.path import normpath
from re import compile

l = logger('catherd.nav')

def is_editor_window(w):
    EDITOR_NAMES = ['hx', 'HELIX_RUNTIME']
    title = w.title
    if title.startswith('['):
        title = title[title.find('] ') + 2:]
    for name in EDITOR_NAMES:
        if f' {name} ' in title or title.startswith(name) or title.startswith(f'./{name}'):
            return True
    return False

def find_editor_window(boss):
    for possible in boss.active_tab.windows:
        if is_editor_window(possible):
            return possible
    return None

def is_shell_window(possible):
    # Fish titles are ([remote hostname] )? (process other than fish running )? (cwd starting with ~ or /)
    title = possible.title
    if title.startswith('['):
        title = title[title.find(']') + 2:]
    words = title.split(' ')
    l.info('Possible title=%s, words=%s', possible.title, words)
    return len(words) == 1 or words[1].startswith('~') or words[1].startswith('/') or words[0] == 'git'

def find_shell_window(boss):
    if is_shell_window(boss.active_window):
        return boss.active_window
    for possible in boss.active_tab.windows:
        if is_shell_window(possible):
            return possible
    return None

_status_re = compile(' (?P<mode>INS|NOR|SEL) . (?P<fn>.+?)(?P<modified>\[\+\])?      .+')
def parse_status(win):
    for line in reversed(win.as_text().split('\n')[-5:]):
        m = _status_re.search(line)
        if not m:
            continue
        mode, fn, modified = m.groups()
        l.info('Found %s %s modified=%s', fn, mode, modified)
        return fn, modified is not None, mode
    raise Exception(f"Couldn't find status in any line in {win}")

def _send_keys(w, keys):
    encoded = b''.join(w.encoded_key(KeyEvent(key=ord(c))) for c in keys)
    w.write_to_child(encoded)

import time
_enter = KeyEvent(key=GLFW_FKEY_ENTER)
def _send_command(w, command):
    l.info("Sending command '%s'", command)
    _send_keys(w, 'o')
    # Send with bracketed paste as helix is slow on input
    w.write_to_child(b'\x1b[200~')
    w.write_to_child(command)
    w.write_to_child(b'\x1b[201~')
    w.write_to_child(w.encoded_key(_enter))

_ctrl_c = KeyEvent(key=ord('c'), mods=GLFW_MOD_CONTROL)
def send_control_c(win):
    win.write_to_child(win.encoded_key(_ctrl_c))

def run_in_shell(win, command):
    l.info("Running '%s' in %s", command, win)
    win.paste_text(command)
    win.write_to_child(win.encoded_key(_enter))

def cwd_in_win(win):
    cwd = win.screen.last_reported_cwd
    if cwd is None:
        raise Exception(f"Couldn't find cwd for win {win}")
    return path_from_osc7_url(cwd)

def abspath_in_win(win, fn):
    if not fn.startswith('/'):
        cwd = cwd_in_win(win)
        fn = f'{cwd}/{fn}'
    return normpath(fn)

def _minimal_address(boss, fn, line, col):
    # active_window_for_cwd uses the base of the active window group.
    # If a kitten is running, active_window is an overlay on top of the window that invoked the kitten
    cwd = cwd_in_win(boss.active_window_for_cwd)
    if fn.startswith(cwd):
        fn = fn[len(cwd) + 1:]
    address = fn
    if line > 1:
        address += f':{line}'
        if col > 1:
            address += f':{col}'
    return address

def edit(boss, fn, line=1, col=1):
    l.info("Edit %s:%s:%s", fn, line, col)
    if is_editor_window(boss.active_window_for_cwd):
        l.info("Using active for edit")
        edit_win = boss.active_window_for_cwd
    else:
        edit_win = find_editor_window(boss)
        l.info("Finding for edit found %s", edit_win)
        if edit_win is None:
            run_in_shell(boss.active_window_for_cwd, f"hx '{_minimal_address(boss, fn, line, col)}'")
            return
        boss.set_active_window(edit_win)

    _, modified, mode = parse_status(edit_win)
    if mode != 'NOR':
        # TODO See if this applies to helix
        # Use C-x to exit INS or SEL mode to avoid weirdness with escdelay in vis
        edit_win.write_to_child(edit_win.encoded_key(KeyEvent(key=ord('x'), mods=GLFW_MOD_CONTROL)))
    if modified:
        _send_command(edit_win, 'w')
    _send_command(edit_win, f'o {_minimal_address(boss, fn, line, col)}')
