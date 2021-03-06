from dmoj.executors.C import Executor as CExecutor
from dmoj.judgeenv import env


class Executor(CExecutor):
    command = env['runtime'].get('clang')
    name = 'CLANG'

initialize = Executor.initialize
