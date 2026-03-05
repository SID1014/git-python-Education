import sys
import os
from pathlib import Path
import zlib
import hashlib
from datetime import datetime,timezone
from urllib import request
import struct



#write tree function for recursion in directory and create data to write in file
Author = "Sid_is_sleeping"
email = "siddhantdakhore147@gmail.com"
now = datetime.now(timezone.utc).astimezone()
timestamp = int(now.timestamp())
timezone = now.strftime('%z')

def main():
    # You can use print statements as follows for debugging, they'll be visible when running tests.
    print("Logs from your program will appear here!", file=sys.stderr)

   
    
    command = sys.argv[1]
    if command == "init":
        os.mkdir(".git")
        os.mkdir(".git/objects")
        os.mkdir(".git/refs")
        with open(".git/HEAD", "w") as f:
            f.write("ref: refs/heads/main\n")
        print("Initialized git directory")
    
    elif command == "cat-file" and sys.argv[2] == '-p':
        
        filename = sys.argv[3]
        
        with open(f'.git/objects/{filename[:2]}/{filename[2:]}' , 'rb') as f:
            #decompress file and remove the header
            blob = zlib.decompress(f.read()).split(b'\x00')[1]
            #decodes the file so additional characters do not appear in output
            print(blob.decode('utf-8'),end="")
            f.close()
            
    elif command == "hash-object" and sys.argv[2] == '-w':
        filename = sys.argv[3]
        print(blob_creation(filename))
    
    elif command == "ls-tree" and sys.argv[2] == '--name-only':
        filename = sys.argv[3]
        with open(f'.git/objects/{filename[:2]}/{filename[2:]}' , 'rb') as f:
            #decompress file, remove the headers and creates list containg filename followed sha hash
            tree = zlib.decompress(f.read()).split(b' ')[2:]
            result = ""
            for i in tree:
                
                #seprates hash
                ele = i.split(b'\x00')[0]
                #add new line
                ele = ele.decode('utf-8') + '\n'
                result += ele
            
            print(result,end="")
    elif command == "write-tree":
        data = write_tree()
        print(data)
    elif command == "commit-tree" and sys.argv[-2] == "-m":
        mesage = sys.argv[-1]
        parent_sha = sys.argv[4]
        commit_sha = sys.argv[2]
        content = f"tree {commit_sha}\nparent {parent_sha}\nauthor {Author} <{email}> {timestamp} {timezone}\ncommiter {Author} <{email}> {timestamp} {timezone}\n\n{mesage}\n"
        content = f"commit {len(content)}\0{content}".encode('utf-8')
        # print(content)
        hash = hashlib.sha1()
        hash.update(content)
        #hexaganol number of hash
        p = hash.hexdigest()
        d = f'.git/objects/{p[:2]}'
        if not Path(d).exists():
            os.mkdir(d)
        #writes zlib compressed binary data
        with open(f'.git/objects/{p[:2]}/{p[2:]}','wb') as m:
            m.write(zlib.compress(content))
            m.close()
        print(p)
    elif command == "clone":
        url = sys.argv[2]
        working_dir = sys.argv[3]
        clone(url, working_dir)    
    else:
        raise RuntimeError(f"Unknown command #{command}")

def blob_creation(filename):
        with open(f"{filename}",'rb') as f:
            data = f.read()
            #adds header
            data = bytes(f"blob {len(data)}\x00",encoding = 'utf-8') + data
            #calculate hash
            hash = hashlib.sha1()
            hash.update(data)
            #hexaganol number of hash
            p = hash.hexdigest()
            #create directory for storing file
            d = f'.git/objects/{p[:2]}'
            if not Path(d).exists():
                os.mkdir(d)
            #writes zlib compressed binary data
            with open(f'.git/objects/{p[:2]}/{p[2:]}','xb') as m:
                m.write(zlib.compress(data))
                m.close()
            
            f.close()
            return p

def write_tree(dir='.'):
        result = []
        with os.scandir(dir) as elements:
            for ele in elements:
                if ele.name == ".git":
                    continue
                elif ele.is_file():
                    nam  = ele.name
                    result.append([ '100644' ,nam ,blob_creation(filename= os.path.join(dir,nam) , )])
                else:
                    result.append(['40000',ele.name,write_tree(os.path.join(dir,ele.name))])
            result.sort(key = lambda x :x[1])
            return tree_creation(result)


def parse_pkt_line(data):
    offset = 0
    while offset < len(data):
        # 1. Read the 4-character hex length
        line_len_hex = data[offset:offset+4].decode('ascii')
        line_len = int(line_len_hex, 16)
        
        # 2. Handle the Flush Packet (0000)
        if line_len == 0:
            yield None
            offset += 4
            continue
            
        # 3. Extract the actual data (excluding the 4 length bytes)
        line_data = data[offset+4 : offset+line_len]
        yield line_data
        
        # 4. Move to the next packet
        offset += line_len
    return offset
                    
