#!/usr/bin/env python3
"""Derive a BMW NBT EVO ATA user password from HU identity data.

Algorithm recovered from BMW/Harman srv-hddmgr2:
    payload  = ETH_MAC[6] || BT_MAC[6] || serial_raw
    digest   = MD5(payload)
    password = Base64(digest[:15])

This public tool contains only synthetic examples.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import re
import sys

HEX_RE = re.compile(r"^[0-9A-Fa-f]+$")


def parse_mac(value: str, label: str) -> bytes:
    compact = re.sub(r"[:-]", "", value.strip())
    if len(compact) != 12 or not HEX_RE.fullmatch(compact):
        raise ValueError(f"{label} must contain exactly 12 hex digits")
    return bytes.fromhex(compact)


def parse_serial_hex(value: str) -> bytes:
    compact = re.sub(r"[\s:_-]", "", value.strip())
    if not compact or len(compact) % 2 or not HEX_RE.fullmatch(compact):
        raise ValueError("serial hex must contain an even, non-zero number of hex digits")
    return bytes.fromhex(compact)


def serial_from_label_barcode(barcode: str) -> bytes:
    """Observed mapping: 0x00 + ASCII(last 9 chars of main barcode).

    Verified on one 2018 NBT EVO. Prefer --serial-hex when the exact
    E2P.ProdLogistic.SerialNo value is available.
    """
    value = barcode.strip()
    if len(value) < 9:
        raise ValueError("barcode must contain at least 9 characters")
    tail = value[-9:]
    try:
        return b"\x00" + tail.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError("last 9 barcode characters must be ASCII") from exc


def derive(eth: bytes, bt: bytes, serial: bytes) -> tuple[bytes, bytes, str]:
    payload = eth + bt + serial
    digest = hashlib.md5(payload).digest()
    password = base64.b64encode(digest[:15]).decode("ascii")
    return payload, digest, password


def self_test() -> None:
    eth = bytes.fromhex("001122334455")
    bt = bytes.fromhex("AABBCCDDEEFF")
    serial = bytes.fromhex("00314132423343344435")
    payload, digest, password = derive(eth, bt, serial)
    assert payload.hex().upper() == "001122334455AABBCCDDEEFF00314132423343344435"
    assert digest.hex() == "84047925c5840fe65fdf54684201c515"
    assert password == "hAR5JcWED+Zf31RoQgHF"
    print("SELF_TEST_PASS")


def main() -> int:
    p = argparse.ArgumentParser(description="Derive BMW NBT EVO ATA user password")
    p.add_argument("--eth")
    p.add_argument("--bt")
    group = p.add_mutually_exclusive_group()
    group.add_argument("--serial-hex", help="exact E2P.ProdLogistic.SerialNo hex value")
    group.add_argument("--label-barcode", help="main sticker barcode; uses last 9 chars")
    p.add_argument("--verbose", action="store_true")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args()

    if args.self_test:
        self_test()
        if not args.eth and not args.bt and not args.serial_hex and not args.label_barcode:
            return 0

    if not args.eth or not args.bt or not (args.serial_hex or args.label_barcode):
        p.error("--eth, --bt and one serial source are required")

    try:
        eth = parse_mac(args.eth, "ETH MAC")
        bt = parse_mac(args.bt, "BT MAC")
        if args.serial_hex:
            serial = parse_serial_hex(args.serial_hex)
            source = "explicit E2P serial hex"
        else:
            serial = serial_from_label_barcode(args.label_barcode)
            source = "0x00 + ASCII(last 9 main-barcode chars)"
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    payload, digest, password = derive(eth, bt, serial)

    if args.verbose:
        print(f"ETH_BYTES     = {eth.hex().upper()}")
        print(f"BT_BYTES      = {bt.hex().upper()}")
        print(f"SERIAL_SOURCE = {source}")
        print(f"SERIAL_BYTES  = {serial.hex().upper()}")
        if serial[:1] == b"\x00":
            try:
                print(f"SERIAL_ASCII  = {serial[1:].decode('ascii')!r}")
            except UnicodeDecodeError:
                pass
        print(f"MD5_INPUT     = {payload.hex().upper()}")
        print(f"MD5           = {digest.hex()}")
        print(f"MD5_FIRST_15  = {digest[:15].hex()}")

    print(f"PASSWORD      = {password}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
