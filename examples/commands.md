# Commands examples
## Build and push

```
➜  kitt --debug build -f /tmp/myshell.toml myshell
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