# Commands examples
## Build and push

```
➜  kitt --debug build /tmp/myshell.toml myshell
✓ Build success !

➜  kitt list
 myshell
 pentest
 debug-tools
 toolkit

➜  kitt push --registry "senges/kitt" myshell
✓ Push done !

➜  kitt push --registry "senges/kitt" toolkit
✓ Push done !
```

## Pull and run

```
➜  kitt list
 toolkit

➜  kitt pull senges/kitt myshell
✓ Image myshell pull done

➜  kitt remove toolkit
✓ Done !

➜  kitt list
 myshell

➜  kitt run myshell
user@myshell~$ echo "Hello kitt container !"
Hello kitt container ! 
```

## Run with custom context

If user is not un docker group, you will want to run kitt as root.  
However, you might still want to keep acting like the current user.

Then just run `kitt run` command with `--user` (or `-u`) flag to run as another host user.

```
➜  sudo kitt run -u mike -v /home/mike/.kube:/home/user/.kube:rw myshell
user@myshell~$ ls -lAh
.bashrc
.kube
```