from shell import Shell
import subprocess
import configparser
from pathlib import Path

class SambaConfigureError(Exception):
    def __init__(self, message):
        super().__init__(message)
        self.message = message

    def __str__(self):
        return f"{self.message}"

class SambaConfigure(Shell):
    samba_config = "/etc/samba/smb.conf"
    backup_config = "/etc/samba/smb.conf.bak"

    def backup_config(self):
        """Создание резервной копии конфига"""
        if Path(self.samba_config).exists():
            self._run_command(["cp", self.samba_config, self.backup_config])

    def configure_global_settings(self):
        """Настройка глобальных параметров Samba"""
        config = configparser.ConfigParser()

        # Базовые настройки
        config['global'] = {
            'workgroup': 'WORKGROUP',
            'server string': self.server_name,
            'netbios name': self.netbios_name,
            'security': 'user',
            'map to guest': 'bad user',
            'dns proxy': 'no',
            'server min protocol': self.min_protocol,
            'server max protocol': self.max_protocol,
            'smb encrypt': 'desired',
            'getwd cache': 'yes',
        }

        # Добавляем параметры производительности
        for key, value in self.perf_settings.items():
            if isinstance(value, bool):
                value = "yes" if value else "no"
            config['global'][key] = str(value)

        # Добавляем шары
        for share_name, share_config in self.shares:
            config[share_name] = share_config

        # Сохраняем конфиг
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
