import sys
import os
from pathlib import Path
import zlib
import hashlib


#write tree function for recursion in directory and create data to write in file


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
        # with open(f"{filename}",'rb') as f:
        #     data = f.read()
        #     #adds header
        #     data = bytes(f"blob {len(data)}\x00",encoding = 'utf-8') + data
        #     #calculate hash
        #     hash = hashlib.sha1()
        #     hash.update(data)
        #     #hexaganol number of hash
        #     p = hash.hexdigest()
        #     #create directory for storing file
        #     os.mkdir(f'.git/objects/{p[:2]}')
        #     #writes zlib compressed binary data
        #     with open(f'.git/objects/{p[:2]}/{p[2:]}','xb') as m:
        #         m.write(zlib.compress(data))
        #         m.close()
        #     print(p)
        #     f.close()
    
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
                if ele.is_file():
                    nam  = ele.name
                    result.append([ '100644' ,nam ,blob_creation(filename= dir+'/'+nam , )])
                elif ele.name == ".git":
                    pass
                else:
                    print(ele.name , "is dir")
                    result.append(['40000',ele.name,write_tree(f"./{ele.name}")])
            return tree_creation(result)
            
def tree_creation(results):
    size = len(results)
    data = bytes(f"tree {size}\x00",encoding = 'utf-8')
    for i in results:
        stage = f"{results[0]} {results[1]}\x00{results[3]}"
        data += bytes(stage)
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

if __name__ == "__main__":
    main()
