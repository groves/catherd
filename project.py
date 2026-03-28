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
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Thread
from typing import NamedTuple, Any

l = logger("catherd.project")


proj_dirs = [Path(f"~/{d}").expanduser() for d in ["code", "dev"]]
clod_dir = Path("~/clod").expanduser()
jj = Path("~/.nix-profile/bin/jj").expanduser()
history_fn = f"{cache_dir}/project_history.json"
clod_cache_fn = f"{cache_dir}/clod_info.json"


class WorkspaceInfo(NamedTuple):
    description: str
    changed: int
    on_main: bool


def fzf(options: list[str]) -> str | None:
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


jj_info_template = 'parents.map(|p| p.bookmarks().join(",") ++ "|||" ++ p.description().first_line()).join("") ++ "\n"'


def workspace_info(ws_dir: str) -> WorkspaceInfo:
    result = run(
        [str(jj), "log", "-r", "@", "--no-graph", "--summary", "-T", jj_info_template],
        cwd=ws_dir,
        stdout=PIPE,
        stderr=PIPE,
    )
    if result.returncode != 0:
        l.warning(f"jj failed in {ws_dir}: {result.stderr.decode().strip()}")
        return WorkspaceInfo("", 0, False)
    lines = result.stdout.decode().strip().split("\n")
    header = lines[0] if lines else ""
    parts = header.split("|||", 1)
    on_main = "main" in parts[0]
    description = parts[1] if len(parts) > 1 else ""
    changed = len([line for line in lines[1:] if line.strip()])
    return WorkspaceInfo(description, changed, on_main)


def clod_workspaces() -> list[tuple[str, Path]]:
    if not clod_dir.exists():
        return []
    tasks = []
    for repo in sorted(clod_dir.iterdir()):
        if not repo.is_dir() or not (repo / "main" / ".jj").exists():
            continue
        for ws in sorted(repo.iterdir()):
            if (
                ws.is_dir()
                and (ws.name == "main" or ws.name.isdigit())
                and (ws / ".jj").exists()
            ):
                tasks.append((f"{repo.name}/{ws.name}", ws))
    return tasks


def format_entry(ident: str, info: WorkspaceInfo | list[Any]) -> str:
    description, changed, on_main = info
    if changed == 0 and on_main:
        return f"{ident}  [unused]"
    return f"{ident}  ({changed} changed) {description[:50]}"


def clod_entries() -> list[str]:
    tasks = clod_workspaces()
    cache = load(open(clod_cache_fn)) if exists(clod_cache_fn) else {}
    return [
        format_entry(ident, cache[ident]) if ident in cache else ident
        for ident, _ in tasks
    ]


def update_history(project: str) -> None:
    history = load(open(history_fn)) if exists(history_fn) else []
    all_regular = set(proj_names())
    all_clod = {ident for ident, _ in clod_workspaces()}
    all_valid = all_regular | all_clod
    history = [project] + [p for p in history if p != project and p in all_valid]
    dump(history, open(history_fn, "w"))


def background_update(project: str) -> None:
    update_history(project)
    refresh_clod_cache()


def refresh_clod_cache() -> None:
    tasks = clod_workspaces()
    infos = {}
    with ThreadPoolExecutor() as executor:
        futures = {
            executor.submit(workspace_info, str(ws_dir)): ident
            for ident, ws_dir in tasks
        }
        for future in as_completed(futures):
            ident = futures[future]
            try:
                infos[ident] = list(future.result())
            except Exception:
                l.exception(f"Failed to get workspace info for {ident}")
                infos[ident] = ["", 0, False]
    dump(infos, open(clod_cache_fn, "w"))


def proj_paths() -> list[Path]:
    return [p for d in proj_dirs for p in d.iterdir() if p.is_dir()] + [
        ws for _, ws in clod_workspaces()
    ]


def proj_names() -> list[str]:
    return [p.name for d in proj_dirs for p in d.iterdir() if p.is_dir()]


def main(args: list[str]) -> str | None:
    history = load(open(history_fn))[1:] if exists(history_fn) else []
    regular = proj_names()
    clod = clod_entries()
    clod_by_ident = {e.split()[0]: e for e in clod}

    all_by_ident = {p: p for p in regular} | clod_by_ident
    ordered = []
    for h in history:
        if h in all_by_ident:
            ordered.append(all_by_ident[h])
    for ident in sorted(all_by_ident):
        if ident not in history:
            ordered.append(all_by_ident[ident])

    result = fzf(ordered)
    if result is None:
        return None
    return result.split()[0]


@result_handler()
def handle_result(
    args: list[str], answer: str | None, target_window_id: int, boss: Any
) -> None:
    try:
        open_project(boss, answer, len(args) > 1 and args[1] == "attach")
        if answer:
            Thread(target=background_update, args=(answer,), daemon=True).start()
    except:
        l.exception("project blew chunks!")


def find_proj(project: str) -> Path:
    if "/" in project:
        repo, ws = project.split("/", 1)
        sub = clod_dir / repo / ws
        if sub.exists() and sub.is_dir():
            return sub
        raise Exception(f"No clod workspace {project}")
    for d in proj_dirs:
        sub = d / project
        if sub.exists() and sub.is_dir():
            return sub
    raise Exception(f"No {project} dir in {proj_dirs}")


def open_project(boss: Any, project: str | None, attach: bool) -> None:
    if project is None:
        return
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
        boss.detach_tab()
    else:
        w = sorted(found, key=lambda w: w.last_focused_at)[0]
        if attach:
            target_os_window_id = boss.active_tab.tab_manager_ref().os_window_id
            if w.tabref().tab_manager_ref().os_window_id != target_os_window_id:
                l.info(f"Moving existing to a tab for {project_dir}")
                boss._move_tab_to(w.tabref(), target_os_window_id=target_os_window_id)
            else:
                l.info(f"{project_dir} already in tab in current window, only focusing")
        boss.set_active_window(w, switch_os_window_if_needed=True)
