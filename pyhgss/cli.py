import argparse
import logging

global script_dictionary

logger = logging.getLogger(__name__)

def cli(*args):
    import os, sys
    if __name__ == 'cli' or __name__ == '__main__':
        # use absolute import if this is at the top level of the package structure
        from serve import HierarchicalPyghssHTTPRequestHandler as FolderHandler, SinglePyghssHTTPRequestHandler as SingleHandler, MultiplePyhgssHTTPRequestHandler as MultiHandler
        from __init__ import HypertextGenerator
    else:
        from .serve import HierarchicalPyghssHTTPRequestHandler as FolderHandler, SinglePyghssHTTPRequestHandler as SingleHandler, MultiplePyhgssHTTPRequestHandler as MultiHandler
        from . import HypertextGenerator
    from http.server import ThreadingHTTPServer
    from functools import partial
    parser = argparse.ArgumentParser('pyhgss',
        description='Python Hypertext Generation Scripting System command line utility',
        epilog='Copyright 2019, kleinesfilmroellchen')

    parser.add_argument('file', action='store', metavar='FILES', nargs='+',
        help='The pyhg script to serve. If a folder is given, serve all files\
            in the folder using their respective name.\
            In this case, the following behavior is applied:\
            For any incoming request on any path, traverse that path inside\
            the folder and examine the respective file. If it is a folder,\
            look for the files "index.pyh", "index.pyhgs", "index.py",\
            "index.html", "index.htm", "index" (in this particular order).\
            If no such file was found, generate a folder view website (unless\
            the option --no-dirs is specified). If it is a pyhg script, i.e. the\
            last part of the url plus the ending ".pyh", "pyhgs" or ".py" (in\
            this particular order) matches the file\'s name, the specified\
            script is executed and its output transmitted to the client.\
            Finally, if it is of any other type, serve that file with guessed\
            MIME type. Such arbitrary file serving can be controlled and\
            restricted with the --no-arbitrary-files and --serve-html options.\
            Multiple files (but not folders!) can be given to serve each file\
            under its respective name.'
            )
    parser.add_argument('--no-arbitrary-files', '-n', dest='arbitraryFiles',
        action='store_false', default=True,
        help='Prevent arbitrary files from being served. When this option is given,\
            no file that has an ending other than ".pyh", "pyhgs" or ".py" will\
            ever be served to the client. To re-enable serving HTML files, use\
            the --serve-html option.')
    parser.add_argument('--serve-html', '-t', dest='allowHTML',
        action='store_true', default=False,
        help='Re-enable serving HTML files if the option --no-arbitrary-files\
            is used and would usually prevent HTML files from being served.\
            This option has no effect without --no-arbitrary-files, as HTML\
            files are always served by default.')
    parser.add_argument('-d', '--host', dest='host',
        action='store', default='127.0.0.1',
        help='On which host to listen. Defaults to localhost,\
            use 0.0.0.0 to listen on all public inbound addresses (for e.g. docker)')
    parser.add_argument('-p', '--port', dest='port',
        action='store', type=int, default=80,
        help='Which port to bind to. Defaults to 80 (http standard).\
            This can cause problems if other applications are listening on the same port.')

    arguments = parser.parse_args(args)

    logger.debug(arguments)

    try:
        handler_class = None
        if len(arguments.file) == 1:
            arguments.file = arguments.file[0]
            if not os.path.exists(arguments.file):
                raise argparse.ArgumentTypeError(
                    f'file or directory {arguments.file} does not exist')
            if os.path.isdir(arguments.file):
                # it is a folder, serve the folder
                serve_restriction = arguments.arbitraryFiles
                if serve_restriction is False:
                    serve_restriction = 'html' if arguments.allowHTML else False
                script_dictionary = dict()
                handler_class = partial(FolderHandler, directory=arguments.file,
                    serve_arbitrary_files=serve_restriction,
                    scriptdict=script_dictionary)
            else:
                handler_class = partial(SingleHandler, filename=arguments.file, script=HypertextGenerator(arguments.file))
        else:
            for fname in arguments.file:
                if not os.path.exists(fname):
                    raise argparse.ArgumentTypeError(
                        f'file {fname} does not exist')
                if os.path.isdir(fname):
                    raise argparse.ArgumentTypeError(
                        f'multiple files given, but {fname} is a directory')
            script_dictionary = dict()
            handler_class = partial(MultiHandler, files=arguments.file, scriptdict=script_dictionary)

        logger.debug(handler_class)

        #nest da partial
        logr = logging.getLogger(__package__ + '.server' if len(__package__) > 0 else 'server')
        handler_class = partial(handler_class, logger=logr)

        srver = ThreadingHTTPServer((arguments.host, arguments.port), handler_class)

        print(f'PyHGSS Server active on {arguments.host}:{arguments.port} ...')
        try:
            srver.serve_forever()
        except KeyboardInterrupt:
            print(f'Closing server.')

    except argparse.ArgumentTypeError as e:
        parser.print_usage()
        print(parser.prog + ': error:', e)
        sys.exit(-1)
