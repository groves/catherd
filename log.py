from logging import basicConfig, DEBUG, getLogger
from os import makedirs
from os.path import expanduser

log_dir = expanduser("~/.cache/catherd")
makedirs(log_dir, exist_ok=True)

basicConfig(
    filename=f"{log_dir}/log",
    filemode="a",
    format="%(asctime)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
    level=DEBUG,
)


def logger(name):
    return getLogger(name)
