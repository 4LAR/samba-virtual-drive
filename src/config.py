# import example
# from config import CONFIG, USERS, GROUPS, SHARE

from jsonschema import validate, ValidationError
import yaml
import json
import os

################################################################################

CONFIG_FILENAME = "config/config.yml"
SCHEMA = {
    "type": "object",
    "properties": {
        "users": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {"type": "string"}
            },
            "additionalProperties": False
        },
        "groups": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "array",
                    "items": {"type": "string"}
                }
            },
            "additionalProperties": False
        },
        "share": {
            "type": "object",
            "patternProperties": {
                "^[a-zA-Z0-9_]+$": {
                    "type": "object",
                    "properties": {
                        "filename": {"type": "string"},
                        "size": {
                            "type": "string",
                            "pattern": "^\\d+(B|KB|MB|GB|TB|PB)$"
                        },
                        "read_only": {"type": "boolean"},
                        "users": {
                            "type": "array",
                            "items": {"type": "string"}
                        },
                        "groups": {
                            "type": "array",
                            "items": {"type": "string"}
                        }
                    },
                    "additionalProperties": False,
                    "required": ["size"],
                    "anyOf": [
                        {"required": ["users"]},
                        {"required": ["groups"]}
                    ]
                }
            },
            "additionalProperties": False
        }
    },
    "required": ["users"],
    "additionalProperties": False
}

################################################################################

def humanize_error(error):
    if error.validator == 'type':
        return f"Invalid data type in field '{'.'.join(error.path)}'. Expected {error.validator_value}, got {type(error.instance).__name__}."
    elif error.validator == 'patternProperties':
        return f"Invalid name '{error.path[-1]}' in section '{'.'.join(error.path[:-1])}'. Only letters, numbers and underscores are allowed."
    elif error.validator == 'additionalProperties':
        return f"Invalid field '{error.validator_value}' in section '{'.'.join(error.path)}'."
    elif error.validator == 'required':
        return f"Missing required field '{error.validator_value[0]}' in section '{'.'.join(error.path)}'."
    elif error.validator == 'pattern':
        if 'size' in error.path:
            return f"Invalid size format '{error.instance}' in section '{'.'.join(error.path)}'. Use 'number+unit' format (e.g., '1GB')."
    elif error.validator == 'anyOf':
        return f"Section '{'.'.join(error.path)}' must have at least one of the fields: 'users' or 'groups'."
    return str(error)

################################################################################

CONFIG = {
    "users": {
        "admin": "password"
    },
    "share": {
        "private": {
            "filename": "private.img",
            "size": "100MB",
            "read_only": False,
            "users": [
                "admin"
            ]
        }
    }
}
USERS = {}
GROUPS = {}
SHARE = {}

def read_config():
    global CONFIG
    global USERS
    global GROUPS
    global SHARE
    if not os.path.exists(CONFIG_FILENAME):
        os.makedirs(os.path.dirname(CONFIG_FILENAME), exist_ok=True)
        with open(CONFIG_FILENAME, 'w') as outfile:
            yaml.dump(CONFIG, outfile, default_flow_style=False, sort_keys=False)
        print(f"Configuration file '{CONFIG_FILENAME}' has been created. Please configure it and run the program again.")
        return False

    with open(CONFIG_FILENAME) as stream:
        CONFIG = yaml.safe_load(stream)

    try:
        validate(instance=CONFIG, schema=SCHEMA)
    except ValidationError as e:
        print(humanize_error(e))
        return False

    USERS   = CONFIG["users"] if "users" in CONFIG else {}
    GROUPS  = CONFIG["groups"] if "groups" in CONFIG else {}
    SHARE   = CONFIG["share"] if "share" in CONFIG else {}

    return True

if __name__ == "__main__":
    read_config()
    print("CONFIG:", json.dumps(CONFIG, indent=2, ensure_ascii=False))
    print("USERS:", USERS)
    print("GROUPS:", GROUPS)
    print("SHARE:", SHARE)

else:
    if not read_config():
        exit(1)
