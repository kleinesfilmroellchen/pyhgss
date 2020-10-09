from http.server import BaseHTTPRequestHandler, SimpleHTTPRequestHandler
from http import HTTPStatus
import urllib
import posixpath
import os.path as pathtools
from os import curdir

import logging
logger = logging.getLogger(__name__)

if __name__ == 'serve' or __name__ == '__main__':
    from __init__ import HypertextGenerator, make_environment
else:
    from . import HypertextGenerator, make_environment


class LoggingBaseHTTPRequestHandler(BaseHTTPRequestHandler):
    '''
    Short extension of the BaseHTTPRequestHandler that redirects logging output
    to the logger provided as the first argument to the constructor.

    Also, exception output is fed through the stackprinter module.
    '''

    def __init__(self, *arg, logger=logging.getLogger(__name__), **kwargs):
        import stackprinter
        self.last_logged_str = ''
        self.logger = logger
        super().__init__(*arg, **kwargs)
        stackprinter.set_excepthook(style="darkbg")

    def send_response_only(self, code, message=None):
        self.log_request(code, message if message is not None else '')
        super().send_response_only(code, message)

    def send_response(self, code, message=None):
        # HACK: prevent send_response from logging by
        # removing the logger methods temporarily
        oldloggers = self.log_message, self.log_error, self.log_warning
        self.log_message = lambda format, *args: None
        self.log_warning = lambda format, *args: None
        self.log_error = lambda format, *args: None
        super().send_response(code, message)
        self.log_message, self.log_error, self.log_warning = oldloggers
        self.log_request(code, message if message is not None else '')

    def log_message(self, string, *args):
        self.logger.info(string % args)

    def log_warning(self, string, *args):
        self.logger.warning(string % args)

    def log_error(self, string, *args):
        if string.startswith('code '):
            # no extra logging of >= 300 requests
            return
        self.logger.error(string % args)

    def log_request(self, code=000, size=''):
        if isinstance(code, HTTPStatus):
            code = code.value
        fmtstring = f'%38s: %s - {self.statustype(code)} (%s)'
        if code >= 300 and code < 400:
            self.log_warning(fmtstring, self.requestline, str(code), str(size))
        elif code >= 400:
            self.log_error(fmtstring, self.requestline, str(code), str(size))
        else:
            self.log_message(fmtstring, self.requestline, str(code), str(size))

    @staticmethod
    def statustype(code):
        return (lambda code: 'Info' if 200 > code >= 100 else
                             'OK' if 300 > code >= 200 else
                             'Redirect' if 400 > code >= 300 else
                             'Client Error' if 500 > code >= 400 else
                             'Server Error' if code >= 500 else '')(code).rjust(12)


