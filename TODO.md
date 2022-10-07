# TODO
## Fixs

- [x] Path is not properly exported for root, cannot find catalog bin folder
- [x] Docker group GID do not match host group GID
- [ ] X11 forwarding mostly works, but xeyes is super laggy

## Short term

- [x] Add static files onboarding
- [x] Add dind managment with new user
- [x] Add push strategy
- [x] Add secret managment
- [x] Handle local user not in docker group (run as other user ?)
- [x] Make sure local catalog image is updated
- [ ] Add layer caching for prebuild
- [ ] Better logging
- [x] Should we properly handle runtimes ? (go, python, ..) => Probably not as exploiting Nix dependencies ?
- [ ] Shoud share PID with host ? (--pid=host)
- [ ] Only remap UID/GID when volumes (?)
- [x] Make plugins J2 generated
- [ ] Add bash / zsh completion
- [ ] Proper host home mapping of folders / dotfiles
- [ ] Add custom part for Dockerfile
- [ ] package location instead of __file__ : http://peak.telecommunity.com/DevCenter/PythonEggs#accessing-package-resources
- [ ] Refresh only one image

## Mid-Long term

- [x] Kitt inside kitt ? (=> added to catalog)
- [ ] Attach other TTY to running kitt container
- [x] Catalog custom input file not supported yet => fixed by Nix
- [ ] Display building logs (see Image.build second argument as JSON stream)
- [ ] Add sound (see [docker-pulseaudio-example](https://github.com/TheBiggerGuy/docker-pulseaudio-example))