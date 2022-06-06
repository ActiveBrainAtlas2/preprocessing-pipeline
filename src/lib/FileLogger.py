import os
import subprocess
from pathlib import Path
import logging
import socket
from datetime import datetime
from abakit.model.log import Log


class FileLogger:
    def __init__(self, LOGFILE_PATH):
        """
        -CHECK FOR PRESENCE OF LOG FILE (RW PERMISSION)
        -SET CONFIG FOR LOGGING
        """
        hostname = socket.gethostname()
        LOGFILE = os.path.join(LOGFILE_PATH, 'process-' + str(hostname) + '.log')
        try:
            with open(LOGFILE, "a") as f:
                pass
        except FileNotFoundError:
            print("CREATED LOGFILE @ ", LOGFILE)
            Path(LOGFILE).touch()

        logging.basicConfig(
            filename=LOGFILE, level=logging.INFO, format="%(message)s", force=True
        )

    def logevent(self, msg: str):
        timestamp = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        logging.info(f"{timestamp} - {msg}")
        return timestamp


# PREVIOUS VERSION BELOW (LOG TO DB)
class DatabaseHandler(logging.Handler):
    def __init__(self,session):
        super().__init__()
        self.session = session

    def emit(self, record):
        log = Log(
            prep_id=record.name,
            level=record.levelname,
            logger=record.module,
            msg=record.msg,
        )
        self.session.add(log)
        self.session.commit()


def get_logger(prep_id, session,level=logging.INFO):
    handler = DatabaseHandler(session)
    logger = logging.getLogger(prep_id)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
