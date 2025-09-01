import logging
from settings import settings

LEVEL = getattr(logging, settings.log_level.upper(), logging.INFO)
logging.basicConfig(level=LEVEL, format='%(levelname)s: %(message)s')
logger = logging.getLogger("entertainment_planner")
