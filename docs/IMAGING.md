# Preservation-oriented imaging workflow

After a successful ATA unlock, avoid modifying the original drive.

## Make the Linux block device read-only

```bash
sudo blockdev --setro /dev/sdX
sudo blockdev --getro /dev/sdX
```

The second command should print `1`.

## Image with ddrescue

Install GNU ddrescue:

```bash
sudo apt update
sudo apt install -y gddrescue
```

First pass:

```bash
sudo ddrescue -f -n \
  /dev/sdX \
  /path/to/nbt-evo-hdd.img \
  /path/to/nbt-evo-hdd.map
```

Retry pass:

```bash
sudo ddrescue -d -r3 \
  /dev/sdX \
  /path/to/nbt-evo-hdd.img \
  /path/to/nbt-evo-hdd.map
```

Hash the completed image:

```bash
sha256sum /path/to/nbt-evo-hdd.img \
  | tee /path/to/nbt-evo-hdd.img.sha256
```

Perform subsequent filesystem analysis on the image or on a clone, not on the original disk.
