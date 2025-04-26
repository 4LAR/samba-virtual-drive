from shell import Shell
from .diskError import VirtualDiskError
import subprocess
import os

class diskInfo(Shell):
    def __init__(self, disk_image, loop_devices):
        self.disk_image = disk_image
        self.loop_devices = loop_devices

    def _detect_filesystem(self):
        """Specifies the file system type in the image."""
        try:
            result = self._run_command_output(
                ["blkid", "-o", "value", "-s", "TYPE", self.disk_image],
            )
            return result.strip() if result else "unknown"
        except subprocess.CalledProcessError:
            return "unknown"

    def get_disk_info(self):
        """
        Returns information about the virtual disk:
        - Image file size (in MB)
        - File system
        - Mount points
        - Used and free space (if mounted)
        """
        if not os.path.exists(self.disk_image):
            raise VirtualDiskError(f"The disk file ({self.disk_image}) does not exist")

        info = {
            "disk_file": self.disk_image,
            "size_mb": os.path.getsize(self.disk_image) // (1024 * 1024),
            "filesystem": self._detect_filesystem(),
            "mounted": self.is_mounted(),
            "mount_points": self.get_mount_points(),
            "usage": {}
        }

        if info["mounted"]:
            for mount_point in info["mount_points"]:
                disk_usage = os.statvfs(mount_point)
                info["usage"][mount_point] = {
                    "total_gb": (disk_usage.f_blocks * disk_usage.f_frsize) / (1024 ** 3),
                    "used_gb": ((disk_usage.f_blocks - disk_usage.f_bfree) * disk_usage.f_frsize) / (1024 ** 3),
                    "free_gb": (disk_usage.f_bavail * disk_usage.f_frsize) / (1024 ** 3),
                    "use_percent": 100 - (disk_usage.f_bavail / disk_usage.f_blocks * 100)
                }

        return info

    def is_mounted(self):
        """Checks if the disk is mounted (including recovered loop devices)."""
        if not self.loop_devices:
            return False

        try:
            mounts = self._run_command_output(['mount'])
            return any(dev in mounts for dev in self.loop_devices)
        except subprocess.CalledProcessError:
            return False

    def get_mount_points(self):
        """Returns a list of mount points where the disk can be mounted."""
        mount_points = []
        try:
            output = self._run_command_output(['mount'])
            for line in output.splitlines():
                if self.disk_image in line or any(loop_device in line for loop_device in self.loop_devices):
                    mount_point = line.split()[2]
                    mount_points.append(mount_point)
        except subprocess.CalledProcessError:
            pass
        return mount_points
