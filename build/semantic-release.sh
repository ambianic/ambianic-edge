#!/bin/bash
# exit bash script on error
set -e

# verbose mode
set -x

ls -al
pwd

# nvm install node --reinstall-packages-from=$(nvm current)
nvm install lts/* --reinstall-packages-from=node
nvm ls
nvm uninstall v8
nvm ls

# npm cache clean -f
# npm install n
# n stable
node --version

npm install npm@latest
# npm install -U node
# npm install lts/*
npm install --save-dev @semantic-release/commit-analyzer
npm install --save-dev @semantic-release/git
npm install --save-dev semantic-release
npm install --save-dev semantic-release-docker
npm install --save-dev @semantic-release/release-notes-generator
npm install --save-dev @semantic-release/github
npm install --save-dev @semantic-release/changelog
npm install --save-dev @semantic-release/exec
node --version
npx semantic-release
