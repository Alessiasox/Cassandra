# src/ssh/fetcher_remote.py

import io
import os
import paramiko
from typing import List, Dict
from datetime import datetime
from parser.parse_filenames import parse_filename

class RemoteVLFClient:
    def __init__(
        self,
        host: str,
        port: int,
        username: str,
        key_path: str,
        remote_base: str
    ):
        """
        host        – remote SSH host
        port        – SSH port (usually 22)
        username    – SSH user
        key_path    – path to your private key (Ed25519)
        remote_base – root folder on remote (e.g. C:/htdocs/VLF)
        """
        self._host        = host
        self._port        = port
        self._username    = username
        self._key_path    = os.path.expanduser(key_path)
        # ensure remote paths use forward slashes
        self._remote_base = remote_base.replace("\\", "/")
        self._client      = None
        self._sftp        = None

    def connect(self):
        """Lazily open SSH and SFTP sessions."""
        if self._client:
            return

        # load your private key
        key = paramiko.Ed25519Key.from_private_key_file(self._key_path)

        # set up SSHClient
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # connect, allowing agent fallback
        client.connect(
            hostname      = self._host,
            port          = self._port,
            username      = self._username,
            pkey          = key,            # <-- use our loaded key
            allow_agent   = True,
            look_for_keys = True
        )

        # open SFTP
        self._client = client
        self._sftp   = client.open_sftp()

    def close(self):
        """Cleanly close SFTP and SSH connections."""
        if self._sftp:
            self._sftp.close()
        if self._client:
            self._client.close()
        self._sftp = self._client = None

    def list_images(self, resolution: str) -> List[Dict]:
        """
        List all .jpg files under <remote_base>/<resolution>,
        parse their filenames, and return a list of metadata dicts:

            {
              "station": ...,
              "resolution": resolution,
              "timestamp": datetime(...),
              "remote_path": "C:/htdocs/VLF/HiRes/...",
              "original_filename": "G1_HiResT_250410UTC144040.jpg"
            }
        """
        self.connect()
        remote_dir = f"{self._remote_base}/{resolution}"
        out = []

        for entry in self._sftp.listdir_attr(remote_dir):
            # only .jpg
            if not entry.filename.lower().endswith(".jpg"):
                continue

            # parse out station, timestamp, etc.
            info = parse_filename(entry.filename)
            if not info:
                continue

            # override/add the fields we need
            info["resolution"]     = resolution
            info["remote_path"]    = f"{remote_dir}/{entry.filename}"
            info["original_filename"] = entry.filename
            # overwrite timestamp with the file’s actual mtime
            info["timestamp"]      = datetime.fromtimestamp(entry.st_mtime)

            out.append(info)

        # sort by timestamp ascending
        return sorted(out, key=lambda x: x["timestamp"])

    def fetch_image_bytes(self, remote_path: str) -> bytes:
        """
        Download a remote image into memory and return its raw bytes.
        """
        self.connect()
        buf = io.BytesIO()
        # getfo writes file‐like into buf
        self._sftp.getfo(remote_path, buf)
        return buf.getvalue()

    def list_wavs(self) -> List[Dict]:
        """
        List all .wav files under <remote_base>/Wav,
        returning metadata dicts with 'remote_path', 'filename', and 'timestamp'.
        """
        self.connect()
        remote_dir = f"{self._remote_base}/Wav"
        out = []

        for entry in self._sftp.listdir_attr(remote_dir):
            if not entry.filename.lower().endswith(".wav"):
                continue

            path = f"{remote_dir}/{entry.filename}"
            out.append({
                "remote_path": path,
                "filename":    entry.filename,
                "timestamp":   datetime.fromtimestamp(entry.st_mtime)
            })

        return sorted(out, key=lambda x: x["timestamp"])

    def fetch_wav_bytes(self, remote_path: str) -> bytes:
        """
        Download a remote .wav into memory; return raw bytes.
        """
        self.connect()
        buf = io.BytesIO()
        self._sftp.getfo(remote_path, buf)
        return buf.getvalue()