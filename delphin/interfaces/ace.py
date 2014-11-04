
u"""ACE interface"""

from __future__ import with_statement
import logging
from subprocess import (check_call, CalledProcessError, Popen, PIPE, STDOUT)

class AceProcess(object):

    _cmdargs = []

    def __init__(self, grm, cmdargs=None, executable=None, **kwargs):
        self.grm = grm
        self.cmdargs = cmdargs or []
        self.executable = executable or u'ace'
        self._open()

    def _open(self):
        self._p = Popen(
            [self.executable, u'-g', self.grm] + self._cmdargs + self.cmdargs,
            stdin=PIPE,
            stdout=PIPE,
            stderr=STDOUT,
            universal_newlines=True
        )

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()
        return False  # don't try to handle any exceptions

    def send(self, datum):
        self._p.stdin.write(datum.rstrip() + u'\n')
        self._p.stdin.flush()

    def receive(self):
        return self._p.stdout

    def interact(self, datum):
        self.send(datum)
        result = self.receive()
        return result

    def read_result(self, result):
        return result

    def close(self):
        self._p.stdin.close()
        for line in self._p.stdout:
            logging.debug(u'ACE cleanup: {}'.format(line.rstrip()))
        retval = self._p.wait()
        return retval


class AceParser(AceProcess):

    def receive(self):
        response = {
            u'NOTES': [],
            u'WARNINGS': [],
            u'ERRORS': [],
            u'SENT': None,
            u'RESULTS': []
        }

        blank = 0

        stdout = self._p.stdout
        line = stdout.readline().rstrip()
        while True:
            if line.strip() == u'':
                blank += 1
                if blank >= 2:
                    break
            elif line.startswith(u'SENT: ') or line.startswith(u'SKIP: '):
                response[u'SENT'] = line.split(u': ', 1)[1]
            elif (line.startswith(u'NOTE:') or
                  line.startswith(u'WARNING') or
                  line.startswith(u'ERROR')):
                level, message = line.split(u': ', 1)
                response[u'{}S'.format(level)].append(message)
            else:
                mrs, deriv = line.split(u' ; ')
                response[u'RESULTS'].append({
                    u'MRS': mrs.strip(),
                    u'DERIV': deriv.strip()
                })
            line = stdout.readline().rstrip()
        return response


class AceGenerator(AceProcess):

    _cmdargs = [u'-e']

    def receive(self):
        response = {
            u'NOTE': None,
            u'WARNING': None,
            u'ERROR': None,
            u'SENT': None,
            u'RESULTS': None
        }
        results = []

        stdout = self._p.stdout
        line = stdout.readline().rstrip()
        while not line.startswith(u'NOTE: '):
            if line.startswith(u'WARNING') or line.startswith(u'ERROR'):
                level, message = line.split(u': ', 1)
                response[level] = message
            else:
                results.append(line)
            line = stdout.readline().rstrip()
        # sometimes error messages aren't prefixed with ERROR
        if line.endswith(u'[0 results]') and len(results) > 0:
            response[u'ERROR'] = u'\n'.join(results)
            results = []
        response[u'RESULTS'] = results
        return response


def compile(cfg_path, out_path, log=None):
    #debug('Compiling grammar at {}'.format(abspath(cfg_path)), log)
    try:
        check_call(
            [u'ace', u'-g', cfg_path, u'-G', out_path],
            stdout=log, stderr=log, close_fds=True
        )
    except (CalledProcessError, OSError):
        logging.error(
            u'Failed to compile grammar with ACE. See {}'
            .format(abspath(log.name) if log is not None else u'<stderr>')
        )
        raise
    #debug('Compiled grammar written to {}'.format(abspath(out_path)), log)


def parse_from_iterable(dat_file, data, **kwargs):
    with AceParser(dat_file, **kwargs) as parser:
        for datum in data:
            yield parser.interact(datum)


def parse(dat_file, datum, **kwargs):
    return parse_from_iterable(dat_file, [datum], **kwargs).next()


def generate_from_iterable(dat_file, data, **kwargs):
    with AceGenerator(dat_file, **kwargs) as generator:
        for datum in data:
            yield generator.interact(datum)


def generate(dat_file, datum, **kwargs):
    return generate_from_iterable(dat_file, [datum], **kwargs).next()


# def do(cmd):
#     # validate cmd here (e.g. that it has a 'grammar' key, correct 'task', etc)
#     task = cmd['task']
#     grammar = cmd['grammar']
#     cmdargs = cmd['arguments'] + ['-g', grammar]
#     if task == 'parse':
#         process_output = parse_results
#     elif task == 'transfer':
#         process_output = transfer_results
#     elif task == 'generate':
#         process_output = generation_results
#     else:
#         logging.error('Task "{}" is unsupported by the ACE interface.'
#                       .format(task))
#         return
#     cmdargs = map(lambda a: a.format(**cmd['variables']), cmdargs)
#     _do()
