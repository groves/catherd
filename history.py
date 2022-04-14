import importer
importer.reload_catherd_modules()
from kittens.tui.handler import result_handler
from log import logger
from nav import move

l = logger('catherd.history')

def main(args):
    return None

@result_handler(no_ui=True)
def handle_result(args, answer, target_window_id, boss):
    try:
        move(boss, args[1])
    except:
        l.exception("history blew chunks!")