class HierarchicalPyghssHTTPRequestHandler(LoggingBaseHTTPRequestHandler, SimpleHTTPRequestHandler):
    '''
    HTTP Request handler (to be used with HTTPServer or any of its subclasses) for serving
    PyHG scripts from a folder and its subfolders starting at the given directory.

    When scripts are not found for a GET request path, the handling is passed on to
    SimpleHTTPRequestHandler's do_GET method for static file serving.

    :param directory: Which directory of the file system to consider the website root.
        Defaults to the currrent working directory.
        (This parameter is handled by SimpleHTTPRequestHandler)

    :param serve_arbitrary_files: Whether to serve arbitrary (non-script) files
        from the file system (True/False). This effectively disables handing
        off to SimpleHTTPRequestHandler's GET method. If this parameter is set
        to 'html', only if SimpleHTTPRequestHandler's send_head() sets a
        `Content-Type: text/html` header, the file will be served. This also
        means that directory listings are served.
    '''

    def __init__(self, *args, scriptdict=None, serve_arbitrary_files=True, **kwargs):
        if scriptdict is None:
            # use a private scriptdict
            scriptdict = {}
        self.scriptdict = scriptdict
        self.toserve = (None if serve_arbitrary_files is False
                        else 'html' if serve_arbitrary_files == 'html'
                        else 'all')
        super().__init__(*args, **kwargs)

    def do_GET(self):
        """
        Normal GET handler.

        This executes PyHG Scripts if they match the filepath (without their ending)

        This method also serves static arbitrary files, if the respective
        constructor parameter was given, or only static HTTP files, if 'http' war given
        """
        # first try sending a script
        url = urllib.parse.urlparse(self.path)

        path = posixpath.normpath(url.path)
        self.logger.debug(path)

        # find the hypertext generating script
        hgs = None
        if path in self.scriptdict:
            # if it already exists, use it
            hgs = self.scriptdict[path]
        else:
            fullpath = pathtools.abspath(self.directory + path)
            for ending in HypertextGenerator.SUPPORTED_ENDINGS + ('',):
                scriptfile = fullpath + ending
                logger.debug('try %s', scriptfile)
                if pathtools.exists(scriptfile) and not pathtools.isdir(scriptfile):
                    hgs = HypertextGenerator(scriptfile)
                    self.scriptdict[path] = hgs

        if hgs is not None:
            # we have ourselves a script
            self.logger.info('Executing PyHG Script %s', path)
            # TODO override options?
            headers, data = hgs.execute()
            self.send_response(200)
            for header, value in headers.items():
                self.send_header(header, value)
            self.end_headers()
            self.wfile.write(data)
            return
        # if that fails, dispatch to simplehttp if required, check mime header if necessary
        if self.toserve is None:
            self.send_error(404)
        elif self.toserve == 'all':
            super().do_GET()
        elif self.toserve == 'html':
            body = super().send_head()
            for binheader in self._headers_buffer:
                logger.debug(binheader)
                name, *value = binheader.decode('latin-1').split(': ')
                value = ': '.join(value)
                logger.debug("%s| : |%s", name, value)
                if name.lower() == 'content-type' and value.lower().startswith('text/html'):
                    # yay send the file
                    logger.debug('File with HTML content found, sending...')
                    self.copyfile(body, self.wfile)
                    break
            else:
                self._headers_buffer = []
                self.send_error(404)


class SinglePyghssHTTPRequestHandler(LoggingBaseHTTPRequestHandler):
    '''
    Handler class that executes a single PyGH script for every request on the
    base path, and sends 404 for all other paths.
    '''

    def __init__(self, *args, filename=None, script=None, **kwargs):
        if filename is None:
            raise ValueError('filename must not be None')
        self.filename = filename
        self.script = script
        super().__init__(*args, **kwargs)

    # all da http
    def do_GET(self):
        self.execute_request('GET')

    def do_HEAD(self):
        self.execute_request('HEAD')

    def do_POST(self):
        self.execute_request('POST')

    def do_PUT(self):
        self.execute_request('PUT')

    def do_DELETE(self):
        self.execute_request('DELETE')

    def do_PATCH(self):
        self.execute_request('PATCH')

    def do_CONNECT(self):
        self.execute_request('CONNECT')

    def do_TRACE(self):
        self.execute_request('TRACE')

    def do_OPTIONS(self):
        self.execute_request('OPTIONS')

    def execute_request(self, methodstr: str):
        self.logger.info('%s request on %s', methodstr, self.filename)
        binary = self.script.execute()
        self.wfile.write(binary)


class MultiplePyhgssHTTPRequestHandler(LoggingBaseHTTPRequestHandler):
    '''
    Handler class that executes several PyGH scripts, one for each
    corresponding path, and sends 404 for all other paths.
    '''

    def __init__(self, *args, files=None, scriptdict={}, **kwargs):
        if files is None:
            raise ValueError('files must not be None')
        self.files = files
        self.scripts = scriptdict
        for file in self.files:
            self.scripts[file] = HypertextGenerator(file)
        super().__init__(*args, **kwargs)

    # all da http
    def do_GET(self):
        self.execute_request('GET')

    def do_HEAD(self):
        self.execute_request('HEAD')

    def do_POST(self):
        self.execute_request('POST')

    def do_PUT(self):
        self.execute_request('PUT')

    def do_DELETE(self):
        self.execute_request('DELETE')

    def do_PATCH(self):
        self.execute_request('PATCH')

    def do_CONNECT(self):
        self.execute_request('CONNECT')

    def do_TRACE(self):
        self.execute_request('TRACE')

    def do_OPTIONS(self):
        self.execute_request('OPTIONS')

    def execute_request(self, methodstr: str):
        logger.info('%s %s request on scripts %s',
                    methodstr, self.path, self.files)
        path = posixpath.normpath(urllib.parse.urlparse(self.path).path)
        binary = self.scripts[path].execute()
        self.wfile.write(binary)
