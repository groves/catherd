import importer
importer.reload_catherd_modules()
from log import logger
from kittens.tui.handler import result_handler
from nav import cwd_in_win, edit, history, is_vis_window, parse_status, run_in_shell
from os.path import relpath

l = logger('catherd.edit')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        open_window(boss)
    except:
        l.exception('edit blew chunks!')

def open_window(boss):
    win = boss.active_window
    cwd = cwd_in_win(win)
    # We start the shell instead of passing a command to use the shell's path
    new_win = boss.active_tab.new_window(use_shell=True, cwd=cwd, overlay_for=win.id)
    def on_close_wrapper(b, w, d):
        try:
            on_close(b, w, d)
        except:
            l.exception("on_close no bueno")
    new_win.watchers.on_close.append(on_close_wrapper)

    # Pull up to 10 files closest to the idx in history to print first for easy hopping
    recents = []
    def add_to_recent(idx):
        fn = relpath(h.locations[idx].fn, cwd)
        if fn not in recents:
            recents.append(fn)
    h = history(boss.active_tab)
    backidx = h.idx - 1
    foreidx = h.idx
    while len(recents) < 10 and (backidx >= 0 or foreidx < len(h.locations) - 1):
        if backidx >= 0:
            add_to_recent(backidx)
            backidx -= 1
        if foreidx < len(h.locations) - 1:
            add_to_recent(foreidx)
            foreidx += 1
    print_recents = f"""printf '%s\\n' '{"' '".join(recents)}'""" if recents else ''

    excludes = [r for r in recents if not r.startswith('..')]
    prox_sort = ''
    if is_vis_window(win):
        loc, _, _ = parse_status(win)
        if loc.fn not in excludes:
            excludes.append(loc.fn)
        prox_sort = f" | proximity-sort '{loc.fn}'" # Sort by proximity to the current file if there is one
    # Don't print any recents or the current file in fd
    exclusions = f""" --exclude '{"' --exclude '".join(excludes)}'""" if excludes else ''

    run_in_shell(new_win, f'''set -l stdout (
    begin
        {print_recents}
        fd --type file --hidden --follow --strip-cwd-prefix --exclude .git{exclusions}{prox_sort}
    end |
    fzf --tiebreak index
) ; \
python ~/dev/catherd/kitten-result.py $status "$stdout" ; \
exit''')

def on_close(boss, window, data):
    res = window.kitten_result
    if res["returncode"] != 0:
        l.info("Non-zero returncode %s", res["returncode"])
        return
    edit(boss, res["stdout"])
