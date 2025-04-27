from shell import Shell
from .diskError import VirtualDiskError
import subprocess
import os

class diskOperations(Shell):
    def __init__(self, disk_image, loop_devices):
        self.disk_image = disk_image
        self.loop_devices = loop_devices

    def create(self, size, fs_type='ext4'):
        """Создает виртуальный диск заданного размера (в МБ) с указанной файловой системой."""
        if os.path.exists(self.disk_image):
            raise VirtualDiskError("Such a virtual disk has already been created")

        self._run_command(['dd', 'if=/dev/zero', f'of={self.disk_image}', 'bs=1M', f'count={size}'], check=True)
        self._run_command(['mkfs', '-t', fs_type, self.disk_image], check=True)

    def mount(self, mount_point):
        """Монтирует виртуальный диск в заданную точку монтирования."""
        if not os.path.exists(mount_point):
            os.makedirs(mount_point)

        loop_device = self._run_command_output(
            ['losetup', '--show', '-f', self.disk_image]
        ).strip()
        self.loop_devices.append(loop_device)

        self._run_command(['mount', loop_device, mount_point], check=True)

    def unmount(self, mount_point):
        """Размонтирует виртуальный диск из заданной точки монтирования."""
        try:
            self._run_command(['umount', mount_point], check=True)
        except subprocess.CalledProcessError as e:
            raise VirtualDiskError(f"Failed to unmount: {e}")

        for loop_device in self.loop_devices:
            try:
                self._run_command(['losetup', '-d', loop_device], check=True)
            except subprocess.CalledProcessError as e:
                raise VirtualDiskError(f"Failed to detach loop device: {e}")

        self.loop_devices.clear()

    def resize(self, new_size_mb):
        """Изменяет размер виртуального диска (в МБ)."""
        if not os.path.exists(self.disk_image):
            raise VirtualDiskError("Disk image does not exist")

        current_size = os.path.getsize(self.disk_image) // (1024 * 1024)
        if new_size_mb <= current_size:
            raise VirtualDiskError("New size must be larger than current size")

        loop_device, is_temp = self._get_loop_device()

        try:
            # 1. Изменяем размер образа
            self._run_command(
                ['truncate', '-s', f'{new_size_mb}M', self.disk_image],
                check=True
            )

            # 2. Расширяем loop-устройство (важно!)
            self._run_command(
                ['losetup', '-c', loop_device],
                check=True
            )

            fs_type = self._detect_filesystem()
            if fs_type.startswith('ext'):
                # 3. Проверяем файловую систему
                self._run_command(
                    ['e2fsck', '-f', '-y', loop_device],
                    check=True
                )

                # 4. Явно указываем новый размер файловой системы
                # Сначала получаем размер в блоках
                block_size = int(self._run_command_output(
                    ['tune2fs', '-l', loop_device]
                ).split('Block size:')[1].split()[0])

                blocks_count = (new_size_mb * 1024 * 1024) // block_size

                # 5. Изменяем размер с явным указанием количества блоков
                self._run_command(
                    ['resize2fs', loop_device, f'{blocks_count}'],
                    check=True
                )

                # 6. Проверяем результат
                final_size = os.path.getsize(self.disk_image) // (1024 * 1024)
                if final_size < new_size_mb:
                    raise VirtualDiskError(f"Failed to resize: expected {new_size_mb}MB, got {final_size}MB")

            else:
                raise VirtualDiskError(f"Unsupported filesystem for resize: {fs_type}")

        except subprocess.CalledProcessError as e:
            raise VirtualDiskError(f"Failed to resize disk: {e}")
        except Exception as e:
            raise VirtualDiskError(f"Unexpected error during resize: {e}")
        finally:
            self._release_loop_device(loop_device, is_temp)

    def cleanup(self):
        """Удаляет файл виртуального диска."""
        if os.path.exists(self.disk_image):
            os.remove(self.disk_image)
