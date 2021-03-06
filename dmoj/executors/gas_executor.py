import os
import re
import subprocess

from .base_executor import CompiledExecutor
from dmoj.error import CompileError


refeatures = re.compile('^[#;@|!]\s*features:\s*([\w\s,]+)', re.M)
feature_split = re.compile('[\s,]+').split


class GASExecutor(CompiledExecutor):
    as_path = None
    ld_path = None
    qemu_path = None
    dynamic_linker = None
    crt_pre = None
    crt_post = None

    name = 'GAS'
    ext = '.asm'

    def __init__(self, problem_id, source_code, *args, **kwargs):
        self.use_qemu = self.qemu_path is not None and os.path.isfile(self.qemu_path)

        features = refeatures.search(source_code)
        if features is not None:
            self.features = set(filter(None, feature_split(features.group(1))))
        else:
            self.features = set()

        super(GASExecutor, self).__init__(problem_id, source_code + '\n', *args, **kwargs)

    def compile(self):
        object = self._file('%s.o' % self.problem)
        process = subprocess.Popen([self.as_path, '-o', object, self._code],
                                   cwd=self._dir, stderr=subprocess.PIPE)
        as_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(as_output)

        to_link = [object]
        if 'libc' in self.features:
            to_link = ['-dynamic-linker', self.dynamic_linker] + self.crt_pre + ['-lc'] + to_link + self.crt_post

        executable = self._file(self.problem)
        process = subprocess.Popen([self.ld_path, '-s', '-o', executable] + to_link,
                                   cwd=self._dir, stderr=subprocess.PIPE)
        ld_output = process.communicate()[1]
        if process.returncode != 0:
            raise CompileError(ld_output)

        self.warning = ('%s\n%s' % (as_output, ld_output)).strip()
        return executable

    def get_cmdline(self):
        if self.use_qemu:
            return [self.qemu_path, self._executable]
        return super(GASExecutor, self).get_cmdline()

    def get_executable(self):
        if self.use_qemu:
            return self.qemu_path
        return super(GASExecutor, self).get_executable()

    def get_fs(self):
        fs = super(GASExecutor, self).get_fs()
        if self.use_qemu:
            fs += ['/usr/lib', '/proc', self._executable]
        return fs

    def get_allowed_syscalls(self):
        syscalls = super(GASExecutor, self).get_allowed_syscalls()
        if self.use_qemu:
            syscalls += ['madvise']
        return syscalls

    def get_address_grace(self):
        grace = super(GASExecutor, self).get_address_grace()
        if self.use_qemu:
            grace += 65536
        return grace

    @classmethod
    def initialize(cls, sandbox=True):
        if any(i is None for i in (cls.as_path, cls.ld_path, cls.dynamic_linker, cls.crt_pre, cls.crt_post)):
            return False
        if any(not os.path.isfile(i) for i in (cls.as_path, cls.ld_path, cls.dynamic_linker)):
            return False
        if any(not os.path.isfile(i) for i in cls.crt_pre) or any(not os.path.isfile(i) for i in cls.crt_post):
            return False
        return cls.run_self_test(sandbox)
