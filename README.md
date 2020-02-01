[![Build Status](https://travis-ci.org/ambianic/ambianic-edge.svg?branch=master)](https://travis-ci.org/ambianic/ambianic-edge) 
[![Docker Automated](https://img.shields.io/docker/cloud/automated/ambianic/ambianic.svg)](https://hub.docker.com/r/ambianic/ambianic/builds) 
[![Docker Build](https://img.shields.io/docker/cloud/build/ambianic/ambianic.svg)](https://hub.docker.com/r/ambianic/ambianic/builds) 
[![codecov](https://codecov.io/gh/ambianic/ambianic-core/branch/master/graph/badge.svg)](https://codecov.io/gh/ambianic/ambianic-core)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fambianic%2Fambianic-core.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fambianic%2Fambianic-core?ref=badge_shield) 
[![CodeFactor](https://www.codefactor.io/repository/github/ambianic/ambianic-edge/badge)](https://www.codefactor.io/repository/github/ambianic/ambianic-edge)
  
![Ambianic logo][logo]

# Project mission

[Ambianic.ai](https://ambianic.ai) is an Open Source Ambient Intelligence platform for Home and Business Automation

[Ambianic Edge](https://github.com/ambianic/ambianic-edge) runs on edge devices such as Raspberry Pi. It monitors sensors, cameras and other inputs, passes them through AI inference and makes actionable observations.

[Ambianic UI](https://github.com/ambianic/ambianic-ui) is the user interface to Ambianic Edge deployments. Latest live version available at [ui.ambianic.ai](https://ui.ambianic.ai)

# Project Status
Ambianic Edge is in active development stage sprinting towards its first public Beta.

# Product design goals

When the product is officially released, it must show tangible value to first time users with minimal initial investment.
- Less than 15 minutes setup time
- Less than $75 in hardware costs
  + Reference hardware platform: Raspberry Pi 4 B, 4GB RAM, 32GB SDRAM
- No coding required to get started
- Decomposable and hackable

# How to run in development mode
If you are interested to try the development version, follow these steps:
1. Clone this git repository.
2. `./ambianic-start.sh`
3. Study `config.yaml` and go from there.

# Documentation

An introduction to the project with user journey, architecture and other high level artifacts are [now available here](https://ambianic.github.io/ambianic-docs/).

Additional content is coming in daily as the project advances to its official release.

# Community Support 

If you have questions, ideas or cool projects you'd like to share with the Ambianic team and community, please use the [Ambianic Twitter channel](https://twitter.com/ambianicai).

# Contributing
Your constructive feedback and help are most welcome!

If you are interested in becoming a contributor to the project, please read the [Contributing](CONTRIBUTING.md) page and follow the steps. Looking forward to hearing from you!

[logo]: https://avatars2.githubusercontent.com/u/52052162?s=200&v=4

# Acknowledgements

This project has been inspired by the prior work of many bright people. Special gratitude to:
* [Yong Tang](https://github.com/yongtang) for his guidance as Tensorflow SIG IO project lead
* [Robin Cole](https://github.com/robmarkcole) for his invaluable insights and code on home automation AI with Home Assistant
* [Blake Blackshear](https://github.com/blakeblackshear) for his work on Frigate and vision for the home automation AI space
