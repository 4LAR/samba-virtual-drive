
import subprocess
import os

from .loop import LoopManager
from .diskInfo import diskInfo
from .operations import diskOperations

class VirtualDisk(LoopManager, diskInfo, diskOperations):
    def __init__(self, disk_image, debug=False):
        self.moduleName = "VirtualDisk"
        self.disk_image = disk_image
        self.debug = debug
        self._recover_loop_devices()
