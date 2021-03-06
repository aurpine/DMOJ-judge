import os

try:
    from dmoj.cptbox import CHROOTSecurity, SecurePopen, PIPE
except ImportError:
    CHROOTSecurity, SecurePopen, PIPE = None, None, None
    from dmoj.wbox import WBoxPopen

from .base_executor import CompiledExecutor
from dmoj.judgeenv import env
import subprocess

C_FS = ['.*\.so', '/proc/meminfo', '/dev/null']
GCC_ENV = env['runtime'].get('gcc_env', {})
GCC_COMPILE = os.environ.copy()
IS_ARM = hasattr(os, 'uname') and os.uname()[4].startswith('arm')

if os.name == 'nt':
    GCC_COMPILE.update((k.encode('mbcs'), v.encode('mbcs')) for k, v in
                       env['runtime'].get('gcc_compile', GCC_ENV).iteritems())
    GCC_ENV = dict((k.encode('mbcs'), v.encode('mbcs')) for k, v in GCC_ENV.iteritems())
else:
    GCC_COMPILE.update(env['runtime'].get('gcc_compile', {}))


class GCCExecutor(CompiledExecutor):
    defines = []
    flags = []
    name = 'GCC'

    def create_files(self, problem_id, main_source, aux_sources=None, fds=None, writable=(1, 2)):
        if not aux_sources:
            aux_sources = {}
        aux_sources[problem_id + self.ext] = main_source
        sources = []
        for name, source in aux_sources.iteritems():
            if '.' not in name:
                name += self.ext
            with open(self._file(name), 'wb') as fo:
                fo.write(source)
            sources.append(name)
        self.sources = sources
        self._fds = fds
        self._writable = writable

    def get_ldflags(self):
        if os.name == 'nt':
            return ['-Wl,--stack,67108864']
        return []

    def get_flags(self):
        return self.flags

    def get_defines(self):
        defines = ['-DONLINE_JUDGE'] + self.defines
        if os.name == 'nt':
            defines.append('-DWIN32')
        return defines

    def get_compile_args(self):
        return ([self.command, '-Wall'] + (['-fdiagnostics-color=always'] if self.has_color else []) + self.sources
                + self.get_defines() + ['-O2', '-lm'] + ([] if IS_ARM else ['-march=native'])
                + self.get_flags() + self.get_ldflags() + ['-s', '-o', self.get_compiled_file()])

    def get_compile_env(self):
        return GCC_COMPILE

    def get_fs(self):
        return ['.*\.so', '/proc/meminfo', '/dev/null']

    def get_security(self):
        return CHROOTSecurity(self.get_fs(), writable=self._writable)

    def get_env(self):
        return GCC_ENV

    @classmethod
    def initialize(cls, sandbox=True):
        try:
            version = float(subprocess.Popen([cls.command, '-dumpversion'],
                                             stdout=subprocess.PIPE,
                                             stderr=subprocess.PIPE).communicate()[0][:3])
            cls.has_color = version >= 4.9
        except:
            cls.has_color = False
        return super(CompiledExecutor, cls).initialize(sandbox=sandbox)
