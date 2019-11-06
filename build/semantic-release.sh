#!/bin/bash
# exit bash script on error
set -e

# verbose mode
set -x

ls -al
pwd

npm cache clean -f
npm install -g n
n stable
node --version

npm install -g npm@latest
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
