import logging
import threading
import asyncio
import sys
import os
import time
import random
import re
from ftplib import FTP

class Thread(threading.Thread):
    def __init__(self,target,*args):
        self.target = target
        self.args = args
        self.thread = threading.Thread(target=self.target,args=self.args)

    def start(self):
        self.thread.start()

    def join(self):
        self.thread.join()

logging.basicConfig(filename="log.txt",filemode="w",level=logging.DEBUG,
                    format="%(asctime)s | %(levelname)s: %(message)s",datefmt="%Y/%m/%d %H:%M:%S")
logging.info("Server Started!")
print("Server Started!")

server = "server address here"

ftp = FTP(server,"user","pass")
ftp.cwd("Default directory here")

async def setup():
    with FTP("Server address here") as ftp:
        try:
            ftp.login(user="user",passwd="pass")
        except:
            print("An error occured")
            logging.error("An error occured!")
            logging.error("Shutdown by Setup!")
            sys.exit()

        print("Connection: 200")

        await conhandler(ftp,"","")

        try:
            ftp.quit()
        except:
            ftp.close()

async def conhandler(ftp,lib,path):
    #ftp.set_debuglevel(1)
    if lib == "_home" or path == "":
        ftp.cwd("/")
        path = "/"
    else:
        if lib != "":
            if lib not in ftp.nlst():
                print("Invalid Pathname!")
            else:
                path += "/" + lib
        ftp.cwd(path)

    print(f"\nCurrent path: home{path}")
    print(f"Directory Content:\n")
    print("  Last Modify:\t\t  Format:\tSize:\t   Name:")
    print(f"-".rjust(60,"-"),"\n")
    files = ftp.dir()

    print(f"-".rjust(60, "-"), "\n")
    lib = input("\nInput: ")

    if lib == "_back":
        pos = path.rfind("/")
        path = path[:pos]
        lib = ""

    elif lib == "_exit" or lib == "_esc":
        return

    elif "_mkdir" in lib: # make new directory
        name = lib.split()
        name.pop(0)
        ftp.mkd(" ".join(name))
        print("Directory Created!")
        logging.info(f"Directory created at: {path}")

    elif "_rename" in lib: # Rename
        if "/" not in lib:
            print("Use '/' as seperator")
            lib = ""
        else:
            name = lib.split('/')
            lib = ""
            name.pop(0)
            if name[0] not in ftp.nlst():
                logging.error("Rename: Invalid file/dirname!")
                print("Invalid file/dirname!")
            else:
                re.sub('[^\w\-_\. ]', '_', name[1])
                ftp.rename(name[0],name[1])
                print(f"Renamed {name[0]} to {name[1]} in {path}")
                logging.info(f"Renamed {name[0]} to {name[1]} in {path}")

    elif "_del" in lib:   #Delete folder or file
        if "/" not in lib:
            print("Use '/' as seperator")
            lib = ""
        else:
            name = lib.split('/')
            name.pop(0)
            for n in name:
                x = input("Are you sure you want to delete: " + n + " \ninput: ")
                if x == "yes" or x == "y" or x == "Yes":
                    if "." not in n:
                        try:
                            ftp.rmd(n)
                        except:
                            print("Error: Directory not found!")
                            logging.error("Delete:  Directory not found")
                    else:
                        try:
                            ftp.delete(n)
                        except:
                            print("Error: File not found!")
                            logging.error("Delete: File not found")
            lib = ""

    elif "_d" in lib:     # Download
        if "/" not in lib:
            print("Use '/' as seperator")
            lib = ""
        else:
            fs = lib.split("/")
            fs = fs[1:]
            ready = True
            for i in fs:
                if i not in ftp.nlst():
                    print(f"ERROR: {i} is not found!")
                    logging.error(f"{i} is not found!")
                    ready = False
                    break

            if ready:
                await downloadhandler(ftp,fs,path)

            lib = ""

    elif "_u" in lib:     # Upload
        if "/" not in lib:
            print("Use '/' as seperator")
            lib = ""
        else:
            fs = lib.split("/")
            fs = fs[1:]
            ready = True

            for i in fs:
                if i not in os.listdir("Upload"):
                    print(f"ERROR: {i} is not found!")
                    logging.error(f"{i} is not found!")
                    ready = False
                    break

            if ready:
                n = []

                for i in range(len(fs)):
                    if "." not in fs[i]:
                        n.append(fs[i])
                for j in n:
                    if j in fs:
                        fs.remove(j)

                await uploadhandler(ftp,fs,path,n)
            lib = ""

    elif "_rel" in lib:
        lib = ""
        pass

    os.system("cls")
    await conhandler(ftp,lib,path)


