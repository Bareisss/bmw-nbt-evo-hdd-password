# Reverse-engineering notes

[English](RESEARCH.md) | [Deutsch](RESEARCH_DE.md)

## Analyzed component

The derivation was recovered from BMW/Harman `srv-hddmgr2` build 4, an ARM/QNX executable responsible for HDD management and HDD security.

The analyzed binary exposed strings and code paths associated with:

```text
CHddSecurityServiceImpl
requestSetPassword
requestSetPasswordExplicit
doProcedureHddUnlock
doProcedureHddLock
doProcedureHddPasswordRecovery
HddSecurityLib.cpp
```

No original binary is redistributed by this repository.

## Input construction

The password helper constructs one contiguous buffer in this order:

```text
6 raw Ethernet-MAC bytes
6 raw Bluetooth-MAC bytes
raw E2P.ProdLogistic.SerialNo bytes
```

The MAC addresses are binary bytes, not their colon-separated ASCII representation.

## Serial parsing

The security serial is supplied as hexadecimal text and decoded two hex characters per byte before password generation.

That means:

```text
00314132423343344435
```

is interpreted as:

```text
00 31 41 32 42 33 43 34 44 35
```

not as the ASCII characters `0`, `0`, `3`, `1`, ...

## Hash and encoding

The implementation contains the standard MD5 initialization state and round constants. The final 16-byte MD5 digest is produced normally.

Only the first 15 digest bytes are then passed to a standard Base64 encoder using:

```text
ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/
```

Hence:

```text
password = Base64(MD5(ETH || BT || serial)[0:15])
```

## Sticker mapping observed during validation

On the single 2018 NBT EVO used for hardware validation, the exact security serial could be reconstructed from the **main barcode** on the HU label as:

```text
serial_raw = 0x00 || ASCII(last 9 characters of main barcode)
```

The 7-digit `SNR:` field was not the value used directly by the HDD password routine. The `CRIN:` line was also not used by the verified reconstruction; the relevant source was the main barcode line and its last 9 characters.

This public repository intentionally omits the real sticker contents, real MAC addresses, and real derived password used during that validation.

## Confidence

Confirmed by code analysis and a successful physical ATA unlock:

```text
input order       = ETH raw || BT raw || serial raw
ETH length        = 6 bytes
BT length         = 6 bytes
hash              = MD5
Base64 input      = first 15 MD5 bytes
Base64 alphabet   = standard
password length   = 20 ASCII characters
```

Still limited in scope:

```text
The label mapping 0x00 + ASCII(last 9 main-barcode chars)
was verified on one 2018 unit and is not claimed universal.
```

When possible, prefer the exact diagnostic `E2P.ProdLogistic.SerialNo` value over label inference.
