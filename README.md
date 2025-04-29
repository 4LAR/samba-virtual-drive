English | [Русский](https://github.com/4LAR/samba-virtual-drive/blob/main/README-ru_RU.md)

Docker Container for Deploying .img Disks to a Samba Network

## How to Use

Using Docker Compose:

```yml
services:
  samba:
    image: 100lar/samba-virtual-drive
    container_name: samba-virtual-drive
    privileged: true
    environment:
      - SERVER_NAME=Samba Server              # ОDisplay name of the server in the network (visible in network neighborhood)
      - NETBIOS_NAME=SAMBA                    # NetBIOS server name (up to 15 chars, for compatibility with legacy clients)
      - MIN_PROTOCOL=SMB2                     # Minimum supported SMB version
      - MAX_PROTOCOL=SMB3                     # Maximum SMB version
    volumes:
      - /dev:/dev
      - ./virtual_drives:/app/virtual_drives  # Directory where virtual disks will be stored
      - ./config:/app/config                  # Path to the config
    ports:
      - "445:445"
      - "139:139"
```

Using Docker CLI:

```bash
docker run -d \
  --name samba-virtual-drive \
  --privileged \
  -v /dev:/dev \
  -v ./virtual_drives:/app/virtual_drives \
  -v ./config:/app/config \
  -p 445:445 \
  -p 139:139 \
  100lar/samba-virtual-drive
```

## Configuration

*On the first run, a __config.yml__  file will be generated in the __config/__ directory.*

The configuration file is a YAML document with the following main sections:

```yml
users:    # Required section
groups:   # Optional section
share:    # Optional section
```

### __Users__ section

Defines a list of users.

```yml
users:
  username1: "password1"  # Simple name:password mapping
  username2: "password2"
```

### __Groups__ section

Defines user groups and their members.

```yml
groups:
  groupname1:
    - user1
    - user2
  groupname2:
    - user3
```

### __Share__ section

Defines shared resources and their settings.

```yml
share:
  resource1:
    filename: data.img    # Optional
    size: 100GB           # Required (format: number + B/KB/MB/GB/TB/PB)
    read_only: false      # Optional (default: false)
    auto_resize: true     # Optional (default: false)
    users:                # At least one of "users" or "groups" is required
      - user1
    groups:
      - group1
```

### Full Configuration Example

```yml
users:
  user1: pass123
  admin: adminPass

groups:
  devs:
    - user1
  ops:
    - admin

share:
  development:
    filename: dev.img
    size: 50GB
    users:
      - user1
    groups:
      - devs
    auto_resize: true

  logs:
    size: 200GB
    read_only: true
    groups:
      - ops
```
