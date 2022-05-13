from collections import namedtuple
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER, GLFW_MOD_CONTROL
from kitty.utils import path_from_osc7_url
from log import logger
from os.path import normpath
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
    return ' vis ' in w.title or w.title.startswith('vis')

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

def cwd_in_win(win):
    cwd = win.screen.last_reported_cwd
    if cwd is None:
        raise Exception(f"Couldn't find cwd for win {win}")
    return path_from_osc7_url(cwd)

def abspath_in_win(win, fn):
    cwd = cwd_in_win(win)
    l.info('cwd=%s fn=%s', cwd, fn)
    if not fn.startswith('/'):
        fn = f'{cwd}/{fn}'
    l.info('fn=%s, np=%s', fn, normpath(fn))
    return normpath(fn)

def edit(boss, fn, line=0, col=0, back=False):
    # active_window_for_cwd uses the base of the active window group. If a kitten is running, active_window is an overlay on top of the window that invoked the kitten
    fn = abspath_in_win(boss.active_window_for_cwd, fn)
    h = history(boss.active_tab)
    if line == 0 and col == 0:
        for idx, (past_fn, past_line, past_col) in enumerate(h.locations):
            if past_fn == fn:
                l.info("Found past edit of %s, using its line and col", fn)
                h.locations.pop(idx)
                if idx < h.idx:
                    h.idx -= 1
                line = past_line
                col = past_col
                break
    address_cmd = f'{line}#{col}'
    l.info("Edit %s:%s back=%s", fn, address_cmd, back)

    if is_vis_window(boss.active_window_for_cwd):
        l.info("Using active for edit")
        edit_win = boss.active_window_for_cwd
    else:
        edit_win = find_vis_window(boss)
        l.info("Finding for edit found %s", edit_win)
        if edit_win is None:
            run_in_shell(boss.active_window_for_cwd, f"vis +{address_cmd} '{fn}'")
            return

    current_loc, modified, mode = parse_status(edit_win)
    current_loc = Location(abspath_in_win(edit_win, current_loc.fn), current_loc.line, current_loc.col)
    if mode != 'NORMAL':
        # Use C-x to exit normal mode to avoid weirdness with escdelay in vis
        edit_win.write_to_child(edit_win.encoded_key(KeyEvent(key=ord('x'), mods=GLFW_MOD_CONTROL)))
    if modified:
        _send_command(edit_win, 'w')
    h.locations.insert(h.idx, current_loc)
    if not back:
        h.idx += 1
    l.info("After edit history is %s idx %s", h.locations, h.idx)
    _send_command(edit_win, f'e {fn}')
    _send_command(edit_win, address_cmd)

def move(boss, direction):
    h = history(boss.active_tab)
    l.info("Before move %s history is %s idx is %s", direction, h.locations, h.idx)
    dest = h.forward() if direction == "forward" else h.back()
    if dest is None:
        l.info("No history in that direction, skippin'")
        return
    edit(boss, *dest, back=direction=='back')
