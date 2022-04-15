import importer
importer.reload_catherd_modules()
from kittens.tui.handler import result_handler
from log import logger
from nav import parse_location, run_in_shell

l = logger('catherd.rg')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        rg(boss, args)
    except:
        l.exception("rg blew chunks!")


def _find_shell(boss):
    for possible in boss.active_tab.windows:
        if possible.child.foreground_processes[0]['cmdline'][0] == '-fish':
            return possible
    return None

def rg(boss, args):
    reference = args[1] == 'reference'
    declaration = args[1] == 'declaration'
    
    loc = parse_location(boss.active_window)
    ext = loc.fn.split('.')[-1]
    if ext == 'py':
        rg_type = 'py'
    elif ext in ['c', 'h']:
        rg_type = 'c'
    elif ext == 'lua':
        rg_type = 'lua'
    else:
        rg_type = None
    
    # Use the mouse selection as the ripgrep query if we don't have something more specific
    query = boss.active_window.text_for_selection()
    if query == '':
        l.info("Nothing selected, not querying")
        return
    # Haven't come up with a definition regexp for lua, so use the reference query for both styles for it
    if reference or rg_type == 'lua':
        if rg_type in ['py', 'lua', 'c']:
            query = f'(^|[ .@(&]){query}([^[[:alnum:]]_]|$)'
    elif declaration:
        if rg_type == 'py':
            query = f'''(def\s+{query}\(|(^|[ .]){query}\s*=|\[.{query}.]\s*=)'''
        elif rg_type == 'c':
            # This gets a word followed by a possible pointer declaration followed by the query word exactly.
            # It gets macro definitions as well as C declarations.
            # It'll pick up false positives like the query in a comment, but doing that feels better than 
            # making this super complicated.
            query = f'''(\w+\s+)\**{query}([^[[:alnum:]]_]|$)'''
    type_flag = f' --type {rg_type}' if rg_type is not None else ''
    cmd = f"rg --context 2 '{query}'{type_flag}"
    
    shell_win = _find_shell(boss)
    l.info("Got shell=%s, query=%s, loc=%s, rg_type=%s", shell_win, query, loc.fn, rg_type)
    if shell_win is None:
        l.info("No bare shell window, bailing")
        return
    
    run_in_shell(shell_win, cmd)
