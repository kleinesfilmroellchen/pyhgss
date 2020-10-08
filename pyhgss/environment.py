import logging
import time
import sys

logger = logging.getLogger(__name__)

class ScriptExited(Exception):
    pass

def make_environment():
    return HypertextGenerationEnvironment()

# list of inaccessible methods of HypertextGenerationEnvironment
PRIVATE_METHODS = ['_change_setting', 'setting_changer']

class HypertextGenerationEnvironment(dict):

    never = -1

    def __init__(self):
        self.id = time.time_ns()
        self.logger = logging.getLogger(__name__ + '.' + str(abs(hash(self)))[:6])
        self.data = bytes()

    # hijack dictionary lookup when this object is used as a globals() -dict
    # redirect the lookup to setattr/getattr for easy method & variable defintion
    def __getitem__(self, name):
        if name not in PRIVATE_METHODS:
            return self.__getattribute__(name)
        raise AttributeError('Attribute %s not found' % name)
    def __setitem__(self, name, value):
        if name not in PRIVATE_METHODS:
            return self.__setattr__(name, value)
        raise AttributeError('Attribute %s not found' % name)

    def __getattribute__(self, name):
        if name != '__getattribute__' and name != '__setattr__':
            logger.log(5, 'Get %s', name)
        
        val = None
        if name == 'settings' or name == 'setting':
            val = self.setting_changer()
        else:
            val = super().__getattribute__(name)
        return val

    def __setattr__(self, name, value):
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
        self.data += bytes(string, encoding='utf-8')

    def load(self, filename:str):
        self.logger.debug('Load call with filename %s', filename)
        return ''

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