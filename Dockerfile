FROM python:3.12

RUN apt-get update && \
  apt-get install -y samba kmod systemctl && \
  apt-get clean && \
  rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . .

CMD ["python3", "main.py"]
