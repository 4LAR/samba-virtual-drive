[English](https://github.com/4LAR/samba-virtual-drive/blob/main/README.md) | Русский

Docker-контейнер для развертывания .img-дисков в Samba-сеть

## Как использовать

Используя Docker compose:

```yml
services:
  samba:
    image: 100lar/samba-virtual-drive
    container_name: samba-virtual-drive
    privileged: true
    environment:
      - SERVER_NAME=Samba Server              # Отображаемое имя сервера в сети (видно в сетевом окружении)
      - NETBIOS_NAME=SAMBA                    # NetBIOS-имя сервера (до 15 символов, для совместимости со старыми клиентами)
      - MIN_PROTOCOL=SMB2                     # Минимальная поддерживаемая версия SMB
      - MAX_PROTOCOL=SMB3                     # Максимальная версия SMB
    volumes:
      - /dev:/dev
      - ./virtual_drives:/app/virtual_drives  # Место куда будут сохраняться виртуальные диски
      - ./config:/app/config                  # Путь до конфига
    ports:
      - "445:445"
      - "139:139"
```

Используя Docker CLI:

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

## Конфигурация

*При первом запуске сгенерируется __config.yml__ в директории __config/__.*

Конфигурационный файл представляет собой YAML-документ со следующими основными разделами:

```yml
users:    # Обязательный раздел
groups:   # Опциональный раздел
share:    # Опциональный раздел
```

### Раздел __users__

Определяет список пользователей системы.

```yml
users:
  username1: "password1"  # Простое сопоставление имя:пароль
  username2: "password2"
```

### Раздел __groups__

Определяет группы пользователей и их членов.

```yml
groups:
  groupname1:
    - user1
    - user2
  groupname2:
    - user3
```

### Раздел __share__

Определяет общие ресурсы и их настройки.

```yml
share:
  resource1:
    filename: data.img    # Опционально
    size: 100GB           # Обязательно (формат: число + B/KB/MB/GB/TB/PB)
    read_only: false      # Опционально (по умолчанию false)
    auto_resize: true     # Опционально (по умолчанию false)
    users:                # Хотя бы один из users или groups обязателен
      - user1
    groups:
      - group1
```

### Полный пример конфигурации

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
