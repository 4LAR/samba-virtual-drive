import os
import re
from smb import SambaConfigurator
from mount import VirtualDisk, list_filesystems
from config import USERS, GROUPS, SHARE

################################################################################

def convert_to_mb(size, unit):
    unit = unit.upper()

    conversion_factors = {
        'B': 1 / (1024 * 1024),
        'KB': 1 / 1024,
        'MB': 1,
        'GB': 1024,
        'TB': 1024 * 1024,
        'PB': 1024 * 1024 * 1024
    }

    if unit not in conversion_factors:
        raise ValueError(f"Unsupported unit: {unit}. Supported units are: B, KB, MB, GB, TB, PB")

    return size * conversion_factors[unit]

def convert_to_mb_auto(size_str):
    match = re.match(r'^([\d.]+)\s*([A-Za-z]+)$', size_str.strip())
    if not match:
        raise ValueError("Invalid size format. Expected format like '500KB' or '2GB'")

    size = float(match.group(1))
    unit = match.group(2).upper()

    return convert_to_mb(size, unit)

################################################################################

DISKS_PATH = os.path.abspath("./virtual_drives")
os.makedirs(DISKS_PATH, exist_ok=True)

DISKS_MOUNT_PATH = os.path.abspath("/mnt/virtual/")
os.makedirs(DISKS_MOUNT_PATH, exist_ok=True)

DISKS_LIST = []
DISKS_CONF = [
    {
        "name": "private",
        "size": "1GB",
        "users": ["admin"],
        "read_only": False
    }, {
        "name": "test",
        "size": "2GB",
        "users": ["admin"],
        "read_only": False
    }
]

################################################################################

samba = SambaConfigurator()

for user_key in USERS:
    samba.create_linux_user(user_key, USERS[user_key])
    samba.create_samba_user(user_key, USERS[user_key])

################################################################################

for key in SHARE:
    share_conf = SHARE[key]
    img_path = os.path.join(DISKS_PATH, share_conf["filename"] if "filename" in share_conf else (key + ".img"))
    img_mount_path = os.path.join(DISKS_MOUNT_PATH, key)
    disk = VirtualDisk(img_path)
    try:
        disk.create(int(convert_to_mb_auto(share_conf["size"])))
        print(f"Disk {key} created.")
    except Exception as e:
        # print(e)
        print(f"Disk {key} exist. Skipping")

    for point in disk.get_mount_points():
        try:
            disk.unmount(point)
        except Exception as e:
            print(e)


    disk.mount(img_mount_path)

    samba.add_share(
        share_name      = key,
        path            = img_mount_path,
        valid_users     = share_conf["users"] if "users" in share_conf else [],
        read_only       = share_conf["read_only"] if "read_only" in share_conf else False
    )

    DISKS_LIST.append(disk)

# print(DISKS_LIST)

################################################################################

samba.configure_global_settings()
try:
    samba.configure_firewall()
except Exception as e:
    print(e)

samba.restart_samba()

print("Saamba is running")
for key in SHARE:
    print(f" - \\\\<server_ip>\\{key}")

import time
while True:
    time.sleep(1)
