from log import logger
from nav import edit
from os import environ
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
        edit(boss, fn)
    except:
        l.exception('edit blew chunks!')
