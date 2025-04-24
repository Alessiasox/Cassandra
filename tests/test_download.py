# fetch_first_lores.py

import os
import paramiko

# Configuration
HOST        = "100.76.133.15"              # tailscale IP
PORT        = 22
USERNAME    = "User"                       # the Windows account
KEY_PATH    = os.path.expanduser("~/.ssh/id_ed25519")
REMOTE_BASE = "C:/htdocs/VLF/LoRes"        # forward‑slashes work over SFTP
LOCAL_DIR   = "VLF/LoRes_test"             # where to save the picture

# Connect & SFTP
key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, PORT, USERNAME, pkey=key)

sftp = client.open_sftp()
try:
    # list and filter only jpg files
    files = [f for f in sftp.listdir(REMOTE_BASE) if f.lower().endswith(".jpg")]
    if not files:
        print("No .jpg files found in", REMOTE_BASE)
    else:
        first = sorted(files)[0]
        remote_path = REMOTE_BASE + "/" + first

        os.makedirs(LOCAL_DIR, exist_ok=True)
        local_path = os.path.join(LOCAL_DIR, first)

        print(f"⏬ Downloading {remote_path!r} → {local_path!r} ...")
        sftp.get(remote_path, local_path)
        print("Done.")

finally:
    sftp.close()
    client.close()