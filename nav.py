from collections import namedtuple
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_MOD_CONTROL
from log import logger
from re import compile

l = logger('catherd.nav')

Location = namedtuple('Location', ['fn', 'line', 'col'])

class History:
    def __init__(self):
        self.locations = []
        self.idx = 0

    def back(self):
        if self.idx == 0:
            return None
        location = self.locations.pop(self.idx - 1)
        self.idx -= 1
        return location

    def forward(self):
        if self.idx == len(self.locations):
            return None
        return self.locations.pop(self.idx)

_id_attr = '_catherd.nav.history'
def history(tab):
    h = getattr(tab, _id_attr, None)
    if h is None:
        h = History()
        setattr(tab, _id_attr, h)
    return h

def is_vis_window(w):
    if len(w.child.foreground_processes) != 1:
        if len(w.child.foreground_processes) > 1:
            l.info('Found window with multiple foreground_processes, assuming not vis w=%s fp=%s', w, w.child.foreground_processes)
        return False
    process = w.child.foreground_processes[0]
    return process['cmdline'][0].endswith('/vis')

def find_vis_window(boss):
    for possible in boss.active_tab.windows:
        if is_vis_window(possible):
            return possible
    return None

_status_re = compile('\s*(?P<mode>INSERT » |VISUAL » |VISUAL-LINE » )?(?P<fn>.+?)(?P<modified> \[\+\])?\s+ (?:g « )?\d+% « (?P<line>\d+), (?P<col>\d+)\s*')
def parse_status(win):
    for line in reversed(win.as_text().split('\n')):
        l.info("Matching against %s", line)
        m = _status_re.match(line)
        if not m:
            continue
        mode, fn, modified, line, col = m.groups()
        if mode is not None:
            mode = mode.split(' ')[0]
        else:
            mode = 'NORMAL'
        l.info('Found %s:%s#%s %s modified=%s', fn, line, col, mode, modified)
        return Location(fn, int(line) - 1, int(col) - 1), modified is not None, mode
    raise Exception(f"Couldn't find status in any line in {win}")

_enter = KeyEvent(key=GLFW_FKEY_ENTER)
def _send_command(w, command):
    keys = b''.join(w.encoded_key(KeyEvent(key=ord(c))) for c in 'o' + command)
    w.write_to_child(keys)
    w.write_to_child(w.encoded_key(_enter))

def run_in_shell(win, command):
    l.info("Running '%s' in %s", command, win)
    win.paste_text(command)
    win.write_to_child(win.encoded_key(_enter))

def edit(boss, fn, line=0, col=0, back=False, relative_to_active=True):
    address_cmd = f'{line}#{col}'
    l.info("Edit %s:%s back=%s", fn, address_cmd, back)
    if is_vis_window(boss.active_window):
        l.info("Using active for edit")
        win = boss.active_window
    else:
        win = find_vis_window(boss)
        l.info("Finding for edit found %s", win)
        if win is None:
            run_in_shell(boss.active_window, f"vise +{address_cmd} '{fn}'")
            return
        if relative_to_active:
            active_cwd = boss.active_window.cwd_of_child
            if active_cwd is None:
                active_cwd = boss.active_window.child.cwd
            if active_cwd is not None:
                if not fn.startswith('/'):
                    fn = f'{active_cwd}/{fn}'
                else:
                    l.info("Couldn't find cwd for active win %s, not able to make fn %s relative to active", win, fn)
    current_loc, modified, mode = parse_status(win)
    if mode != 'NORMAL':
        # Use C-x to exit normal mode to avoid weirdness with escdelay in vis
        win.write_to_child(win.encoded_key(KeyEvent(key=ord('x'), mods=GLFW_MOD_CONTROL)))
    if modified:
        _send_command(win, 'w')
    h = history(boss.active_tab)
    h.locations.insert(h.idx, current_loc)
    if not back:
        h.idx += 1
    l.info("After edit history is %s idx %s", h.locations, h.idx)
    _send_command(win, f'e {fn}')
    _send_command(win, address_cmd)

def move(boss, direction):
    h = history(boss.active_tab)
    l.info("Before move %s history is %s idx is %s", direction, h.locations, h.idx)
    dest = h.forward() if direction == "forward" else h.back()
    if dest is None:
        l.info("No history in that direction, skippin'")
        return
    edit(boss, *dest, back=direction=='back', relative_to_active=False)
