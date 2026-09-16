# BMW NBT EVO HDD password derivation

[English](README.md) | [Deutsch](README_DE.md)

Research notes and a small offline tool for deriving the ATA user password used by BMW/Harman NBT EVO hard drives.

This repository intentionally contains **no real vehicle/head-unit identifiers, no real MAC addresses, no real serial numbers, no real sticker contents, and no real recovered password**. All examples are synthetic.

## What was recovered

For the analyzed BMW/Harman `srv-hddmgr2` build, the ATA user password is derived as:

```text
payload = ETH_MAC_raw_6_bytes
       || BT_MAC_raw_6_bytes
       || E2P.ProdLogistic.SerialNo_raw_bytes

digest = MD5(payload)
password = Base64(digest[0:15])
```

Standard Base64 of exactly 15 bytes produces a 20-character ASCII password with no `=` padding.

## Which sticker value is used?

Do **not** use the 7-digit `SNR:` field directly.

The security routine uses `E2P.ProdLogistic.SerialNo` as raw bytes. On the 2018 NBT EVO unit used for hardware validation, the working 10-byte serial value could be reconstructed from the **main barcode line on the HU label** as:

```text
serial_raw = 0x00 || ASCII(last 9 characters of the main barcode)
```

The important field selection is therefore:

```text
HU label
  main barcode  ---> take the LAST 9 characters
  SNR:          ---> do NOT use directly
  CRIN:         ---> not used by the verified reconstruction
```

If a *synthetic* sticker barcode were:

```text
ABCDE1A2B3C4D5
```

then:

```text
last 9 barcode characters = 1A2B3C4D5
ASCII bytes                = 31 41 32 42 33 43 34 44 35
prefix                     = 00
serial raw                 = 00 31 41 32 42 33 43 34 44 35
serial hex                 = 00314132423343344435
```

So the steps are:

1. Read the Ethernet MAC from the HU label.
2. Read the Bluetooth MAC from the HU label.
3. Read the **main barcode** from the HU label.
4. Take the **last 9 characters** of that main barcode.
5. Encode those 9 characters as ASCII bytes.
6. Prefix one zero byte (`0x00`).
7. Concatenate `ETH raw || BT raw || serial raw`.
8. Calculate MD5.
9. Take only the first 15 MD5 bytes.
10. Encode those 15 bytes using standard Base64.

If the exact diagnostic value of `E2P.ProdLogistic.SerialNo` is available, prefer that exact value over sticker inference.

> **Scope note:** the barcode-to-serial mapping `0x00 + ASCII(last 9 main-barcode characters)` was empirically verified on one 2018 NBT EVO. It should not yet be assumed universal for every EVO hardware revision, production period, or market.

## Synthetic example

```text
Ethernet MAC  = 00:11:22:33:44:55
Bluetooth MAC = AA:BB:CC:DD:EE:FF
Main barcode  = ABCDE1A2B3C4D5
```

Derived serial:

```text
last 9 characters = 1A2B3C4D5
serial hex         = 00314132423343344435
```

Run:

```bash
python3 tools/derive_evo_hdd_password.py \
  --eth 00:11:22:33:44:55 \
  --bt AA:BB:CC:DD:EE:FF \
  --label-barcode ABCDE1A2B3C4D5 \
  --verbose
```

For this synthetic example the output password is:

```text
hAR5JcWED+Zf31RoQgHF
```

## Preferred method: exact E2P serial

If you already have the exact hexadecimal value of `E2P.ProdLogistic.SerialNo`, use it directly:

```bash
python3 tools/derive_evo_hdd_password.py \
  --eth 00:11:22:33:44:55 \
  --bt AA:BB:CC:DD:EE:FF \
  --serial-hex 00314132423343344435 \
  --verbose
```

## Built-in self-test

```bash
python3 tools/derive_evo_hdd_password.py --self-test
```

Expected:

```text
SELF_TEST_PASS
```

The test vector is synthetic and contains no identifiers from the hardware used during validation.

## Checking ATA security state

Identify the physical disk first:

```bash
lsblk -d -o NAME,MODEL,SERIAL,SIZE,TRAN
```

Then inspect the security state:

```bash
sudo hdparm -I /dev/sdX | grep -A10 '^Security:'
```

A locked source disk typically reports:

```text
enabled
locked
```

## Controlled unlock

Only after independently verifying the derived password:

```bash
sudo hdparm --user-master u \
  --security-unlock 'DERIVED_20_CHARACTER_PASSWORD' \
  /dev/sdX
```

Immediately verify again:

```bash
sudo hdparm -I /dev/sdX | grep -A10 '^Security:'
```

A successful unlock changes `locked` to `not locked` while `enabled` remains set.

## Safety

On an original disk intended for preservation, do **not** use:

```text
--security-set-pass
--security-disable
--security-erase
--security-erase-enhanced
```

Do not brute-force candidate passwords. Derive the password offline and use a single controlled unlock attempt. USB/SATA bridges may reject ATA security commands even when the password is correct.

After a successful unlock, make the source block device read-only and image it before doing further work:

```bash
sudo blockdev --setro /dev/sdX
sudo blockdev --getro /dev/sdX
```

See [`docs/RESEARCH.md`](docs/RESEARCH.md) for the reverse-engineering evidence and [`docs/IMAGING.md`](docs/IMAGING.md) for a preservation-oriented imaging workflow.

German versions: [`README_DE.md`](README_DE.md), [`docs/RESEARCH_DE.md`](docs/RESEARCH_DE.md), [`docs/IMAGING_DE.md`](docs/IMAGING_DE.md).

## Scope

This repository documents interoperability research on legitimately obtained hardware/software. It is not an official BMW, Harman, Toshiba, or Google project.
