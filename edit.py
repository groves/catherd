import importer
importer.reload_catherd_modules()
from log import logger
from kittens.ssh.main import set_cwd_in_cmdline
from kittens.tui.handler import result_handler
from nav import cwd_in_win, edit, history, is_vis_window, parse_status
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

    kwargs = {}
    ssh_kitten_cmdline =  win.ssh_kitten_cmdline()
    if ssh_kitten_cmdline:
        cmd = ssh_kitten_cmdline
        set_cwd_in_cmdline(cwd, cmd)
        # Attach a tty to the shell since we want to interact with fzf
        cmd.append('-t')
    else:
        kwargs['cwd'] = cwd
        # `ssh command` implicitly runs the user's shell with -c, so we need to do that explicitly for local execution
        # https://unix.stackexchange.com/a/332467
        cmd = ['fish', '-c']

    args = []

    def escape_fn_for_args(fn):
        escaped_fn = fn.replace("'", "\\'")
        return f"'{escaped_fn}'"

    if is_vis_window(win):
        loc, _, _ = parse_status(win)
        args += ['--current', escape_fn_for_args(loc.fn)]

    # Pull up to 10 files closest to the idx in history to print first for easy hopping
    h = history(boss.active_tab)
    def append_history_to_args(idx):
        fn = h.locations[idx].fn
        fn = relpath(fn, cwd)
        escaped_fn = escape_fn_for_args(fn)
        if escaped_fn not in args:
            args.append(escaped_fn)
    backidx = h.idx - 1
    foreidx = h.idx
    while len(args) < 10 and (backidx >= 0 or foreidx < len(h.locations) - 1):
        if backidx >= 0:
            append_history_to_args(backidx)
            backidx -= 1
        if foreidx < len(h.locations) - 1:
            append_history_to_args(foreidx)
            foreidx += 1


    # Pass the command to fish as a single string so it'll do interpolation
    cmd.append(f'source ~/dev/catherd/fzf_fd.fish {" ".join(args)}')

    l.info("Running cmd=%s with kwargs=%s", cmd, kwargs)
    new_win = boss.active_tab.new_window(cmd=cmd, overlay_for=win.id, **kwargs)
    def on_close_wrapper(b, w, d):
        try:
            on_close(b, w, d)
        except:
            l.exception("on_close no bueno")
    new_win.watchers.on_close.append(on_close_wrapper)

def on_close(boss, window, data):
    res = window.kitten_result
    if res["returncode"] != 0:
        l.info("Non-zero returncode %s", res["returncode"])
        return
    edit(boss, res["stdout"])
