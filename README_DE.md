# BMW NBT EVO HDD-Passwort ableiten

[English](README.md) | [Deutsch](README_DE.md)

Dieses Repository dokumentiert die Herleitung des ATA-User-Passworts, das bei BMW/Harman NBT-EVO-Festplatten verwendet wird, und enthält einen kleinen Offline-Rechner dafür.

Dieses öffentliche Repository enthält absichtlich **keine realen Fahrzeug- oder Headunit-Kennungen, keine realen MAC-Adressen, keine realen Seriennummern, keine echten Aufkleberdaten und kein reales, ausgelesenes Passwort**. Alle Beispiele sind synthetisch.

## Rekonstruierter Algorithmus

Für den untersuchten BMW/Harman-`srv-hddmgr2`-Build wird das ATA-User-Passwort so erzeugt:

```text
payload = ETH_MAC_raw_6_bytes
       || BT_MAC_raw_6_bytes
       || E2P.ProdLogistic.SerialNo_raw_bytes

digest = MD5(payload)
password = Base64(digest[0:15])
```

Da exakt 15 Bytes mit Standard-Base64 kodiert werden, entsteht ein 20 Zeichen langes ASCII-Passwort ohne `=`-Padding.

## Welche Nummer vom Aufkleber wird verwendet?

Die 7-stellige Angabe `SNR:` darf **nicht direkt** verwendet werden.

Die Security-Routine arbeitet mit `E2P.ProdLogistic.SerialNo` als Rohbytes. Bei der 2018er NBT-EVO-HU, mit der die Methode praktisch verifiziert wurde, ließ sich dieser 10-Byte-Wert aus der **Haupt-Barcodezeile auf dem HU-Aufkleber** rekonstruieren:

```text
serial_raw = 0x00 || ASCII(letzte 9 Zeichen des Haupt-Barcodes)
```

Die Auswahl auf dem Aufkleber ist also:

```text
HU-Aufkleber
  Haupt-Barcode  ---> die LETZTEN 9 Zeichen verwenden
  SNR:           ---> NICHT direkt verwenden
  CRIN:          ---> bei der verifizierten Rekonstruktion nicht verwendet
```

Angenommen, ein rein *synthetischer* Haupt-Barcode wäre:

```text
ABCDE1A2B3C4D5
```

Dann gilt:

```text
letzte 9 Barcode-Zeichen = 1A2B3C4D5
ASCII-Bytes               = 31 41 32 42 33 43 34 44 35
Präfix                    = 00
Serial raw                = 00 31 41 32 42 33 43 34 44 35
Serial hex                = 00314132423343344435
```

Der komplette Ablauf lautet damit:

1. Ethernet-MAC vom HU-Aufkleber ablesen.
2. Bluetooth-MAC vom HU-Aufkleber ablesen.
3. Den **Haupt-Barcode** auf dem HU-Aufkleber ablesen.
4. Davon die **letzten 9 Zeichen** nehmen.
5. Diese 9 Zeichen als ASCII-Bytes kodieren.
6. Ein Nullbyte (`0x00`) davor setzen.
7. `ETH raw || BT raw || serial raw` zusammenfügen.
8. MD5 über diesen Byte-String berechnen.
9. Nur die ersten 15 MD5-Bytes verwenden.
10. Diese 15 Bytes mit Standard-Base64 kodieren.

Wenn der exakte Diagnosewert `E2P.ProdLogistic.SerialNo` verfügbar ist, sollte dieser exakte Wert immer der Ableitung vom Aufkleber vorgezogen werden.

> **Gültigkeitsbereich:** Die Zuordnung `0x00 + ASCII(letzte 9 Zeichen des Haupt-Barcodes)` wurde praktisch an einer 2018er NBT-EVO-HU verifiziert. Daraus folgt noch nicht, dass sie bei jeder EVO-Hardwareversion, jedem Produktionszeitraum und jedem Markt identisch ist.

## Synthetisches Beispiel

```text
Ethernet-MAC  = 00:11:22:33:44:55
Bluetooth-MAC = AA:BB:CC:DD:EE:FF
Haupt-Barcode = ABCDE1A2B3C4D5
```

Abgeleiteter Serialwert:

```text
letzte 9 Zeichen = 1A2B3C4D5
Serial hex        = 00314132423343344435
```

Aufruf:

```bash
python3 tools/derive_evo_hdd_password.py \
  --eth 00:11:22:33:44:55 \
  --bt AA:BB:CC:DD:EE:FF \
  --label-barcode ABCDE1A2B3C4D5 \
  --verbose
```

Für dieses synthetische Beispiel lautet die Ausgabe:

```text
hAR5JcWED+Zf31RoQgHF
```

## Bevorzugte Methode: exakter E2P-Serialwert

Falls der exakte Hexwert von `E2P.ProdLogistic.SerialNo` bekannt ist, sollte er direkt verwendet werden:

```bash
python3 tools/derive_evo_hdd_password.py \
  --eth 00:11:22:33:44:55 \
  --bt AA:BB:CC:DD:EE:FF \
  --serial-hex 00314132423343344435 \
  --verbose
```

## Eingebauter Selbsttest

```bash
python3 tools/derive_evo_hdd_password.py --self-test
```

Erwartete Ausgabe:

```text
SELF_TEST_PASS
```

Der Testvektor ist vollständig synthetisch und enthält keine Kennungen der Hardware, die für die reale Verifikation verwendet wurde.

## ATA-Security-Status prüfen

Zuerst das physische Laufwerk eindeutig identifizieren:

```bash
lsblk -d -o NAME,MODEL,SERIAL,SIZE,TRAN
```

Danach den Security-Status prüfen:

```bash
sudo hdparm -I /dev/sdX | grep -A10 '^Security:'
```

Eine gesperrte Quelle zeigt typischerweise:

```text
enabled
locked
```

## Kontrollierter Unlock

Erst nachdem das berechnete Passwort unabhängig geprüft wurde:

```bash
sudo hdparm --user-master u \
  --security-unlock 'BERECHNETES_20_ZEICHEN_PASSWORT' \
  /dev/sdX
```

Unmittelbar danach erneut prüfen:

```bash
sudo hdparm -I /dev/sdX | grep -A10 '^Security:'
```

Bei erfolgreichem Unlock wechselt `locked` zu `not locked`, während `enabled` gesetzt bleibt.

## Sicherheit

Auf einer Original-HDD, die erhalten werden soll, **nicht** verwenden:

```text
--security-set-pass
--security-disable
--security-erase
--security-erase-enhanced
```

Passwörter nicht durchprobieren oder bruteforcen. Das Passwort offline berechnen und höchstens einen kontrollierten Unlock-Versuch durchführen. USB-SATA-Bridges können ATA-Security-Kommandos ablehnen, obwohl das Passwort korrekt ist.

Nach erfolgreichem Unlock die Quelle auf Linux-Blockebene read-only setzen und zuerst ein Image erstellen:

```bash
sudo blockdev --setro /dev/sdX
sudo blockdev --getro /dev/sdX
```

Details zur Reverse-Engineering-Beweislage stehen in [`docs/RESEARCH_DE.md`](docs/RESEARCH_DE.md). Der sichere Imaging-Ablauf steht in [`docs/IMAGING_DE.md`](docs/IMAGING_DE.md).

## Zweck

Dieses Repository dokumentiert Interoperabilitätsforschung an rechtmäßig erhaltener Hardware/Software. Es ist kein offizielles Projekt von BMW, Harman, Toshiba oder Google.
