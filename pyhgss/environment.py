import logging
import time
import sys
import bs4

from functools import singledispatchmethod
from enum import Enum

logger = logging.getLogger(__name__)


class ScriptExited(Exception):
    '''Exception type without any extra features. Signals a user-invoked exit of the PyHG script.'''
    pass


def make_environment():
    '''Returns a new :py:class:`HypertextGenerationEnvironment`. This method is intended for more complicated environment setup in the future.'''
    hge = HypertextGenerationEnvironment()
    hge.headers['Content-Type'] = 'text/html; charset=UTF-8'
    hge.__dict__.update(Type._member_map_)
    return hge


# list of inaccessible methods of HypertextGenerationEnvironment
PRIVATE_METHODS = ['id', 'logger',
                   '_change_setting', 'setting_changer', 'headers']


class Type(Enum):
    '''Enumerates the external file types that PyHGSs can auto-detect and that the user can specify manually.'''
    HTML = 'html'
    JavaScript = 'js'
    CSS = 'css'


class HypertextGenerationEnvironment(dict):
    '''
    This object acts as the global environment for PyHGSs scripts. This is possible because it extends the :py:class:`dict` class and overrides the ``__getitem__`` and ``__setitem__`` that Python will invoke when resolving or binding a global variable, respectively. These are redirected to the normal ``__getattr__`` and ``__setattr__``, which handle the usual resolving of object fields.

    This class is responsible for handling the script's input and output. Its 
    '''

    never = -1
    '''Constant for caching, uses the special value of -1.'''

    class JSCode:
        '''
        An object representing JavaScript code. This is mostly a convenience object for quickly and correctly passing around JavaScript code that the user creates and loads from files. This object does not parse JavaScript and cannot execute it (internally).
        '''

        def __init__(self, code: str):
            ''':param code: The string code to store in this JSCode object.'''
            self.code = code

        def __str__(self):
            '''The string conversion wraps the code in a simple script tag.'''
            return '<script>' + self.code + '</script>'

    def __init__(self):
        '''
        The constructor of the environment does not take any arguments.
        '''
        self.id = time.time_ns()
        self.logger = logging.getLogger(
            __name__ + '.' + str(abs(hash(self)))[:6])
        self.data = bytes()
        self.file_encoding = 'utf-8'
        self.headers = dict()
        # global namespaces

    # hijack dictionary lookup when this object is used as a globals() -dict
    # redirect the lookup to setattr/getattr for easy method & variable defintion
    def __getitem__(self, name: str):
        '''
        Overrides :py:meth:`dict.__getitem__`.

        Is used here to intercept all global lookups and redirect them to the normal :py:meth:`HypertextGenerationEnvironment.__getattribute__`.'''

        if name not in PRIVATE_METHODS:
            return self.__getattribute__(name)
        raise AttributeError('Attribute %s not found' % name)

    def __setitem__(self, name: str, value):
        '''
        Overrides :py:meth:`dict.__setitem__`.

        Is used here to intercept all global assignments and redirect them to the normal :py:meth:`HypertextGenerationEnvironment.__setattr__`.'''

        if name not in PRIVATE_METHODS:
            return self.__setattr__(name, value)
        raise AttributeError('Attribute %s not found' % name)

    def __getattribute__(self, name: str):
        '''
        Handles global lookups of the PyHGSs script.

        This method is overwritten as to prevent certain lookups (e.g. __getattribute__ itself) and to redirect some other lookups, most importantly the pseudo-object ``settings``.
        '''
        if name != '__getattribute__' and name != '__setattr__':
            logger.log(5, 'Get %s', name)

        val = None
        if name == 'settings' or name == 'setting':
            val = self.setting_changer()
        else:
            val = super().__getattribute__(name)
        return val

    def __setattr__(self, name: str, value):
        '''
        Handles global assignments of the PyHGSs script.

        This method is overwritten as to prevent certain assignments (e.g. __setattr__ itself).
        '''
        super().__setattr__(name, value)
        if name != '__getattribute__' and name != '__setattr__':
            logger.log(5, 'Set %s to %s', name, value)

    def __hash__(self):
        hs = 0
        for key, value in super().values():
            hs ^= hash(key + repr(value))
        # lower places are most changing, use those as top places
        return int(str(hs ^ self.id)[::-1])

    @singledispatchmethod
    def write(self, data, tag: str = None):
        '''
        Write data to the page. This is the most important output function.

        There are multiple overrides to the ``write`` method, chosen by :py:func:`functools.singledispatchmethod`.

        :param tag: The HTML tag in which to enclose the data, optional.
        :param data: The following different actions are chosen with different argument types. Other arguments are :py:func:`str`-ified and passed to the write(str) method.
        * :py:class:`str`: Writes a verbatim string to the page. Note that no HTML escaping takes place, so this method can write any HTML it wants. Its encoding is the same as the script's encoding. The encoding for input strings can be changed with ``settings.encoding``.
        * :py:class:`bs4.BeautifulSoup`: Writes the prettified version of the BeautifulSoup parsed HTML to the page. If a tag is used, the tag enclosing happens at the abstract level to keep the HTML syntax valid.
        * :py:class:`pyhgss.environment.HypertextGenerationEnvironment.JSCode`: Writes the JavaScript enclosed in <script> tags to the page.
        '''
        # default method stringifies argument
        self.write(str(data), tag)

    @write.register
    def _write(self, string: str, tag: str = None):
        self.logger.debug('Write string %s', string)
        self.data += bytes(string, encoding=self.file_encoding)

    @write.register
    def _write(self, html: bs4.BeautifulSoup, tag: str = None):
        self.logger.debug('Write HTML %s', html)
        if tag is not None:
            html = html.wrap(html.new_tag(tag))
        self.data += bytes(html.prettify(), encoding=self.file_encoding)

    def load(self, filename: str, type: Type = None):
        '''
        Load data from a file.

        This method serves the purpose of easily loading external data and using it with the page generation. By default, this method auto-detects the file type based on its ending and loads a respective data representation. The file encoding is always guessed using chardet.

        When the following type is detected or specified, the following action is taken on the file:

        * **HTML:** The file's text content is given to BeautifulSoup4's 'html.parser' parser, and the result is returned to the user. This gives the user a perfectly normal BS4 parsed HTML tree which can then be manipulated. All of the I/O functions of the PyHGS system can deal with BS4 objects.
        * **JavaScript:** Returns a wrapper :py:class:`HypertextGenerationEnvironment.JSCode`. This simply contains the JavaScript of the file. See the documentation of the class to find out more about working with JSCode objects.
        * **CSS:**

        Otherwise, the plain text of the file is returned as a string.

        :param filename: Specify the filename, always in relation to the script's file location.
        :param type: Specify the file type, in the form ``Type.*``, where * is one of the supported file type identifiers. This overrides the file type auto-detection.
        '''
        self.logger.debug('Load call with filename %s', filename)
        return ''

    def header(self, key: str, value: str):
        '''
        Set an HTTP header. Any existing header with this name is overwritten.

        :param key: The header's name.
        :param value: The value of the header.
        '''
        self.logger.debug('Setting header %12s to "%20s".', key, value)
        self.headers[key] = value

    def _change_setting(self, setting_name: str, value):
        '''
        Handles the actual settings change itself.

        :param setting_name: The setting that was attempted to change.
        :param value: The value that was assigned to the setting.
        '''
        self.logger.debug('Change setting %s to value %s', setting_name, value)
        # switch case
        if setting_name == 'encoding':
            self.file_encoding = value
        return value

    def setting_changer(self):
        '''Generate a proxy object that will hijack and redirect all changes made to the pseudo-object ``settings``.'''
        class SettingChangeHijacker(object):
            def __init__(self, parent):
                self.parent = parent

            def __setattr__(self, name, value):
                if name == 'parent':
                    return super().__setattr__(name, value)
                self.parent._change_setting(name, value)
        return SettingChangeHijacker(self)

    def javascript(self, data):
        '''
        Wrapper method for creating a new :py:class:`HypertextGenerationEnvironment.JSCode` object.
        '''
        return JSCode(data)

    def exit(self):
        '''Stops the PyHG script execution by throwing :py:class:`ScriptExited`'''
        self.logger.info('Script exiting.')
        raise ScriptExited()
