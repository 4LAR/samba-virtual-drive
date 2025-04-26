import os
import re
import json
from samba import Samba, SambaError, SambaConfigureError
# from mount import VirtualDisk, list_filesystems
from VirtualDisk import VirtualDisk
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

YELLOW_COLOR = "\033[1;33m"
BLUE_COLOR = "\033[1;34m"
TURQUOISE_COLOR = "\033[1;36m"
WHITE_COLOR = "\033[0m"

################################################################################

samba = Samba()
samba.stop_samba()

for user_key in USERS:
    try:
        samba.create_linux_user(user_key, USERS[user_key])
    except SambaError:
        print(f"User '{user_key}' already exist. Skipping")
    except Exception as e:
        print(e)
    samba.create_samba_user(user_key, USERS[user_key])

################################################################################

for key in SHARE:
    share_conf = SHARE[key]
    img_path = os.path.join(DISKS_PATH, share_conf["filename"] if "filename" in share_conf else (key + ".img"))
    img_mount_path = os.path.join(DISKS_MOUNT_PATH, key)
    disk = VirtualDisk(img_path)
    disk_size = int(convert_to_mb_auto(share_conf["size"]))
    try:
        disk.create(disk_size)
        print(f"Disk {key} created.")
    except Exception as e:
        print(f"Disk {key} exist. Skipping")

    for point in disk.get_mount_points():
        try:
            disk.unmount(point)
        except Exception as e:
            print(e)

    if disk.get_disk_info()["size_mb"] != disk_size:
        print(f"Resize {key} ({disk.get_disk_info()['size_mb']}MB => {disk_size}MB)")
        disk.resize(disk_size)

    disk.mount(img_mount_path)

    users_share = share_conf.get("users", [])
    for group in share_conf.get("groups", []):
        users_share.extend(user for user in GROUPS.get(group, []) if user not in users_share)

    disk_info = disk.get_disk_info()
    print()
    print(f"{TURQUOISE_COLOR}{key}:{WHITE_COLOR}")
    print(f"  {BLUE_COLOR}• Path:{WHITE_COLOR} {disk_info['disk_file']}")
    print(f"  {BLUE_COLOR}• Size:{WHITE_COLOR} {disk_info['size_mb']} MB")
    print(f"  {BLUE_COLOR}• Filesystem:{WHITE_COLOR} {disk_info['filesystem']}")
    print(f"  {BLUE_COLOR}• Mounted:{WHITE_COLOR} {'Yes' if disk_info['mounted'] else 'No'}")

    if disk_info['mounted']:
        print(f"  {BLUE_COLOR}• Mount points:{WHITE_COLOR}")
        for mp in disk_info['mount_points']:
            print(f"    - {mp}")

        print(f"  {BLUE_COLOR}• Usage:{WHITE_COLOR}")
        for mp, usage in disk_info['usage'].items():
            print(f"    {YELLOW_COLOR}{mp}:{WHITE_COLOR}")
            print(f"      Total: {usage['total_gb']:.2f} GB")
            print(f"      Used: {usage['used_gb']:.2f} GB ({usage['use_percent']:.1f}%)")
            print(f"      Free: {usage['free_gb']:.2f} GB")
    print()

    samba.add_share(
        share_name      = key,
        path            = img_mount_path,
        valid_users     = users_share,
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
    print(f" • \\\\<server_ip>\\{key}")
print()

samba.monitor()
