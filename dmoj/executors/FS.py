import os

from dmoj.executors.clr_executor import CLRExecutor
from dmoj.executors.utils import test_executor
from dmoj.judgeenv import env


class Executor(CLRExecutor):
    extension = 'fs'
    compiler = 'fsc'
    compile_args = ['--nologo', '--out:{exe}', '{source}']


def initialize(sandbox=True):
    # TODO: sandbox is ignored
    if 'fsc' not in env['runtime']:
        return False
    if not os.path.isfile(env['runtime']['fsc']):
        return False
    return test_executor('FS', Executor, 'printfn "Hello, World!"')
