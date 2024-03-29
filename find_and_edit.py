import importer

importer.reload_catherd_modules()
from log import logger
from kittens.ssh.main import connection_sharing_args
from kittens.tui.handler import result_handler
from nav import cwd_in_win, edit
from os import getpid

l = logger("catherd.edit")


def main(args):
    pass


@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        open_window(boss)
    except:
        l.exception("edit blew chunks!")


def open_window(boss):
    win = boss.active_window
    cwd = cwd_in_win(win)

    kwargs = {}
    ssh_kitten_cmdline = win.ssh_kitten_cmdline()
    if ssh_kitten_cmdline:
        # Use ssh directly rather than the ssh kitten as the ssh kitten has to send a bunch of
        # setup stuff we don't need that is noticeably slow
        cmd = ["ssh"]
        # Use the ssh kitten's control socket though to keep from having to create a connection
        cmd.extend(connection_sharing_args(getpid()))
        # Request a tty so we can interact with fzf, assume the final arg to the ssh kitten is the
        # hostname, and cd into the current remote directory. SSH joins all trailing arguments with
        # a space and passes them to the user's shell, so starting with cd like this gets us to the
        # right place
        cmd.extend(["-t", ssh_kitten_cmdline[-1], f"cd {cwd};"])
    else:
        kwargs["cwd"] = cwd
        # `ssh command` implicitly runs the user's shell with -c, so we need to do that explicitly for local execution
        # https://unix.stackexchange.com/a/332467
        cmd = ["fish", "-c"]

    # Pass the command to fish as a single string so it'll do interpolation
    cmd.append(f"source ~/dev/catherd/fzf_fd.fish")

    l.info("Running cmd=%s with kwargs=%s", cmd, kwargs)
    new_win = boss.active_tab.new_window(cmd=cmd, overlay_for=win.id, **kwargs)

    def on_close_wrapper(b, w, d):
        try:
            on_close(b, w, d, cwd)
        except:
            l.exception("on_close no bueno")

    new_win.watchers.on_close.append(on_close_wrapper)


def on_close(boss, window, data, cwd):
    res = window.kitten_result
    if res["returncode"] != 0:
        l.info("Non-zero returncode %s", res["returncode"])
        return
    edit(boss, f'{cwd}/{res["stdout"]}')
