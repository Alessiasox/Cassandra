# tests/test_fetch_dates.py
#
# Run **only** when you have network + key and the env-vars below.
# Skipped automatically in CI.

import os
from datetime import timezone
import pytest

from ssh.fetcher_remote import RemoteVLFClient


def _skip_unless_env():
    host = os.getenv("VLF_HOST")
    user = os.getenv("VLF_USER")
    if not (host and user):
        pytest.skip(
            "Live remote test skipped: "
            "set VLF_HOST and VLF_USER (and optionally VLF_KEY_PATH).",
            allow_module_level=True
        )
    return host, user, os.getenv("VLF_KEY_PATH", "~/.ssh/id_ed25519")


# ────────────────────────────────────────────────────────────────────────────
host, user, key_path = _skip_unless_env()


@pytest.fixture(scope="module")
def client():
    cli = RemoteVLFClient(
        host        = host,
        port        = 22,
        username    = user,
        key_path    = key_path,
        remote_base = "C:/htdocs/VLF"          # adjust if your layout differs
    )
    yield cli
    cli.close()


def test_live_lores_date_range(client):
    """
    Real SSH hit: list LoRes frames and check earliest / latest dates.
    """
    lores = client.list_images("LoRes")
    assert lores, "No LoRes images returned"

    first = lores[0]["timestamp"].astimezone(timezone.utc)
    last  = lores[-1]["timestamp"].astimezone(timezone.utc)

    print(f"\nFound {len(lores)} LoRes frames "
          f"from {first:%Y-%m-%d %H:%M} UTC "
          f"to   {last:%Y-%m-%d %H:%M} UTC")

    assert first.year >= 2020
    assert last   >= first


def test_live_hires_sample_fetch(client, tmp_path):
    """
    Download **one** HiRes frame into a temp file to make sure bytes arrive.
    """
    hires = client.list_images("HiRes")
    assert hires, "No HiRes images returned"

    sample = hires[len(hires)//2]            # pick the middle frame
    raw    = client.fetch_image_bytes(sample["remote_path"])

    # write to disc just so we know the bytes are valid JPEG
    out_file = tmp_path / sample["original_filename"]
    out_file.write_bytes(raw)

    # quick header check: JPEG starts with 0xFFD8, ends with 0xFFD9
    assert raw[:2] == b"\xFF\xD8" and raw[-2:] == b"\xFF\xD9"
    print(f"\nFetched {len(raw)/1024:.1f} kB from {sample['remote_path']}")