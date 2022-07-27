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
- [ ] Proper host home mapping of folders / dotfiles
- [ ] Add custom part for Dockerfile
- [ ] Make sure local catalog image is updated

## Mid-Long term

- [x] Kitt inside kitt ? (=> added to catalog)
- [ ] Attach other TTY to running kitt container
- [ ] Catalog custom input file not supported yet
- [ ] Display building logs (see Image.build second argument as JSON stream)
- [ ] Add sound (see [docker-pulseaudio-example](https://github.com/TheBiggerGuy/docker-pulseaudio-example))