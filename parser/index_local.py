import os
from parser.parse_filenames import parse_filename

def index_local_images(directory: str):
    """
    Scans the given directory for .jpg files,
    parses their metadata, and returns a list of parsed info dicts.
    """
    results = []
    for fname in os.listdir(directory):
        print(f"Found file: {fname}")

        if not fname.lower().endswith(".jpg"):
            print(" --> Skipped: not a jpg")
            continue

        parsed = parse_filename(fname)
        if parsed is None:
            print(" --> Skipped: failed to parse")
            continue

        full_path = os.path.join(directory, fname)
        parsed["full_path"] = full_path
        results.append(parsed)
        print(" --> Parsed and added.")
    
    return results

if __name__ == "__main__":
    # For quick testing, specify some local path
    test_dir = "/Users/alessiasollo/Desktop/Cassandra/VLF/LoRes"
    parsed_info_list = index_local_images(test_dir)
    
    # Print some results
    for info in parsed_info_list[:10]:
        print(info)