from shell import Shell
from datetime import datetime
import subprocess
import sys
import time
import re
import json

class SambaLogger(Shell):
    sessions = {}
    tcons = {}
    open_files = {}
    def __init__(self):
        pass

    def _get_status_json(self):
        return json.loads(self._run_command_output(
            ['smbstatus', '-j']
        ))

    def monitor(self, delay=2):
        while True:
            data = self._get_status_json()
            # print(json.dumps(data, indent=4))

            date_now = f"[ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} ]"

            # Соединения
            tcons = data["tcons"]
            for con in tcons:
                if not (con in self.tcons.keys()):
                    con_data = tcons[con]
                    self.tcons[con] = {
                        "service": con_data['service'],
                        "machine": con_data['machine']
                    }

                    print(date_now, f"Opened new connection: {con_data['machine']} ({con}) to '{con_data['service']}'")

            closed_tcons = list(set(self.tcons.keys()) - set(tcons.keys()))
            for con in closed_tcons:
                con_data = self.tcons[con]
                print(date_now, f"Desconnected: {con_data['machine']} ({con}) authorized as '{con_data['service']}'")
                self.tcons.pop(con)

            # Сессии
            sessions = data["sessions"]
            for ses in sessions:
                if not (ses in self.sessions.keys()):
                    ses_data = sessions[ses]
                    self.sessions[ses] = {
                        "remote_machine": ses_data['remote_machine'],
                        "username": ses_data['username']
                    }

                    print(date_now, f"Created new session: {ses_data['remote_machine']} ({ses}) authorized as '{ses_data['username']}'")

            closed_sessions = list(set(self.sessions.keys()) - set(sessions.keys()))
            for ses in closed_sessions:
                ses_data = self.sessions[ses]
                print(date_now, f"Removed session: {ses_data['remote_machine']} ({ses}) authorized as '{ses_data['username']}'")
                self.sessions.pop(ses)

            # Открытые файлы
            open_files = data["open_files"]
            for file in open_files:
                if not (file in self.open_files.keys()):
                    file_data = open_files[file]
                    self.open_files[file] = {
                        "service_path": file_data['service_path'],
                        "filename": file_data['filename']
                    }

                    print(date_now, f"Open file '{file_data['filename']}' in '{file_data['service_path'].split('/')[-1]}'")

            closed_open_files = list(set(self.open_files.keys()) - set(open_files.keys()))
            for file in closed_open_files:
                file_data = self.open_files[file]
                print(date_now, f"Close file '{file_data['filename']}' in '{file_data['service_path'].split('/')[-1]}'")
                self.open_files.pop(file)

            time.sleep(delay)
