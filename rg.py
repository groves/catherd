import importer
importer.reload_catherd_modules()
from kittens.tui.handler import result_handler
from log import logger
from nav import find_shell_window, is_vis_window, parse_status, run_in_shell, send_control_c

l = logger('catherd.rg')

def main(args):
    pass

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        rg(boss, args)
    except:
        l.exception("rg blew chunks!")


def rg(boss, args):
    reference = args[1] == 'reference'
    declaration = args[1] == 'declaration'
    
    def extract_query(win):
        query = win.text_for_selection()
        if query == '':
            return None, None, None
        if is_vis_window(win):
            loc, _, _ = parse_status(win)
            ext = loc.fn.split('.')[-1]
            if ext == 'py':
                rg_type = 'py'
            elif ext in ['c', 'h']:
                rg_type = 'c'
            elif ext == 'lua':
                rg_type = 'lua'
            return query, loc, rg_type
        return query, None, None

    # Look for a query in the active window first, then try the rest in the tab
    query, loc, rg_type = extract_query(boss.active_window)
    if query is None:
        for win in boss.active_tab.windows:
            query, loc, rg_type = extract_query(win)
            if query is not None:
                break
        else:
            l.info("No selection, not querying")
            return
    
    # Haven't come up with a definition regexp for lua, so use the reference query for both styles for it
    if reference or rg_type == 'lua':
        if rg_type in ['py', 'lua', 'c']:
            query = f'(^|[ .@(&!]){query}([^[[:alnum:]]_]|$)'
    elif declaration:
        if rg_type == 'py':
            query = f'''(def\s+{query}\(|(^|[ .]){query}\s*=|\[.{query}.]\s*=)'''
        elif rg_type == 'c':
            # This gets a word followed by a possible pointer declaration followed by the query word exactly.
            # It gets macro definitions as well as C declarations.
            # It'll pick up false positives like the query in a comment, but doing that feels better than 
            # making this super complicated.
            query = f'''(\w+\s+)\**{query}([^[[:alnum:]]_]|$)'''
    # We use the plain selection as the query if there's not something more specific
    type_flag = f' --type {rg_type}' if rg_type is not None else ''
    cmd = f"rg --context 2 '{query}'{type_flag}"
    
    shell_win = find_shell_window(boss)
    l.info("Got shell=%s, query=%s, loc=%s, rg_type=%s", shell_win, query, loc.fn if loc else None, rg_type)
    if shell_win is None:
        l.info("No bare shell window, bailing")
        return
    
    # Clear out any partial commands entered. TODO find a shell most recently used for rg that isn't running a command
    send_control_c(shell_win)
    run_in_shell(shell_win, cmd)
