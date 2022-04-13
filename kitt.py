#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# =============================================================================
# Author : @senges
# Version : March 2022
# Description : A portable toolbox
# =============================================================================

from container import client as docker

def main():
    docker.pull('hello-world')
    docker.run('hello-world')

if __name__ == '__main__':
    main()