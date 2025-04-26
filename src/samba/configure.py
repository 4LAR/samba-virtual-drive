
from shell import Shell
import subprocess
import configparser

class SambaConfigureError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class SambaConfigure(Shell):
    samba_config = "/etc/samba/smb.conf"
    backup_config = "/etc/samba/smb.conf.bak"

    def __init__(self, shares):
        self.shares = shares

    def backup_config(self):
        """Создание резервной копии конфига"""
        if Path(self.samba_config).exists():
            self._run_command(["cp", self.samba_config, self.backup_config])

    def configure_global_settings(self):
        """Настройка глобальных параметров Samba"""
        config = configparser.ConfigParser()

        config['global'] = {
            'workgroup': 'WORKGROUP',
            'server string': 'Samba Server',
            'netbios name': 'PYTHON-SAMBA',
            'security': 'user',
            'map to guest': 'bad user',
            'dns proxy': 'no',
            'server min protocol': 'SMB2',
            'server max protocol': 'SMB3',
            'smb encrypt': 'desired',
            # Увеличиваем размер буферов
            "min receivefile size": "16384",
            "write cache size": "262144",
            "getwd cache": "yes",
             # Отключаем ненужные проверки
            "strict locking": "no",

            "aio read size": "16384",
            "aio write size": "16384",
            "use sendfile": "yes",
            # Увеличиваем максимальный размер SMB-пакетов
            "server max protocol": "SMB3",
            "server min protocol": "SMB2",
            "smb2 max read": "8388608",
            "smb2 max write": "8388608",
            "smb2 max trans": "8388608",
            # Кэширование
            "kernel share modes": "no",
            "kernel oplocks": "no",
            "posix locking": "no"
        }

        for share_name, share_config in self.shares:
            config[share_name] = share_config

        with open('/tmp/smb.conf.tmp', 'w') as f:
            config.write(f)

        self._run_command(["mv", "/tmp/smb.conf.tmp", self.samba_config])
        self._run_command(["chmod", "644", self.samba_config])

    def configure_firewall(self):
        """Настройка фаервола для Samba"""
        try:
            self._run_command(["ufw", "allow", "samba"])
        except subprocess.CalledProcessError:
            raise SambaConfigureError("Failed to configure firewall (maybe ufw is not installed)")

    def set_selinux_context(self, path):
        """Установка контекста SELinux для папки"""
        try:
            self._run_command(["chcon", "-t", "samba_share_t", path])
            self._print(f"SELinux контекст установлен для {path}")
        except subprocess.CalledProcessError:
            raise SambaConfigureError("Failed to set SELinux context (maybe SELinux is disabled)")
