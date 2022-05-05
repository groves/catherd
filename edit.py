import importer
importer.reload_catherd_modules()
from log import logger
from nav import cwd_in_win, edit, parse_status, run_in_shell
from kittens.tui.handler import result_handler

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
    loc, _, _ = parse_status(win)
    # We start the shell instead of passing a command to use the shell's path
    new_win = boss.active_tab.new_window(use_shell=True, cwd=cwd_in_win(win), overlay_for=win.id)
    def on_close_wrapper(b, w, d):
        try:
            on_close(b, w, d)
        except:
            l.exception("on_close no bueno")
    new_win.watchers.on_close.append(on_close_wrapper)
    run_in_shell(new_win,
        f'''set -l stdout (fd --type file --hidden --follow --exclude .git | proximity-sort {loc.fn} | fzf --tiebreak index ) ; python ~/dev/catherd/kitten-result.py $status "$stdout"; exit''')

def on_close(boss, window, data):
    res = window.kitten_result
    if res["returncode"] != 0:
        l.info("Non-zero retcode %s", res["returncode"])
        return
    edit(boss, res["stdout"])
