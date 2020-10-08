import logging
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    logging.basicConfig(format='%(levelname)s [%(name)s]: %(message)s', level=logging.DEBUG)
    import sys
    from cli import cli
    logger.debug(__name__)
    cli(*sys.argv[1:])