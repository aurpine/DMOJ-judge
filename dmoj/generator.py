import os
import traceback

import sys

from dmoj.error import CompileError
from dmoj.utils import ansi


class GeneratorManager(object):
    def __init__(self):
        self._cache = {}

    def get_generator(self, filename, flags):
        from dmoj.executors import executors
        from dmoj.config import InvalidInitException

        filename = os.path.abspath(filename)
        cache_key = filename, tuple(flags)
        if cache_key in self._cache:
            return self._cache[cache_key]

        try:
            with open(filename) as file:
                source = file.read()
        except:
            traceback.print_exc()
            raise IOError('could not read generator source')

        def find_cpp():
            for grader in ('CPP14', 'CPP11', 'CPP0X', 'CPP'):
                if grader in executors:
                    return grader
            raise InvalidInitException("can't grade with generator; why did I get this submission?")

        lookup = {
            '.py': executors.get('PY2', None),
            '.py3': executors.get('PY3', None),
            '.c': executors.get('C', None),
            '.cpp': executors.get(find_cpp(), None),
            '.java': executors.get('JAVA', None),
            '.rb': executors.get('RUBY', None)
        }
        ext = os.path.splitext(filename)[1]
        pass_platform_flags = ['.c', '.cpp']

        if pass_platform_flags:
            flags += ['-DWINDOWS_JUDGE', '-DWIN32'] if os.name == 'nt' else ['-DLINUX_JUDGE']

        clazz = lookup.get(ext, None)
        if not clazz:
            raise IOError('could not identify generator extension')

        try:
            executor = clazz.Executor('_generator', source)
        except CompileError as err:
            # Strip ansi codes from CompileError message so we don't get wacky displays on the site like
            # 01m[K_generator.cpp:26:23:[m[K [01;31m[Kerror: [m[K'[01m[Kgets[m[K' was not declared in this scope
            raise CompileError(ansi.strip_ansi(err.message))

        if hasattr(executor, 'flags'):
            executor.flags += flags

        self._cache[cache_key] = executor
        return executor
