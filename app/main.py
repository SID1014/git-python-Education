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
        repo = request.urlopen(url+"/info/refs?service=git-upload-pack")
        response = repo.read()
        for line in parse_pkt_line(response):
            if line is None: continue # Skip flush
            if b'#' in line: continue # Skip service header
            
            parts = line.split(b'\0')
            ref_info = parts[0].split(b' ')
            sha1 = ref_info[0].decode()
            ref_name = ref_info[1].decode()
            
            # print(f"Found Ref: {ref_name} -> {sha1}")
            if len(parts) > 1:
                capabilities = parts[1].decode().split(' ')
        response = clone_negotiation(url,sha1)
        print(parse_packfile(response))
        
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

def parse_packfile(data):
    # Strip HTTP smart protocol prefix '0008NAK\n' if present
    if data[:8] == b'0008NAK\n':
        data = data[8:]

    # Validate PACK magic
    assert data[:4] == b'PACK', "Not a valid packfile"

    version = struct.unpack('>I', data[4:8])[0]
    num_objects = struct.unpack('>I', data[8:12])[0]
    offset = 12  # Move past the 12-byte PACK header

    types = {1: "commit", 2: "tree", 3: "blob", 4: "tag"}

    print(f"PACK version={version}, objects={num_objects}")

    for i in range(num_objects):
        # --- 1. Parse variable-length header ---
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

        # --- 2. Handle delta types ---
        if obj_type_id == 7:  # REF_DELTA: skip 20-byte base object SHA
            base_sha = data[offset:offset + 20].hex()
            offset += 20
            print(f"  REF_DELTA base sha: {base_sha} (skipping delta resolution)")

        elif obj_type_id == 6:  # OFS_DELTA: skip variable-length negative offset
            while data[offset] & 0x80:
                offset += 1
            offset += 1
            print(f"  OFS_DELTA (skipping delta resolution)")

        obj_type = types.get(obj_type_id, "unknown")

        # --- 3. Decompress zlib data ---
        try:
            decompressor = zlib.decompressobj()
            content = decompressor.decompress(data[offset:])
            consumed = len(data[offset:]) - len(decompressor.unused_data)
            offset += consumed

        except zlib.error as e:
            print(f"[!] zlib failed at offset {offset} (object {i}, type={obj_type_id})")
            print(f"    Bytes: {data[offset:offset+10].hex()}")
            raise e

        # --- 4. Skip delta objects (can't store without base resolution) ---
        if obj_type_id in (6, 7):
            print(f"  Skipping delta object storage (requires base resolution)")
            continue

        # --- 5. Compute SHA-1 and write to .git/objects ---
        header = f"{obj_type} {len(content)}".encode() + b'\x00'
        full_object = header + content
        sha1 = hashlib.sha1(full_object).hexdigest()

        obj_dir = f".git/objects/{sha1[:2]}"
        os.makedirs(obj_dir, exist_ok=True)

        obj_path = f"{obj_dir}/{sha1[2:]}"
        if not os.path.exists(obj_path):
            with open(obj_path, "wb") as f:
                f.write(zlib.compress(full_object))

        # print(f"[{i+1}/{num_objects}] Stored {obj_type}: {sha1}")
        
        
        
if __name__ == "__main__":
    main()
