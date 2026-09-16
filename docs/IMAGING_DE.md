# Sicheres Imaging der entsperrten NBT-EVO-HDD

[English](IMAGING.md) | [Deutsch](IMAGING_DE.md)

Nach einem erfolgreichen ATA-Unlock sollte die Original-HDD nicht weiter verändert werden. Ziel ist zuerst ein vollständiges 1:1-Image.

## Linux-Blockgerät read-only setzen

```bash
sudo blockdev --setro /dev/sdX
sudo blockdev --getro /dev/sdX
```

Der zweite Befehl sollte ausgeben:

```text
1
```

Damit wird das Linux-Blockgerät schreibgeschützt. Das ändert nicht die ATA-Security-Konfiguration der HDD.

## Image mit GNU ddrescue erstellen

Installation:

```bash
sudo apt update
sudo apt install -y gddrescue
```

Erster schonender Durchlauf:

```bash
sudo ddrescue -n \
  /dev/sdX \
  /pfad/zum/nbt-evo-hdd.img \
  /pfad/zum/nbt-evo-hdd.map
```

`-n` versucht zunächst, möglichst viele Daten ohne aufwendige Wiederholungsversuche zu sichern. Die Map-Datei speichert den Fortschritt und erlaubt spätere gezielte Wiederholungen.

Falls nach dem ersten Durchlauf noch Lesefehler übrig sind, kann mit derselben Map-Datei ein Retry-Durchlauf erfolgen:

```bash
sudo ddrescue -d -r3 \
  /dev/sdX \
  /pfad/zum/nbt-evo-hdd.img \
  /pfad/zum/nbt-evo-hdd.map
```

Danach einen SHA-256-Hash des fertigen Images erzeugen:

```bash
sha256sum /pfad/zum/nbt-evo-hdd.img \
  | tee /pfad/zum/nbt-evo-hdd.img.sha256
```

## Weiterarbeiten nur auf Image oder Klon

Dateisystemanalyse, Extraktion, Modifikationen oder Versuche mit Ersatzlaufwerken sollten anschließend auf dem Image oder auf einer daraus erzeugten Kopie stattfinden, nicht auf der Original-HDD.

Vor jedem Schreibvorgang auf eine SSD oder andere Zielplatte das Zielgerät mit `lsblk` eindeutig identifizieren. Ein direktes Schreiben eines Images auf `/dev/sdX` überschreibt die vorhandene Partitionstabelle und alle Dateisysteme auf dem Ziel vollständig.