def tree_creation(results):
    
    data = b""
    for i in results:
        stage = f"{i[0]} {i[1]}\x00"
        data += bytes(stage,encoding = 'utf-8') + bytes.fromhex(f"{i[2]}")
        
    size = len(data)
    data = bytes(f"tree {size}\x00",encoding = 'utf-8') + data
    hash = hashlib.sha1()
    hash.update(data)
    #hexaganol number of hash
    p = hash.hexdigest()
        
        
    #create directory for storing file
    d = f'.git/objects/{p[:2]}'
    if not Path(d).exists():
        os.mkdir(d)

            
        #writes zlib compressed binary data
    with open(f'.git/objects/{p[:2]}/{p[2:]}','xb') as m:
        m.write(zlib.compress(data))
        m.close()
    return p

def clone_negotiation(repo_url, sha1):
    upload_pack_url = f"{repo_url}/git-upload-pack"
    want_line = f"want {sha1}\n"
    line_len = len(want_line) + 4
    pkt_want = f"{line_len:04x}{want_line}".encode('ascii')
    
    pkt_flush = b"0000"
    pkt_done = b"0009done\n"
    
    body = pkt_want + pkt_flush + pkt_done
    req = request.Request(
        upload_pack_url, 
        data=body, 
        headers={'Content-Type': 'application/x-git-upload-pack-request'}
    )
    
    with request.urlopen(req) as response:
        packfile_data = response.read()
        return packfile_data

def clone(url, working_dir):
    # --- 1. Setup target directory ---
    os.makedirs(working_dir, exist_ok=True)
    os.chdir(working_dir)
    os.makedirs(".git/objects", exist_ok=True)
    os.makedirs(".git/refs/heads", exist_ok=True)
    with open(".git/HEAD", "w") as f:
        f.write("ref: refs/heads/main\n")

    # --- 2. Discover refs ---
    repo = request.urlopen(url + "/info/refs?service=git-upload-pack")
    response = repo.read()

    refs = {}
    head_sha = None
    for line in parse_pkt_line(response):
        if line is None: continue
        if b'#' in line: continue

        parts = line.split(b'\0')
        ref_info = parts[0].split(b' ')
        sha = ref_info[0].decode().strip()
        ref = ref_info[1].decode().strip() if len(ref_info) > 1 else None

        if ref:
            refs[ref] = sha
            if ref == "HEAD" or head_sha is None:
                head_sha = sha

    # --- 3. Fetch packfile ---
    packfile = clone_negotiation(url, head_sha)

    # --- 4. Parse and store all objects (with delta resolution) ---
    object_store = parse_packfile(packfile)

    # --- 5. Write branch refs ---
    for ref, sha in refs.items():
        if ref.startswith("refs/"):
            ref_path = f".git/{ref}"
            os.makedirs(os.path.dirname(ref_path), exist_ok=True)
            with open(ref_path, "w") as f:
                f.write(sha + "\n")

    # --- 6. Checkout HEAD into working directory ---
    checkout(head_sha)
    print(f"Cloned {url} into {working_dir}")


def resolve_delta(base_content, delta_data):
    """Apply a Git delta to a base object."""
    idx = 0

    def read_varint():
        nonlocal idx
        result, shift = 0, 0
        while True:
            byte = delta_data[idx]; idx += 1
            result |= (byte & 0x7F) << shift
            shift += 7
            if not (byte & 0x80): break
        return result

    base_len = read_varint()
    result_len = read_varint()
    result = b""

    while idx < len(delta_data):
        cmd = delta_data[idx]; idx += 1
        if cmd & 0x80:  # Copy from base
            cp_off, cp_size = 0, 0
            if cmd & 0x01: cp_off   |= delta_data[idx] << 0;  idx += 1
            if cmd & 0x02: cp_off   |= delta_data[idx] << 8;  idx += 1
            if cmd & 0x04: cp_off   |= delta_data[idx] << 16; idx += 1
            if cmd & 0x08: cp_off   |= delta_data[idx] << 24; idx += 1
            if cmd & 0x10: cp_size  |= delta_data[idx] << 0;  idx += 1
            if cmd & 0x20: cp_size  |= delta_data[idx] << 8;  idx += 1
            if cmd & 0x40: cp_size  |= delta_data[idx] << 16; idx += 1
            if cp_size == 0: cp_size = 0x10000
            result += base_content[cp_off:cp_off + cp_size]
        elif cmd:  # Insert literal bytes
            result += delta_data[idx:idx + cmd]; idx += cmd
        else:
            raise ValueError("Unexpected delta command 0x00")

    return result


