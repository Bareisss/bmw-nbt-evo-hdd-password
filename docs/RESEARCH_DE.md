# Reverse-Engineering-Notizen

[English](RESEARCH.md) | [Deutsch](RESEARCH_DE.md)

## Untersuchte Komponente

Die Herleitung wurde aus BMW/Harman `srv-hddmgr2` Build 4 rekonstruiert. Dabei handelt es sich um eine ARM/QNX-Anwendung, die unter anderem HDD-Verwaltung und HDD-Security übernimmt.

Im analysierten Binary finden sich unter anderem Strings und Codepfade zu:

```text
CHddSecurityServiceImpl
requestSetPassword
requestSetPasswordExplicit
doProcedureHddUnlock
doProcedureHddLock
doProcedureHddPasswordRecovery
HddSecurityLib.cpp
```

Das originale Binary wird in diesem Repository nicht weitergegeben.

## Aufbau des Eingabepuffers

Die Passwort-Routine erzeugt einen zusammenhängenden Bytepuffer in dieser Reihenfolge:

```text
6 rohe Ethernet-MAC-Bytes
6 rohe Bluetooth-MAC-Bytes
rohe E2P.ProdLogistic.SerialNo-Bytes
```

Die MAC-Adressen werden als Binärbytes verwendet, nicht als ASCII-Text mit Doppelpunkten.

## Parsing des Serialwerts

Der Security-Serialwert wird als Hextext übergeben und vor der Passwortberechnung paarweise in Bytes dekodiert.

Das bedeutet beispielsweise:

```text
00314132423343344435
```

wird interpretiert als:

```text
00 31 41 32 42 33 43 34 44 35
```

und nicht als die ASCII-Zeichen `0`, `0`, `3`, `1`, ...

## Hash und Kodierung

Die Implementierung enthält den standardmäßigen MD5-Initialzustand und die üblichen MD5-Rundenkonstanten. Der 16-Byte-MD5-Digest wird normal erzeugt.

Anschließend werden nur die ersten 15 Digest-Bytes an einen Standard-Base64-Encoder übergeben. Verwendet wird das Alphabet:

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
```

Damit ergibt sich:

```text
password = Base64(MD5(ETH || BT || serial)[0:15])
```

## Aufkleber-Zuordnung aus der Hardware-Verifikation

Bei der einzelnen 2018er NBT-EVO-HU, die für die physische Verifikation verwendet wurde, ließ sich der Security-Serialwert aus dem **Haupt-Barcode** auf dem HU-Aufkleber rekonstruieren:

```text
serial_raw = 0x00 || ASCII(letzte 9 Zeichen des Haupt-Barcodes)
```

Die 7-stellige `SNR:` wurde dabei nicht direkt von der HDD-Passwort-Routine verwendet.

Auch die `CRIN:`-Zeile wurde für diese verifizierte Rekonstruktion nicht verwendet. Entscheidend war die Haupt-Barcodezeile und deren letzte 9 Zeichen.

Dieses öffentliche Repository enthält absichtlich weder die echten Aufkleberdaten noch die realen MAC-Adressen oder das reale abgeleitete Passwort aus der Hardware-Verifikation.

## Vertrauensniveau

Durch Codeanalyse und einen erfolgreichen physischen ATA-Unlock bestätigt:

```text
Reihenfolge Input = ETH raw || BT raw || serial raw
ETH-Länge         = 6 Bytes
BT-Länge          = 6 Bytes
Hash              = MD5
Base64-Input      = erste 15 MD5-Bytes
Base64-Alphabet   = Standard
Passwortlänge     = 20 ASCII-Zeichen
```

Noch nicht allgemein bewiesen:

```text
Die Label-Zuordnung 0x00 + ASCII(letzte 9 Zeichen des Haupt-Barcodes)
wurde an einer 2018er Einheit verifiziert und wird nicht als universell behauptet.
```

Wenn `E2P.ProdLogistic.SerialNo` diagnostisch direkt gelesen werden kann, ist dieser exakte Wert immer vorzuziehen.
