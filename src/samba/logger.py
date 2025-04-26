from datetime import datetime
import json
import time
from shell import Shell

class SambaLogger(Shell):
    sessions = {}
    tcons = {}
    open_files = {}
    def __init__(self):
        pass

    def _get_status_json(self):
        return json.loads(self._run_command_output(['smbstatus', '-j']))

    def _log_event(self, event_type, details):
        timestamp = f"[ {datetime.now().strftime('%d.%m.%Y %H:%M:%S')} ]"
        print(timestamp, details)

    def _track_objects(self, current_objects, stored_objects, object_type):
        # Handle new objects
        for obj_id, obj_data in current_objects.items():
            if obj_id not in stored_objects:
                stored_objects[obj_id] = obj_data
                self._log_event(
                    f"new_{object_type}",
                    self._get_object_message(object_type, 'opened', obj_id, obj_data)
                )

        # Handle closed objects
        closed_objects = set(stored_objects) - set(current_objects)
        for obj_id in closed_objects:
            obj_data = stored_objects.pop(obj_id)
            self._log_event(
                f"closed_{object_type}",
                self._get_object_message(object_type, 'closed', obj_id, obj_data)
            )

    def _get_object_message(self, object_type, action, obj_id, obj_data):
        if object_type == 'tcons':
            return {
                'opened': f"Opened new connection: {obj_data['machine']} ({obj_id}) to '{obj_data['service']}'",
                'closed': f"Disconnected: {obj_data['machine']} ({obj_id}) authorized as '{obj_data['service']}'"
            }[action]
        elif object_type == 'sessions':
            return {
                'opened': f"Created new session: {obj_data['remote_machine']} ({obj_id}) authorized as '{obj_data['username']}'",
                'closed': f"Removed session: {obj_data['remote_machine']} ({obj_id}) authorized as '{obj_data['username']}'"
            }[action]
        elif object_type == 'open_files':
            return {
                'opened': f"Open file '{obj_data['filename']}' in '{obj_data['service_path'].split('/')[-1]}'",
                'closed': f"Close file '{obj_data['filename']}' in '{obj_data['service_path'].split('/')[-1]}'"
            }[action]
        return ""

    def monitor(self, delay=2):
        while True:
            try:
                data = self._get_status_json()

                self._track_objects(data.get('tcons', {}), self.tcons, 'tcons')
                self._track_objects(data.get('sessions', {}), self.sessions, 'sessions')
                self._track_objects(data.get('open_files', {}), self.open_files, 'open_files')

            except Exception as e:
                self._log_event('error', f"Error in monitoring: {str(e)}")

            time.sleep(delay)
