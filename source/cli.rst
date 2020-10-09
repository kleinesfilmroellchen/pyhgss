.. contents::

Using the Command-line interface of the PyHGS System
====================================================

PyHGSs comes with a command-line interface that acts as the default PyHGSs server. It is a slight extension of :py:class:`http.server.SimpleHTTPRequestHandler` which runs ``.pyh``, ``pyhgs``, and ``.py`` files with the PyHGSs system to produce sensible output.

Run the CLI by simply running the package itself: ``python -m pyhgss`` (or if it isn't installed: ``python pyhgss`` in the folder that contains the package source). Always refer to the help output provided by ``-h`` and ``--help`` if this documentation is unhelpful.

The FILES arguments
-------------------

The main argument to the CLI are the list of files or folders given after the options. Usually specifies the pyhg script to serve. If a folder is given, it serves all files in the folder using their respective name. In this case, the following behavior is applied: For any incoming request on any path, traverse that path inside the folder and examine the respective file. If it is a folder, look for the files ``index.pyh``, ``index.pyhgs``, ``index.py``, ``index.html``, ``index.htm``, ``index`` (in this particular order). If no such file was found, generate a folder view website (this can be disabled with the option ``--no-dirs``, see :ref:`No directory option <no-dirs-opt>`). If it is a pyhg script, i.e. the last part of the url plus the ending ``.pyh``, ``pyhgs`` or ``.py`` (in this particular order) matches the file's name, the specified script is executed and its output transmitted to the client. Finally, if it is of any other type, serve that file with guessed MIME type. Such arbitrary file serving can be controlled and restricted with the ``--no-arbitrary-files`` and ``--serve-html`` options. Multiple files (but not folders!) can be given to serve each file under its respective name.

.. warning:: The PyHGSs makes no guarantees as to the security of the files that are contained in the folders which you provide it. Any files contained in such folders may be served to the client.

Options
-------

The command-line-interface provides many options and switches:

.. _no-dirs-opt:
* ``--no-dirs`` (not implemented): Do not serve directory listings. This is a default behavior of :py:class:`http.server.SimpleHTTPRequestHandler` which can be disabled by this switch. If present, it does not serve directory listings if no index file was found. This increases the server security by preventing user insight into folder structures.
* ``--help, -h``: Print the help output and exit.
* ``--no-arbitrary-files, -n``: Prevent arbitrary files from being served. When this option is given, no file that has an ending other than ``.pyh``, ``pyhgs`` or ``.py`` will ever be served to the client. To re-enable serving HTML files, use the ``--serve-html`` option. This option is useful because it increases the server's safety by constraining the files to be served.
* ``--serve-html, -t`` Re-enable serving HTML files if the option ``--no-arbitrary-files`` is used and would usually prevent HTML files from being served. This option has no effect without ``--no-arbitrary-files``, as HTML files are always served by default.
* ``--host, -d``: Specify the host on which the server will listen. Defaults to localhost. The most common use case for this may be if you are running this CLI inside a Docker container, in which case you will need to set the host to 0.0.0.0 to listen on all public inbound addresses.
* ``--port, -p``: Specify which port to bind to. Defaults to 80 (http standard). This is particularly important if you are running this on a dev machine with other stuff running on port 80.


Examples
--------

* Serve a single PyHG Script: ``python pyhgss your-script.pyh``. It will be accessible on localhost:80.
* Serve an entire folder on a dev port: ``python pyhgss ./public -p 8081``
* Serve some files to the public, e.g. from a Docker container: ``python pyhgss script1.pyh script2.pyh script3.pyh -d 0.0.0.0 -p 9000``
* Serve only PyHGS and HTML from a folder: ``python pyhgss ./public -nt -p 5000``