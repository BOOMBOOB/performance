import logging.config
from config.yml_agrs_parse import Args


LOG_CONFIG = Args().get_yml_data('log.yml')
logging.config.dictConfig(LOG_CONFIG)

logger = logging.getLogger("console_logger")