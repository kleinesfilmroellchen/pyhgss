# Python Hypertext Generation Scripting System (PyHGSs)

A simple server system that serves Python CGI scripts, Python code with a special environment that allows it to generate HTML and do other server-side processing.

There is a documentation system prepared (make powered by sphinx, e.g. make html), but no documentation is yet written. The code itself is reasonably-well documented, so look into it if you're interested.

Run this program on the command line with `python phgss`. There are several options and the cli documents itself very well:

```
usage: pyhgss [-h] [--no-arbitrary-files] [--serve-html] [-d HOST] [-p PORT] FILES [FILES ...]

Python Hypertext Generation Scripting System command line utility

positional arguments:
  FILES                 The pyhg script to serve. If a folder is given, serve all files in the folder using their respective name. In this case, the following behavior is applied: For any incoming request on any path, traverse that path inside the folder and examine the respective file. If it is a folder, look for the files "index.pyh", "index.pyhgs", "index.py", "index.html", "index.htm", "index" (in this particular order). If no such file was found, generate a folder view website (unless the option --no-dirs is specified). If it is a pyhg script, i.e. the last part of the url plus the ending ".pyh", "pyhgs" or ".py" (in this particular order) matches the file's name, the specified script is executed and its output transmitted to the client. Finally, if it is of any other type, serve that file with guessed MIME type. Such arbitrary file serving can be controlled and restricted with the --no-arbitrary-files and --serve-html options. Multiple files (but not folders!) can be given to serve each file under its respective name.

optional arguments:
  -h, --help            show this help message and exit
  --no-arbitrary-files, -n
                        Prevent arbitrary files from being served. When this option is given, no file that has an ending other than ".pyh", "pyhgs" or ".py" will ever be served to the client. To re-enable serving HTML files, use the --serve-html option.
  --serve-html, -t      Re-enable serving HTML files if the option --no-arbitrary-files is used and would usually prevent HTML files from being served. This option has no effect without --no-arbitrary-files, as HTML files are always served by default.
  -d HOST, --host HOST  On which host to listen. Defaults to localhost, use 0.0.0.0 to listen on all public inbound addresses (for e.g. docker)
  -p PORT, --port PORT  Which port to bind to. Defaults to 80 (http standard). This can cause problems if other applications are listening on the same port.

Copyright 2019, kleinesfilmroellchen
```
