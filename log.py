from logging import basicConfig, DEBUG, getLogger
from os import makedirs
from os.path import expanduser

cache_dir = expanduser("~/.cache/catherd")
makedirs(cache_dir, exist_ok=True)

basicConfig(
    filename=f"{cache_dir}/log",
    filemode="a",
    format="%(asctime)s %(name)s %(message)s",
    datefmt="%H:%M:%S",
    level=DEBUG,
)


def logger(name):
    return getLogger(name)
