#!usr/bin/env python3
import logging
import sys
from hashlib import sha1
from typing import Tuple, Dict


logger = logging.getLogger(__name__)

logger.debug(__name__)

if __name__ == "__init__":
    from cli import cli
    from environment import ScriptExited as _ScriptExited
    from environment import make_environment
    from util import guess_encoding
else:
    from .cli import cli
    from .environment import ScriptExited as _ScriptExited
    from .environment import make_environment
    from .util import guess_encoding

__version__ = '0.1a1'


class HypertextGenerator(object):
    '''
    Hypertext generator base implementation.

    This class keeps track of a hypertext generating file and executes that
    file in a special environment to generate hypertext or other file data and
    transfer that data to the server.
    '''

    '''Supported/recommended ending types for hypertext generating python scripts.
    It is strongly recommended not to use any other endings for the hypertext generating scripts.
    Also, the first given ending is the preferred one.'''
    SUPPORTED_ENDINGS = ('.pyh', '.pyhgs', '.py')

    # max number of file bytes to read at once
    BUFFER_SIZE = 300

    def __init__(self, filename: str):
        if not filename.endswith(self.SUPPORTED_ENDINGS):
            logger.warning(
                'File %(filename)s does not end with any of the supported endings (%(endings)s). It is strongly recommended to use the \'%(preferredending)s\' ending.',
                {'filename': filename,
                 'endings': ', '.join(self.SUPPORTED_ENDINGS),
                 'preferredending': self.SUPPORTED_ENDINGS[0]
                 })
        self.filename = filename
        self.fileencoding = guess_encoding(filename)
        self._filehash = None
        self._code = None
        self.logger = logging.getLogger(__name__ + '.HypertextGenerator')
        self.logger.debug('Guessed encoding %s for file %s',
                          self.fileencoding, self.filename)

    def execute(self, override_opts=None) -> Tuple[Dict[str, str], bytes]:
        if override_opts is None:
            override_opts = {}
        # TODO handle overriding execution options

        contents = str()
        with open(self.filename, 'r', encoding=self.fileencoding) as scriptfile:
            newpart = scriptfile.read(self.BUFFER_SIZE)
            while newpart:
                contents += newpart
                newpart = scriptfile.read(self.BUFFER_SIZE)
        # re-encode file into utf-8 bytes
        bytecontents = bytes(contents, encoding='utf-8')

        filecode = None
        if self._code is not None:
            # hash file and compare it to old hash
            digest = sha1(bytecontents).digest()
            if digest == self._filehash:
                self.logger.info(
                    'Using old compilation with hash %s', self._filehash)
                # we don't need to recompile the file
                filecode = self._code
        # no code generated yet
        if filecode is None:
            self._filehash = sha1(bytecontents).digest()
            filecode = compile(
                contents, filename=self.filename, mode='exec', optimize=2)
            self.logger.debug('Recompiled file %s (hash %s) to code object %s',
                              self.filename, self._filehash, filecode)
            self._code = filecode

        environment_object = make_environment()
        # inform environment of file encoding
        environment_object.file_encoding = self.fileencoding
        environment_object.script_name = self.filename
        try:
            exec(filecode, environment_object)
        except _ScriptExited:
            pass

        return (environment_object.headers, environment_object.data)


logger.info('pyhgss initialized, version %s.', __version__)

if __name__ == "__main__":
    logging.basicConfig(
        format='%(levelname)s [%(name)s]: %(message)s', level=logging.DEBUG)
    logger.setLevel(logging.DEBUG)
    logging.getLogger('environment').setLevel(5)
    # sg = HypertextGenerator('examplegenerator.pyh')
    # bts = sg.execute()
    # logger.debug(bts)
    cli(*sys.argv[1:])
