import logging
from abakit.model.log import Log

class DatabaseHandler(logging.Handler):
    def emit(self, record):
        log = Log(
            prep_id=record.name,
            level=record.levelname,
            logger=record.module,
            msg=record.msg,
        )
        self.session.add(log)
        self.session.commit()


def get_logger(prep_id, level=logging.INFO):
    handler = DatabaseHandler()

    logger = logging.getLogger(prep_id)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger
