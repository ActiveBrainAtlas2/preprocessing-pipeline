import os
import subprocess
from pathlib import Path
import logging
from datetime import datetime
from abakit.lib.sql_setup import session
from abakit.model.log import Log


class FileLogger:
    def __init__(self, LOGFILE_PATH):
        """
        -CHECK FOR PRESENCE OF LOG FILE (RW PERMISSION)
        -SET CONFIG FOR LOGGING
        """

        try:
            with open(LOGFILE_PATH, "a") as f:
                pass
        except FileNotFoundError:
            print("CREATED LOGFILE @ ", LOGFILE_PATH)
            Path(LOGFILE_PATH).touch()

        logging.basicConfig(
            filename=LOGFILE_PATH, level=logging.INFO, format="%(message)s", force=True
        )

    def logevent(self, msg: str):
        timestamp = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"{timestamp} - {msg}")
        return timestamp


##PREVIOUS VERSION BELOW (LOG TO DB)
class DatabaseHandler(logging.Handler):
    def emit(self, record):
        log = Log(
            prep_id=record.name,
            level=record.levelname,
            logger=record.module,
            msg=record.msg,
        )
        session.add(log)
        session.commit()


def get_logger(prep_id, level=logging.INFO):
    handler = DatabaseHandler()

    logger = logging.getLogger(prep_id)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
