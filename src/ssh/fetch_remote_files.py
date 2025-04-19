import paramiko
import os
from datetime import datetime

# This is obv wrong, I need an env file, this is just for testing
HOST_DURONIA  = "100.76.133.15"
PORT       = 22
USERNAME   = "User"
KEY_PATH   = os.path.expanduser("~/.ssh/id_ed25519")
REMOTE_BASE = "C:/htdocs/VLF"
LOCAL_BASE  = "/Users/alessiasollo/Desktop/Cassandra/VLF"

def fetch_remote_folder(sftp, remote_dir, local_dir):
    os.makedirs(local_dir, exist_ok=True)
    for entry in sftp.listdir_attr(remote_dir):
        remote_path = remote_dir + "/" + entry.filename
        local_path  = os.path.join(local_dir, entry.filename)
        if entry.st_mode & 0o40000:  # directory
            fetch_remote_folder(sftp, remote_path, os.path.join(local_dir, entry.filename))
        else:
            # only download if newer (optional)
            remote_mtime = datetime.fromtimestamp(entry.st_mtime)
            if (not os.path.exists(local_path) or
                remote_mtime > datetime.fromtimestamp(os.path.getmtime(local_path))):
                print(f"Downloading {remote_path} → {local_path}")
                sftp.get(remote_path, local_path)

def main():
    # set up key‑based SSH client
    key = paramiko.Ed25519Key.from_private_key_file(KEY_PATH)
    client = paramiko.SSHClient()
    client.set_missing_HOST_DURONIA_key_policy(paramiko.AutoAddPolicy())
    client.connect(HOST_DURONIA, PORT, USERNAME, pkey=key)
    
    # open SFTP session
    with client.open_sftp() as sftp:
        # fetch both LoRes and HiRes
        fetch_remote_folder(sftp,
                            f"{REMOTE_BASE}/LoRes",
                            os.path.join(LOCAL_BASE, "LoRes"))
        fetch_remote_folder(sftp,
                            f"{REMOTE_BASE}/HiRes",
                            os.path.join(LOCAL_BASE, "HiRes"))
        # (and Wav)
        fetch_remote_folder(sftp,
                            f"{REMOTE_BASE}/Wav",
                            os.path.join(LOCAL_BASE, "Wav"))
    
    client.close()

if __name__ == "__main__":
    main()