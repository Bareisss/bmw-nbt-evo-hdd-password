# Preservation-oriented imaging workflow

[English](IMAGING.md) | [Deutsch](IMAGING_DE.md)

After a successful ATA unlock, avoid modifying the original drive. The first goal should be a complete 1:1 image.

## Make the Linux block device read-only

```bash
sudo blockdev --setro /dev/sdX
sudo blockdev --getro /dev/sdX
```

The second command should print:

```text
1
```

This makes the Linux block device read-only without changing the drive's ATA security configuration.

## Image with GNU ddrescue

Install GNU ddrescue:

```bash
sudo apt update
sudo apt install -y gddrescue
```

First, preservation-oriented pass:

```bash
sudo ddrescue -n \
  /dev/sdX \
  /path/to/nbt-evo-hdd.img \
  /path/to/nbt-evo-hdd.map
```

`-n` first tries to recover as much data as possible without spending time on repeated retries. The map file records progress and lets later passes target only unresolved areas.

If read errors remain after the first pass, use the same map file for a retry pass:

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

## Continue work only on an image or clone

Perform subsequent filesystem analysis, extraction, modifications, or replacement-drive experiments on the image or on a clone, not on the original disk.

Before writing an image to an SSD or other target disk, identify the destination unambiguously with `lsblk`. Writing an image directly to `/dev/sdX` overwrites the target's partition table and filesystems completely.
