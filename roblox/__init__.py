import logging
from roblox.client import Roblox as _Roblox
from roblox.enums import AssetType

# logging setup
logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s")

log = logging.getLogger(__name__)
log.setLevel(logging.DEBUG)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)

Roblox = _Roblox
