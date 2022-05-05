from json import dumps
from base64 import b85encode
from sys import argv, stdout
result = {
    'returncode':int(argv[1]),
    'stdout': argv[2] if len(argv) > 2 else ''
}
# Lifted from https://github.com/kovidgoyal/kitty/blob/4ca70bfa266fc1045b50fcf2f77a4934e4688b93/kittens/runner.py#L98
data = b85encode(dumps(result).encode('utf-8'))
stdout.buffer.write(b'\x1bP@kitty-kitten-result|')
stdout.buffer.write(data)
stdout.buffer.write(b'\x1b\\')
stdout.flush()