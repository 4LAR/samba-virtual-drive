import subprocess
import os
from pathlib import Path
from shell import Shell
from .configure import SambaConfigure
from .logger import SambaLogger

class SambaError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class Samba(SambaConfigure, SambaLogger):
    shares = []
    def __init__(self,
        debug=False,
        min_protocol="SMB2",
        max_protocol="SMB3",
        server_name="Samba Server",
        netbios_name="SAMBA",
        perf_settings=None
    ):
        self.moduleName = "Samba"
        self.debug = debug

        self.min_protocol = min_protocol
        self.max_protocol = max_protocol
        self.server_name = server_name
        self.netbios_name = netbios_name

        # Стандартные настройки производительности (если не переданы)
        self.perf_settings = perf_settings or {
            "socket options": "TCP_NODELAY IPTOS_LOWDELAY SO_RCVBUF=65536 SO_SNDBUF=65536",
            "min receivefile size": 16384,
            "write cache size": 262144,
            "aio read size": 16384,
            "aio write size": 16384,
            "smb2 max read": 8388608,
            "smb2 max write": 8388608,
            "smb2 max trans": 8388608,
            "use sendfile": True,
            "strict locking": False,
            "read raw": True,
            "write raw": True,
        }

    def create_linux_user(self, username, password):
        """Создание системного пользователя"""
        try:
            self._run_command(["useradd", "-m", "-s", "/bin/bash", username])

            self._run_command(
                ["passwd", username],
                input_text=f"{password}\n{password}\n"
            )
        except subprocess.CalledProcessError as e:
            raise SambaError(f"Error creating user: {e}")

    def create_samba_user(self, username, password):
        """Добавление пользователя в Samba"""
        self._run_command(
            ["smbpasswd", "-a", username],
            input_text=f"{password}\n{password}\n"
        )

    def add_share(self, share_name, path, valid_users=None, read_only=False, browsable=True, create_mode="0664", directory_mode="0775"):
        """Добавление общей папки"""
        if not os.path.exists(path):
            os.makedirs(path, mode=0o775)

        self._run_command(["chmod", "775", path])

        share_config = {
            'path': path,
            'browsable': 'yes' if browsable else 'no',
            'read only': 'yes' if read_only else 'no',
            'writable': 'no' if read_only else 'yes',
            'guest ok': 'no',
            'create mask': create_mode,
            'directory mask': directory_mode,
            'force user': 'root'
            # 'force user': valid_users[0] if valid_users else 'nobody'
        }

        if valid_users:
            share_config['valid users'] = ' '.join(valid_users)

        self.shares.append((share_name, share_config))

    def restart_samba(self):
        """Перезапуск Samba"""
        self._run_command(["systemctl", "restart", "smbd"])
        self._run_command(["systemctl", "enable", "smbd"])

    def stop_samba(self):
        """Остановка Samba"""
        self._run_command(["systemctl", "stop", "smbd"])
