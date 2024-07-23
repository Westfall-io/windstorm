import os
import sys
import uuid
import logging
import shutil

logger = logging.getLogger("windstorm.common.functions")


def github_issue_error():
    logger.error("Unknown error. Please submit a issue on github.")
    raise NotImplementedError


def setup_logging(debug):
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)

    loggers = [logging.getLogger(name) for name in logging.root.manager.loggerDict]

    for logger in loggers:
        if not logger.handlers:
            if debug:
                logger.setLevel(logging.DEBUG)
            else:
                logger.setLevel(logging.INFO)

            logger.addHandler(handler)
            logger.propagate = False


def is_valid_uuid(val):
    if val == "":
        return val
    else:
        try:
            uuid.UUID(str(val))
            return val
        except ValueError:
            logger.error("The project id was not passed as a valid uuid.")
            sys.exit()


def remove_file(filename):
    try:
        os.remove(filename)
    except OSError:
        pass
    except PermissionError:
        logger.error("Could not remove files appropriately, shutting down.")
        sys.exit()


def rename_file(f1, f2):
    try:
        os.rename(f1, f2)
    except OSError:
        pass
    except PermissionError:
        logger.error("Could not rename files appropriately, shutting down.")
        sys.exit()


def zip_file(filename):
    try:
        shutil.make_archive(filename, "zip", "./tmpzip")
    except PermissionError:
        logger.error("Could not make an archive.")
        sys.exit()

    try:
        # Remove the extra temporary folder
        shutil.rmtree("./tmpzip")
    except PermissionError:
        logger.warning("Could not remove temporary folder.")
        return
