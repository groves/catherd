import logging
from log import logger
from os import environ
from kitty.fast_data_types import KeyEvent, GLFW_FKEY_ENTER
from subprocess import run, PIPE

l = logger('catherd.edit')

def main(args):
    # Run through SHELL to get its path
    process = run([environ['SHELL'], '--command', 'fzf'], stdout=PIPE)
    l.info("PROCESS %s", process)
    return {'returncode':process.returncode, "stdout":process.stdout.decode('utf-8')}

def handle_result(args, answer, target_window_id, boss):
    try:
        if answer['returncode'] != 0:
            l.info('Non-zero returncode %s, not editing', answer['returncode'])
            return
        fn = answer["stdout"].strip()
        w = boss.window_id_map.get(target_window_id)
        if w is not None:
            edit(w, fn)
    except:
        l.exception('edit blew chunks!')

enter = KeyEvent(key=GLFW_FKEY_ENTER)

def send_command(w, command):
    keys = b''.join(w.encoded_key(KeyEvent(key=ord(c))) for c in 'o' + command)
    w.write_to_child(keys)
    w.write_to_child(w.encoded_key(enter))

def edit(w, fn, linenum=None):
    if len(w.child.foreground_processes) == 1:
        process = w.child.foreground_processes[0]
        if process['cmdline'][0].endswith('/vis'):
            send_command(w, 'w')
            send_command(w, f'e {fn}')
            if linenum:
                send_command(w, f'{linenum}')
            return
    linenum_cmd = '' if linenum is None else f'+{linenum} '
    w.paste_text(f"vise {linenum_cmd}'{fn}'")
    w.write_to_child(w.encoded_key(enter))