async def downloadhandler(ftp,ls,path):
    threads = []
    for i in range(4):
        try:
            file = ls.pop(0)
        except IndexError:
            break
        if file:
            thread = Thread(download,ftp,file,path)
            threads.append(thread)

    for i in threads:
        i.start()
        time.sleep(random.uniform(0.30,0.40))

    for i in threads:
        i.join()
    if not ls:
        print("\n Download Completed!")
        return
    else:
        downloadhandler(ftp,ls,path)


def download(ftp,file,path,prevpath=""):

    if "." in file:
        localfile = open(f"Recieved/{file}","wb")
        logging.info(f"Downloading: {file}")
        print(f"Downloading: {file}")
        for j in range(3):
            try:
                ftp.retrbinary("RETR " + path + "/" + file, localfile.write,blocksize=2048)
                ftp.sendcmd("TYPE I")
            except:
                if j < 2:
                    logging.warning(f"Error occured while downloading: {file} Retrying: #{j+1}")
                    print(f"Error occured while downloading: {file} Retrying: #{j+1}")
                    time.sleep(0.5)
                else:
                    logging.error(f"Couldn't download: {file}")
                    print(f"Couldn't download: {file}")
            else:
                break


    else:
        folders = []
        try:
            os.mkdir(f"Recieved/{prevpath}{file}")
        except FileExistsError:
            pass

        path += "/" + file
        ftp.cwd(path)
        files = ftp.nlst()

        while files:
            threads = []
            for i in range(4):
                try:
                    f = files.pop(0)
                except IndexError:
                    break
                if "." in f:
                    thread = Thread(folderhandler,ftp,f,path,file,prevpath)
                    threads.append(thread)
                else:
                    folders.append(f)

            for i in threads:
                i.start()
                time.sleep(random.uniform(0.30,0.40))

            for i in threads:
                i.join()

        if len(folders) > 0:
            for i in folders:
                download(ftp,i,path,file+"/")


def folderhandler(ftp,file,path,dirname,prevpath=""):
    logging.info(f"Downloading: {file}")
    print(f"Downloading: {file}")
    for j in range(3):
        try:
            ftp.retrbinary("RETR " + path + "/" + file, open(f"Recieved/{prevpath}{dirname}/{file}", "wb").write,
                           blocksize=2048)
            ftp.sendcmd("TYPE I")
        except:
            if j < 2:
                logging.warning(f"Error occured while downloading: {file} Retrying: #{j+1}")
                print(f"Error occured while downloading: {file} Retrying: #{j+1}")
                time.sleep(0.5)
            else:
                logging.error(f"Couldn't download: {file}")
                print(f"Couldn't download: {file}")
        else:
            break


async def uploadhandler(ftp,files,path,dirs):

    threads = []

    while files:
        for i in range(4):
            try:
                file = files.pop(0)
            except IndexError:
                break
            thread = Thread(fileuploadhandler,ftp,file,path)
            threads.append(thread)

        for i in threads:
            i.start()
            time.sleep(random.uniform(0.30, 0.40))

        for i in threads:
            i.join()

    threads = []

    while dirs:
        try:
            file = dirs.pop(0)
        except IndexError:
            break

        ftp.cwd(path)
        folderuploadhandler(ftp,file,path,prevpath="")


def folderuploadhandler(ftp,dir,path,prevpath=""):
    if dir not in ftp.nlst():
        ftp.mkd(dir)

    ftp.cwd(path + "/" + prevpath + dir)

    fp = os.listdir(f"Upload/{prevpath}{dir}")
    prevpath += dir + "/"
    folders = []

    for i in range(len(fp)):
        if "." not in fp[i]:
            folders.append(fp[i])
    for j in folders:
        if j in fp:
            fp.remove(j)

    while fp:
        threads = []
        for i in range(4):
            try:
                file = fp.pop(0)
            except IndexError:
                break

            thread = Thread(fileuploadhandler,ftp,file,path,prevpath)
            threads.append(thread)

        for i in threads:
            i.start()
            time.sleep(random.uniform(0.30, 0.40))

        for i in threads:
            i.join()

    while folders:
        try:
            fold = folders.pop(0)
        except IndexError:
            break
        folderuploadhandler(ftp,fold,path,prevpath)


def fileuploadhandler(ftp,file,path,prevpath=""):
    localfile = open(f"Upload/{prevpath}{file}", "rb")
    logging.info(f"Uploading: {file}")
    print(f"Uploading: {file}")
    for j in range(3):
        try:
            ftp.storbinary("STOR " + file, localfile, blocksize=3072)
            ftp.sendcmd("TYPE I")
        except:
            if j < 2:
                logging.warning(f"Error occured while uploading: {file} Retrying: #{j + 1}")
                print(f"Error occured while uploading: {file} Retrying: #{j + 1}")
                time.sleep(0.5)
            else:
                logging.error(f"Couldn't upload: {file}")
                print(f"Couldn't upload: {file}")
        else:
            break


asyncio.run(setup())