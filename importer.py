from importlib import import_module, reload
from sys import modules

# This is dumb, but it's as convenient a simple way I've come up with to reload the library modules that live on in Kitty's Python on each invocation of the kitten that uses them.
def reload_catherd_modules():
    for module_name in ['log', 'nav']:
        if module_name in modules: 
            reload(modules[module_name])
