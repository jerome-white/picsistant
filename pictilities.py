import os
import logging

#
# Setup logger
#
logging.basicConfig(
    format='[ %(asctime)s %(levelname)s %(process)d ] %(message)s',
    datefmt="%H:%M:%S",
    level=os.environ.get('PYTHONLOGLEVEL', 'info').upper(),
)
logging.captureWarnings(True)
Logger = logging.getLogger(__name__)
