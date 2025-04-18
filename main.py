import os
import re
from smb import SambaConfigurator
from mount import VirtualDisk, list_filesystems

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

USERS = {
    "admin": "password"
}
# os.path.abspath
# os.path.join(a, "test")
# os.makedirs(path, exist_ok=True)

DISKS_PATH = os.path.abspath("./virtual_drives")
os.makedirs(DISKS_PATH, exist_ok=True)

DISKS_MOUNT_PATH = os.path.abspath("/mnt/virtual/")
os.makedirs(DISKS_MOUNT_PATH, exist_ok=True)

DISKS_LITS = []
DISKS_CONF = [
    {
        "name": "private",
        "size": "1GB",
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

for disk_conf in DISKS_CONF:
    img_path = os.path.join(DISKS_PATH, disk_conf["name"] + ".img")
    img_mount_path = os.path.join(DISKS_MOUNT_PATH, disk_conf["name"])
    disk = VirtualDisk(img_path)
    try:
        disk.create(int(convert_to_mb_auto(disk_conf["size"])))
        print(f"Disk {disk_conf["name"]} created.")
    except Exception as e:
        # print(e)
        print(f"Disk {disk_conf["name"]} exist. Skipping")

    for point in disk.get_mount_points():
        disk.unmount(point)

    disk.mount(img_mount_path)

    samba.add_share(
        share_name      = disk_conf["name"],
        path            = img_mount_path,
        valid_users     = disk_conf["users"],
        read_only       = disk_conf["read_only"]
    )

    DISKS_LITS.append(disk)

# print(DISKS_LITS)

################################################################################

samba.configure_global_settings()
samba.configure_firewall()
samba.restart_samba()

print("Saamba is running")
for disk_conf in DISKS_CONF:
    print(f" - \\\\<server_ip>\\{disk_conf["name"]}")
