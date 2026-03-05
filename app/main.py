import sys
import os
from pathlib import Path
import zlib
import hashlib
from datetime import datetime,timezone
from urllib import request



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
        print(response.read())
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

if __name__ == "__main__":
    main()
