# src/ssh/fetcher_remote.py

from __future__ import annotations

import io
import os
from datetime import datetime, timezone
from typing import Dict, List

import paramiko
from parser.parse_filenames import parse_filename


class RemoteVLFClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        key_path: str,
        remote_base: str,
    ):
        """
        host         remote SSH host
        port         SSH port (usually 22)
        username     SSH user
        key_path     path to an *Ed25519* private key
        remote_base  root folder on the remote (e.g. ``C:/htdocs/VLF``)
        """
        self._host = host
        self._port = port
        self._username = username
        self._key_path = os.path.expanduser(key_path)
        # always use forward slashes for SFTP paths
        self._remote_base = remote_base.replace("\\", "/")

        self._client: paramiko.SSHClient | None = None
        self._sftp: paramiko.SFTPClient | None = None

    # ------------------------------------------------------------------#
    # connection helpers
    # ------------------------------------------------------------------#
    def connect(self) -> None:
        """Open SSH + SFTP the first time they're needed."""
        if self._client:
            return

        key = paramiko.Ed25519Key.from_private_key_file(self._key_path)

        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=self._host,
            port=self._port,
            username=self._username,
            pkey=key,  # use our key
            allow_agent=True,
            look_for_keys=True,
        )

        self._client = client
        self._sftp = client.open_sftp()

    def close(self) -> None:
        """Close both channels."""
        if self._sftp:
            self._sftp.close()
        if self._client:
            self._client.close()
        self._sftp = self._client = None

    # ------------------------------------------------------------------#
    # images
    # ------------------------------------------------------------------#
    def list_images(self, resolution: str) -> List[Dict]:
        """
        Return metadata dicts for every ``*.jpg`` under
        ``<remote_base>/<resolution>`` (LoRes or HiRes).

        All ``timestamp`` fields are **UTC-aware** ``datetime`` objects.
        """
        self.connect()
        remote_dir = f"{self._remote_base}/{resolution}"
        images: list[Dict] = []

        for entry in self._sftp.listdir_attr(remote_dir):
            if not entry.filename.lower().endswith(".jpg"):
                continue

            # 1) try parsing from the filename
            info = parse_filename(entry.filename)
            if info and info["timestamp"].tzinfo is None:
                info["timestamp"] = info["timestamp"].replace(tzinfo=timezone.utc)

            # 2) if parsing failed, fall back to the mtime
            if info is None:
                info = {
                    "station": "UNKNOWN",
                    "timestamp": datetime.fromtimestamp(
                        entry.st_mtime, tz=timezone.utc
                    ),
                }

            # common additions / overrides
            info["resolution"] = resolution
            info["remote_path"] = f"{remote_dir}/{entry.filename}"
            info["original_filename"] = entry.filename

            images.append(info)

        return sorted(images, key=lambda d: d["timestamp"])

    def fetch_image_bytes(self, remote_path: str) -> bytes:
        """Read a remote image into memory."""
        self.connect()
        buf = io.BytesIO()
        self._sftp.getfo(remote_path, buf)
        return buf.getvalue()

    # ------------------------------------------------------------------#
    # WAV audio
    # ------------------------------------------------------------------#
    def list_wavs(self) -> List[Dict]:
        """
        List every ``*.wav`` under ``<remote_base>/Wav``.

        Returns UTC-aware ``timestamp`` fields.
        """
        self.connect()
        remote_dir = f"{self._remote_base}/Wav"
        wavs: list[Dict] = []

        for entry in self._sftp.listdir_attr(remote_dir):
            if not entry.filename.lower().endswith(".wav"):
                continue

            wavs.append(
                {
                    "remote_path": f"{remote_dir}/{entry.filename}",
                    "filename": entry.filename,
                    "timestamp": datetime.fromtimestamp(
                        entry.st_mtime, tz=timezone.utc
                    ),
                }
            )

        return sorted(wavs, key=lambda x: x["timestamp"])

    def fetch_wav_bytes(self, remote_path: str) -> bytes:
        """Read a remote WAV file into memory."""
        self.connect()
        buf = io.BytesIO()
        self._sftp.getfo(remote_path, buf)
        return buf.getvalue()