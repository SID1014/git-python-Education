import sys
import os
import zlib
import hashlib

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
            
    elif command == "hash-object" and sys.argv[2] == '-w':
        filename = sys.argv[3]
        with open(f"{filename}",'rb') as f:
            data = f.read()
            data = bytes(f"blob {len(data)}\x00",encoding = 'utf-8') + data
            hash = hashlib.sha1()
            hash.update(data)
            p = hash.hexdigest()
            os.mkdir(f'.git/objects/{p[:2]}')
            with open(f'.git/objects/{p[:2]}/{p[2:]}','x') as m:
                m.write(str(zlib.compress(data)))
                m.close()
            
            
            print(p)
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
