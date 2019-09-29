[![Build Status](https://travis-ci.org/ambianic/ambianic-core.svg?branch=master)](https://travis-ci.org/ambianic/ambianic-core) [![Docker Automated](https://img.shields.io/docker/cloud/automated/ambianic/ambianic.svg)](https://hub.docker.com/r/ambianic/ambianic/builds) [![Docker Build](https://img.shields.io/docker/cloud/build/ambianic/ambianic.svg)](https://hub.docker.com/r/ambianic/ambianic/builds) [![codecov](https://codecov.io/gh/ambianic/ambianic-core/branch/master/graph/badge.svg)](https://codecov.io/gh/ambianic/ambianic-core)

![Ambianic logo][logo]

# Project mission
Helpful AI for Home and Business Automation

Local data, custom AI models, federated learning

# Project Status
At this time, Ambianic is in active early formation stages. Lots of design and implementation decisions are made daily with focus on advancing the project to an initial stable version as soon as possible. 

If you are willing to take the risk that comes with early stage code and are able to dive deep into Python, Javascript, Gstreamer, and Tensorflow code, then please keep reading. Otherwise click on the Watch button above (Releases Only option) to be notified when we release a stable end user version.

# Product design guidelines

When the product is officially released, it must show tangible value to first time users with:
- Less than 15 minutes setup time 
- Less than $75 in hardware costs
  + Primary target platform: Raspberry Pi 4 B, 4GB RAM, 32GB SDRAM
- No coding required to get started
- Decomposable and hackable

Relaxing these constraints could unlock deeper value out of the platform. APIs and scalability have their benefits. However we strive to provide a simple and beautiful out of the box experience.

# How to run in development mode
If you are interested to try the development version, follow these steps:
1. Clone this git repository.
2. `./ambianic-start.sh`
3. Study `config.yaml` and go from there.

# Contributors
If you are interested in becoming a contributor to the project, please read the [Contributing](CONTRIBUTING.md) page and follow the steps. Looking forward to hearing from you!

[logo]: https://avatars2.githubusercontent.com/u/52052162?s=200&v=4

# Documentation

At this time there is not much documentation in place. The goal is to fill in the gaps as the project advances closer to a stable version. The latest dev docs are available here: 
[Developer Documentation](https://ambianic.github.io/ambianic-core/ambianic-python-api/)
