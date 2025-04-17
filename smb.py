# import example
# from smb import SambaConfigurator

import subprocess
import configparser
import os
from pathlib import Path

class SambaConfigurator:
    def __init__(self, debug=False):
        self.samba_config = "/etc/samba/smb.conf"
        self.backup_config = "/etc/samba/smb.conf.bak"
        self.shares = []
        self.debug = debug

    def _print(self, text):
        if (self.debug):
            print(text)

    def _run_command(self, command, input_text=None):
        """Утилита для выполнения команд с обработкой ввода"""
        args = {
            "args": command,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "shell": False
        }

        if self.debug:
            args["stdout"] = None
            args["stderr"] = None

        if input_text:
            proc = subprocess.Popen(**args, stdin=subprocess.PIPE, text=True)
            proc.communicate(input_text)
        else:
            subprocess.run(**args, check=True)

    def backup_config(self):
        """Создание резервной копии конфига"""
        if Path(self.samba_config).exists():
            self._run_command(["sudo", "cp", self.samba_config, self.backup_config])
            self._print(f"Резервная копия создана: {self.backup_config}")

    def create_linux_user(self, username, password):
        """Создание системного пользователя"""
        try:
            self._run_command(["sudo", "useradd", "-m", "-s", "/bin/bash", username])
            self._print(f"Пользователь {username} создан в системе")

            self._run_command(
                ["sudo", "passwd", username],
                input_text=f"{password}\n{password}\n"
            )
        except subprocess.CalledProcessError as e:
            self._print(f"Ошибка при создании пользователя: {e}")

    def create_samba_user(self, username, password):
        """Добавление пользователя в Samba"""
        self._run_command(
            ["sudo", "smbpasswd", "-a", username],
            input_text=f"{password}\n{password}\n"
        )
        self._print(f"Пользователь {username} добавлен в Samba")

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
            'smb encrypt': 'desired'
        }

        for share_name, share_config in self.shares:
            config[share_name] = share_config

        with open('/tmp/smb.conf.tmp', 'w') as f:
            config.write(f)

        self._run_command(["sudo", "mv", "/tmp/smb.conf.tmp", self.samba_config])
        self._run_command(["sudo", "chmod", "644", self.samba_config])
        self._print("Конфигурация Samba полностью обновлена")

    def add_share(self, share_name, path, valid_users=None, read_only=False, browsable=True, create_mode="0664", directory_mode="0775"):
        """Добавление общей папки"""
        if not os.path.exists(path):
            os.makedirs(path, mode=0o775)
            self._print(f"Создана директория {path}")

        # if valid_users:
        #     self._run_command(["sudo", "chown", f"{valid_users[0]}:{valid_users[0]}", path])
        # self._run_command(["sudo", "chmod", "775", path])

        # Создаем конфигурацию для шары
        share_config = {
            'path': path,
            'browsable': 'yes' if browsable else 'no',
            'read only': 'yes' if read_only else 'no',
            'writable': 'no' if read_only else 'yes',
            'guest ok': 'no',
            'create mask': create_mode,
            'directory mask': directory_mode,
            # 'force user': valid_users[0] if valid_users else 'nobody'
        }

        if valid_users:
            share_config['valid users'] = ' '.join(valid_users)

        self.shares.append((share_name, share_config))
        self._print(f"Общая папка '{share_name}' подготовлена для добавления")

    def restart_samba(self):
        """Перезапуск Samba"""
        self._run_command(["sudo", "systemctl", "restart", "smbd"])
        self._run_command(["sudo", "systemctl", "enable", "smbd"])
        self._print("Сервис Samba перезапущен")

    def configure_firewall(self):
        """Настройка фаервола для Samba"""
        try:
            self._run_command(["sudo", "ufw", "allow", "samba"])
            self._print("Правила фаервола добавлены")
        except subprocess.CalledProcessError:
            self._print("Не удалось настроить фаервол (возможно ufw не установлен)")

    def set_selinux_context(self, path):
        """Установка контекста SELinux для папки"""
        try:
            self._run_command(["sudo", "chcon", "-t", "samba_share_t", path])
            self._print(f"SELinux контекст установлен для {path}")
        except subprocess.CalledProcessError:
            self._print("Не удалось установить SELinux контекст (возможно SELinux отключен)")

# Пример использования
if __name__ == "__main__":
    samba = SambaConfigurator()

    # Создаем резервную копию конфига
    # samba.backup_config()

    # Создание пользователей
    users = [
        {'username': 'stolar', 'password': '6079815243'}
    ]

    for user in users:
        samba.create_linux_user(user['username'], user['password'])
        samba.create_samba_user(user['username'], user['password'])

    samba.add_share(
        share_name="test1",
        path="/home/stolar/test_mount/zalupa",
        valid_users=['stolar'],
        read_only=False
    )

    # Настройка глобальных параметров
    samba.configure_global_settings()

    # Настройка SELinux (если используется)
    # samba.set_selinux_context("/home/stolar/samba-test/test")

    # Завершение настройки
    samba.configure_firewall()
    samba.restart_samba()

    print("\nНастройка Samba завершена успешно!")
    print("Доступные общие папки:")
    for share_name, _ in samba.shares:
        print(f" - \\\\<server_ip>\\{share_name}")
