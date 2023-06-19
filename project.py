from sys import path

if len(path) == 0 or path[0] != "/Users/groves/.config/kitty":
    path.insert(0, "/Users/groves/.config/kitty")
import importer

importer.reload_catherd_modules()
from log import logger
from kittens.tui.handler import result_handler
from nav import abspath_in_win, edit
from pathlib import Path
from subprocess import run, PIPE

l = logger("catherd.project")


proj_dir_names = ["code", "dev"]
proj_dirs = [Path(f"~/{d}").expanduser() for d in proj_dir_names]


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


def main(args):
    return fzf(
        [p.name for d in proj_dirs for p in d.iterdir() if p.is_dir()] + proj_dir_names
    )


@result_handler()
def handle_result(args, answer, target_window_id, boss):
    try:
        open_project(boss, answer, len(args) > 1 and args[1] == "attach")
    except:
        l.exception("project blew chunks!")


def find_proj(project):
    if project in proj_dir_names:
        return Path(f"~/{project}").expanduser()
    for d in proj_dirs:
        sub = d / project
        if sub.exists() and sub.is_dir():
            return sub
    raise Exception(f"No {project} dir in {proj_dirs}")


def open_project(boss, project, attach):
    project_dir = find_proj(project).as_posix()
    l.info(f"Opening {project_dir}")

    found = None
    for w in boss.all_windows:
        old_fore = w.child.get_foreground_cwd(oldest=True)
        matches = old_fore.startswith(project_dir)
        l.info(
            f"{matches} {w.title} {old_fore} {w.child.get_foreground_cwd(oldest=False)} {w.child.cwd}"
        )
        if matches:
            found = w
    if not found:
        boss.new_tab_with_wd(project_dir)
    else:
        if attach:
            target_os_window_id = boss.active_tab.tab_manager_ref().os_window_id
            if found.tabref().tab_manager_ref().os_window_id != target_os_window_id:
                l.info(f"Moving existing to a tab for {project_dir}")
                boss._move_tab_to(
                    found.tabref(), target_os_window_id=target_os_window_id
                )
            else:
                l.info(f"{project_dir} already in tab in current window, only focusing")
        boss.set_active_window(found, switch_os_window_if_needed=True)
