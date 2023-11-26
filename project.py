from sys import path

if len(path) == 0 or path[0] != "/Users/groves/.config/kitty":
    path.insert(0, "/Users/groves/.config/kitty")
import importer

importer.reload_catherd_modules()
from log import logger, cache_dir
from kittens.tui.handler import result_handler
from nav import abspath_in_win, edit
from pathlib import Path
from subprocess import run, PIPE
from json import dump, load
from os.path import exists

l = logger("catherd.project")


proj_dirs = [
    Path(f"~/{d}").expanduser()
    for d in ["code", "dev", "code/idsb/stork", "code/idsb/.github"]
]
history_fn = f"{cache_dir}/project_history.json"


def fzf(options):
    completed = run(
        Path("~/.nix-profile/bin/fzf").expanduser(),
        input="\n".join(options).encode(),
        stdout=PIPE,
    )
    if completed.returncode == 130:
        l.info(f"fzf returned 130, assuming we hit escape")
        return None
    elif completed.returncode != 0:
        l.warn(f"fzf fzfailed: {completed}")
        return None
    return completed.stdout.decode().strip()


def proj_paths():
    return [p for d in proj_dirs for p in d.iterdir() if p.is_dir()]


def proj_names():
    return [p.name for d in proj_dirs for p in d.iterdir() if p.is_dir()]


def main(args):
    # Don't make the first item in history first as we're probably in that project
    history = load(open(history_fn))[1:] if exists(history_fn) else []
    all = proj_names()
    return fzf([h for h in history if h in all] + [p for p in all if p not in history])


@result_handler()
def handle_result(args, answer, target_window_id, boss):
    try:
        open_project(boss, answer, len(args) > 1 and args[1] == "attach")
    except:
        l.exception("project blew chunks!")


def find_proj(project):
    for d in proj_dirs:
        sub = d / project
        if sub.exists() and sub.is_dir():
            return sub
    raise Exception(f"No {project} dir in {proj_dirs}")


def open_project(boss, project, attach):
    project_dir = find_proj(project).as_posix() + "/"
    l.info(f"Opening {project_dir}")
    all_dirs = [p.as_posix() + "/" for p in proj_paths()]

    found = []
    for w in boss.all_windows:
        old_fore = w.child.get_foreground_cwd(oldest=True) + "/"
        longest_prefix = 0
        w_project = None
        for p in all_dirs:
            if old_fore.startswith(p) and len(p) > longest_prefix:
                longest_prefix = len(p)
                w_project = p
        matches = w_project == project_dir
        l.info(
            f"matches={matches} old_fore={old_fore} w_project={w_project} title={w.title} lfa={w.last_focused_at}"
        )
        if matches:
            found.append(w)
    if not found:
        boss.new_tab_with_wd(project_dir)
    else:
        w = sorted(found, key=lambda w: w.last_focused_at, reverse=True)[0]
        if attach:
            target_os_window_id = boss.active_tab.tab_manager_ref().os_window_id
            if w.tabref().tab_manager_ref().os_window_id != target_os_window_id:
                l.info(f"Moving existing to a tab for {project_dir}")
                boss._move_tab_to(w.tabref(), target_os_window_id=target_os_window_id)
            else:
                l.info(f"{project_dir} already in tab in current window, only focusing")
        boss.set_active_window(w, switch_os_window_if_needed=True)
    history = load(open(history_fn)) if exists(history_fn) else []
    all = proj_names()
    history = [project] + [p for p in history if p != project and p in all]
    dump(history, open(history_fn, "w"))
