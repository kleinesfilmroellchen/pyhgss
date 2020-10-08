import logging
import time
import sys

from enum import Enum

logger = logging.getLogger(__name__)

class ScriptExited(Exception):
    pass

def make_environment():
    return HypertextGenerationEnvironment()

# list of inaccessible methods of HypertextGenerationEnvironment
PRIVATE_METHODS = ['id', 'logger', '_change_setting', 'setting_changer', 'headers']

class HTMLTags(Enum):
    '''Enumerates most of the HTML tags that may be used.'''
    h1 = 'h1'
    h2 = 'h2'
    h3 = 'h3'
    h4 = 'h4'
    h5 = 'h5'
    h6 = 'h6'
    h7 = 'h7'
    h8 = 'h8'
    h9 = 'h9'
    p = 'p'
    a = 'a'
    span = 'span'
    strong = 'strong'
    em = 'em'
    ul = 'ul'
    ol = 'ol'
    li = 'li'
    div = 'div'
    main = 'main'
    header = 'header'
    footer = 'footer'


class HypertextGenerationEnvironment(dict):

    never = -1

    def __init__(self):
        self.id = time.time_ns()
        self.logger = logging.getLogger(__name__ + '.' + str(abs(hash(self)))[:6])
        self.data = bytes()
        self.file_encoding = 'utf-8'
        
        self.headers = dict()
        # TODO do this somewhere else?
        self.headers['Content-Type']  = 'text/html; charset=UTF-8'
        self.__dict__.update(HTMLTags._member_map_)

    # hijack dictionary lookup when this object is used as a globals() -dict
    # redirect the lookup to setattr/getattr for easy method & variable defintion
    def __getitem__(self, name:str):
        if name not in PRIVATE_METHODS:
            return self.__getattribute__(name)
        raise AttributeError('Attribute %s not found' % name)
    def __setitem__(self, name:str, value):
        if name not in PRIVATE_METHODS:
            return self.__setattr__(name, value)
        raise AttributeError('Attribute %s not found' % name)

    def __getattribute__(self, name:str):
        if name != '__getattribute__' and name != '__setattr__':
            logger.log(5, 'Get %s', name)
        
        val = None
        if name == 'settings' or name == 'setting':
            val = self.setting_changer()
        else:
            val = super().__getattribute__(name)
        return val

    def __setattr__(self, name:str, value):
        super().__setattr__(name, value)
        if name != '__getattribute__' and name != '__setattr__':
            logger.log(5, 'Set %s to %s', name, value)

    def __hash__(self):
        hs = 0
        for key, value in super().values():
            hs ^= hash(key + repr(value))
        # lower places are most changing, use those as top places
        return int(str(hs ^ self.id)[::-1])
    
    def write(self, string:str):
        self.logger.debug('Write call with argument %s', string)
        self.data += bytes(string, encoding=self.file_encoding)

    def load(self, filename:str):
        self.logger.debug('Load call with filename %s', filename)
        return ''

    def header(self, key:str, value:str):
        self.logger.debug('Setting header %12s to "%20s".', key, value)
        self.headers[key] = value

    def _change_setting(self, setting_name, value):
        self.logger.debug('Change setting %s to value %s', setting_name, value)
        return value

    def setting_changer(self):
        class SettingChangeHijacker(object):
            def __init__(self, parent):
                self.parent = parent
            def __setattr__(self, name, value):
                if name == 'parent':
                    return super().__setattr__(name, value)
                self.parent._change_setting(name, value)
        return SettingChangeHijacker(self)

    def exit(self):
        self.logger.info('Script exiting.')
        raise ScriptExited()