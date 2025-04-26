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
            "stdout": subprocess.PIPE,
            "stderr": subprocess.PIPE,
            "shell": False
        }

        if not self.debug:
            args["stdout"] = None
            args["stderr"] = None

        if input_text:
            proc = subprocess.Popen(**args, stdin=subprocess.PIPE, text=True)
            proc.communicate(input_text)
        else:
            subprocess.run(**args, check=check)

    def _run_command_output(self, command):
        """Выполнение команд с выводом"""
        args = {
            "args": command,
            "stderr": subprocess.PIPE,
            "shell": False
        }

        if not self.debug:
            args["stderr"] = None

        return subprocess.check_output(**args).decode()