def parse_packfile(data):
    if data[:8] == b'0008NAK\n':
        data = data[8:]

    assert data[:4] == b'PACK', "Not a valid packfile"
    num_objects = struct.unpack('>I', data[8:12])[0]
    offset = 12

    types = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}
    # Store raw content keyed by sha for delta resolution
    object_store = {}
    # Deferred deltas: (type_id, base_sha_or_offset, raw_delta_content)
    deferred_deltas = []

    for i in range(num_objects):
        obj_start = offset

        # Parse variable-length header
        first_byte = data[offset]
        obj_type_id = (first_byte & 0x70) >> 4
        size = first_byte & 0x0F
        shift = 4
        offset += 1

        while data[offset - 1] & 0x80:
            byte = data[offset]
            size |= (byte & 0x7F) << shift
            shift += 7
            offset += 1

        base_sha = None
        base_offset = None

        if obj_type_id == 7:  # REF_DELTA
            base_sha = data[offset:offset + 20].hex()
            offset += 20
        elif obj_type_id == 6:  # OFS_DELTA
            raw = 0
            while data[offset] & 0x80:
                raw = (raw << 7) | (data[offset] & 0x7F)
                offset += 1
            raw = (raw << 7) | data[offset]
            offset += 1
            base_offset = obj_start - raw

        # Decompress
        decompressor = zlib.decompressobj()
        content = decompressor.decompress(data[offset:])
        offset += len(data[offset:]) - len(decompressor.unused_data)

        if obj_type_id in (6, 7):
            deferred_deltas.append((obj_type_id, base_sha or base_offset, content, obj_start))
            continue

        # Store and write base objects
        obj_type = types[obj_type_id]
        _store_object(obj_type, content, object_store)

    # --- Resolve deltas ---
    # Retry loop handles deltas whose base is itself a delta
    max_passes = 10
    for _ in range(max_passes):
        if not deferred_deltas: break
        unresolved = []
        for type_id, base_ref, delta_content, obj_start in deferred_deltas:
            if type_id == 7:
                base = object_store.get(base_ref)
            else:
                base = object_store.get(f"@{base_ref}")  # offset-keyed

            if base is None:
                unresolved.append((type_id, base_ref, delta_content, obj_start))
                continue

            base_type, base_content = base
            result = resolve_delta(base_content, delta_content)
            _store_object(base_type, result, object_store)

        deferred_deltas = unresolved

    if deferred_deltas:
        print(f"Warning: {len(deferred_deltas)} delta(s) could not be resolved")

    return object_store


def _store_object(obj_type, content, object_store):
    header = f"{obj_type} {len(content)}".encode() + b'\x00'
    full_object = header + content
    sha1 = hashlib.sha1(full_object).hexdigest()

    obj_dir = f".git/objects/{sha1[:2]}"
    os.makedirs(obj_dir, exist_ok=True)
    obj_path = f"{obj_dir}/{sha1[2:]}"
    if not os.path.exists(obj_path):
        with open(obj_path, "wb") as f:
            f.write(zlib.compress(full_object))

    object_store[sha1] = (obj_type, content)
    return sha1


def checkout(commit_sha, base_dir='.'):
    """Recursively checkout a commit's tree into the working directory."""
    # Read commit to get tree sha
    commit_type, commit_content = read_object(commit_sha)
    tree_sha = commit_content.split(b'\n')[0].split(b' ')[1].decode()
    checkout_tree(tree_sha, base_dir)


def checkout_tree(tree_sha, base_dir):
    _, tree_content = read_object(tree_sha)
    idx = 0
    while idx < len(tree_content):
        # Parse "mode name\0<20-byte-sha>"
        null = tree_content.index(b'\x00', idx)
        mode, name = tree_content[idx:null].decode().split(' ', 1)
        sha = tree_content[null + 1:null + 21].hex()
        idx = null + 21

        path = os.path.join(base_dir, name)
        if mode == '40000':  # directory
            os.makedirs(path, exist_ok=True)
            checkout_tree(sha, path)
        else:  # file
            _, file_content = read_object(sha)
            with open(path, 'wb') as f:
                f.write(file_content)


def read_object(sha):
    path = f".git/objects/{sha[:2]}/{sha[2:]}"
    with open(path, 'rb') as f:
        raw = zlib.decompress(f.read())
    header, content = raw.split(b'\x00', 1)
    obj_type = header.split(b' ')[0].decode()
    return obj_type, content        
        
        
if __name__ == "__main__":
    main()
