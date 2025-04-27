import subprocess

class Shell:
    def __init__(self, debug=False):
        self.debug = debug
        self.moduleName = ""

    def _print(self, text):
        print(f"[ {self.moduleName} ]" if len(self.moduleName) > 0 else "", text)

    def _run_command(self, command, input_text=None, check=True):
        """Выполнение команд с обработкой ввода"""
        args = {
            "args": command,
            "stdout": None if self.debug else subprocess.DEVNULL,
            "stderr": None if self.debug else subprocess.DEVNULL,
            "shell": False
        }

        if input_text:
            proc = subprocess.Popen(**args, stdin=subprocess.PIPE, text=True)
            proc.communicate(input_text)
        else:
            subprocess.run(**args, check=check)

    def _run_command_output(self, command):
        """Выполнение команд с выводом"""
        args = {
            "args": command,
            # "stdout": subprocess.PIPE,
            "stderr": None if self.debug else subprocess.DEVNULL,
            "shell": False
        }

        return subprocess.check_output(**args).decode()
