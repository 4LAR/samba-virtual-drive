# import example
# from mount import VirtualDisk, list_filesystems

import subprocess
import os

class VirtualDiskError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class VirtualDisk:
    def __init__(self, disk_image):
        self.disk_image = disk_image
        self.loop_devices = []
        self._recover_loop_devices()

    def _recover_loop_devices(self):
        """Восстанавливает loop-устройства, если образ уже смонтирован."""
        try:
            loop_devs = subprocess.check_output(
                ['losetup', '-j', self.disk_image],
                stderr=subprocess.PIPE
            ).decode().strip()

            if loop_devs:
                for line in loop_devs.splitlines():
                    loop_dev = line.split(':')[0]
                    self.loop_devices.append(loop_dev)
        except subprocess.CalledProcessError:
            pass

    def _detect_filesystem(self):
        """Определяет тип файловой системы в образе."""
        try:
            result = subprocess.run(
                ["blkid", "-o", "value", "-s", "TYPE", self.disk_image],
                capture_output=True, text=True
            )
            return result.stdout.strip() if result.stdout else "unknown"
        except subprocess.CalledProcessError:
            return "unknown"

    def get_disk_info(self):
        """
        Возвращает информацию о виртуальном диске:
        - Размер файла образа (в МБ)
        - Файловую систему
        - Точки монтирования
        - Использованное и свободное место (если смонтирован)
        """
        if not os.path.exists(self.disk_image):
            raise VirtualDiskError("Файл диска не существует")

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
        """Проверяет, замонтирован ли диск (включая восстановленные loop-устройства)."""
        if not self.loop_devices:
            return False

        try:
            mounts = subprocess.check_output(['mount']).decode()
            return any(dev in mounts for dev in self.loop_devices)
        except subprocess.CalledProcessError:
            return False

    def get_mount_points(self):
        """Возвращает точки монтирования, даже если программа перезапускалась."""
        mount_points = []
        try:
            mounts = subprocess.check_output(['mount']).decode()
            for line in mounts.splitlines():
                if self.disk_image in line or any(dev in line for dev in self.loop_devices):
                    mount_point = line.split()[2]
                    mount_points.append(mount_point)
        except subprocess.CalledProcessError:
            pass
        return mount_points

    def create(self, size, fs_type='ext4'):
        """Создает виртуальный диск заданного размера (в МБ) с указанной файловой системой."""
        if os.path.exists(self.disk_image):
            raise VirtualDiskError("Such a virtual disk has already been created")

        subprocess.run(
            ['dd', 'if=/dev/zero', f'of={self.disk_image}', 'bs=1M', f'count={size}'],
            check=True
        )
        subprocess.run(['mkfs', '-t', fs_type, self.disk_image], check=True)

    def mount(self, mount_point):
        """Монтирует виртуальный диск в заданную точку монтирования."""
        if not os.path.exists(mount_point):
            os.makedirs(mount_point)

        loop_device = subprocess.check_output(
            ['losetup', '--show', '-f', self.disk_image]
        ).strip().decode()
        self.loop_devices.append(loop_device)

        subprocess.run(['mount', loop_device, mount_point], check=True)

    def unmount(self, mount_point):
        """Размонтирует виртуальный диск из заданной точки монтирования."""
        try:
            subprocess.run(['umount', mount_point], check=True)
        except subprocess.CalledProcessError as e:
            raise VirtualDiskError(f"Failed to unmount: {e}")

        for loop_device in self.loop_devices:
            try:
                subprocess.run(['losetup', '-d', loop_device], check=True)
            except subprocess.CalledProcessError as e:
                raise VirtualDiskError(f"Failed to detach loop device: {e}")

        self.loop_devices.clear()

    def resize(self, new_size):
        """Изменяет размер виртуального диска (в МБ)."""
        subprocess.run(
            ['dd', 'if=/dev/zero', f'of={self.disk_image}', 'bs=1M', f'count={new_size}'],
            check=True
        )

        for loop_device in self.loop_devices:
            try:
                subprocess.run(['resize2fs', loop_device], check=True)
            except subprocess.CalledProcessError as e:
                raise VirtualDiskError(f"Failed to resize filesystem: {e}")

    def get_mount_points(self):
        """Возвращает список точек монтирования, где диск может быть замонтирован."""
        mount_points = []
        try:
            output = subprocess.check_output(['mount']).decode()
            for line in output.splitlines():
                if self.disk_image in line or any(loop_device in line for loop_device in self.loop_devices):
                    mount_point = line.split()[2]
                    mount_points.append(mount_point)
        except subprocess.CalledProcessError:
            pass
        return mount_points

    def cleanup(self):
        """Удаляет файл виртуального диска."""
        if os.path.exists(self.disk_image):
            os.remove(self.disk_image)

def list_filesystems():
    """Выводит список доступных файловых систем."""
    try:
        output = subprocess.check_output(['cat', '/proc/filesystems']).decode()
        filesystems = [line.strip() for line in output.splitlines() if line and not line.startswith('nodev')]
        return filesystems
    except subprocess.CalledProcessError:
        return []
