
import subprocess
from shell import Shell

class LoopError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class LoopManager(Shell):
    loop_devices = []

    def __init__(self):
        pass

    def _recover_loop_devices(self):
        """Восстанавливает loop-устройства, если образ уже смонтирован."""
        try:
            loop_devs = self._run_command_output(
                ['losetup', '-j', self.disk_image]
            ).strip()

            if loop_devs:
                for line in loop_devs.splitlines():
                    loop_dev = line.split(':')[0]
                    self.loop_devices.append(loop_dev)
        except subprocess.CalledProcessError:
            pass

    def _get_loop_device(self):
        """Получает или создает loop-устройство для операций с файловой системой."""
        if not self.loop_devices:
            try:
                loop_dev = self._run_command_output(
                    ['losetup', '--find', '--show', self.disk_image]
                ).strip()

                self.loop_devices.append(loop_dev)
                return loop_dev, True
            except subprocess.CalledProcessError as e:
                raise LoopError(f"Failed to setup loop device: {e}")
        return self.loop_devices[0], False

    def _release_loop_device(self, loop_device, temporary):
        """Освобождает loop-устройство, если оно было временно создано."""
        if temporary:
            try:
                self._run_command(['losetup', '-d', loop_device])

                self.loop_devices.remove(loop_device)
            except subprocess.CalledProcessError as e:
                raise LoopError(f"Failed to detach loop device: {e}")
