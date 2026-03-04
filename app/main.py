import sys
import os
from pathlib import Path
import zlib
import hashlib


#write tree function for recursion in directory and create data to write in file
def write_tree():
        with os.scandir('.') as elements:
            for ele in elements:
                if ele.is_file():
                    nam ,ext = os.path.splitext(ele.name)
                    print(nam,"file",ext)
                else:
                    print(ele.name , "is dir")

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
            os.mkdir(f'.git/objects/{p[:2]}')
            #writes zlib compressed binary data
            with open(f'.git/objects/{p[:2]}/{p[2:]}','xb') as m:
                m.write(zlib.compress(data))
                m.close()
            print(p)
            f.close()
    
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
    else:
        raise RuntimeError(f"Unknown command #{command}")


if __name__ == "__main__":
    main()
