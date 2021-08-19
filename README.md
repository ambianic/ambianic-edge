[![Gitpod ready-to-code](https://img.shields.io/badge/Gitpod-ready--to--code-blue?logo=gitpod)](https://gitpod.io/#https://github.com/ambianic/ambianic-edge)
[![Join the Slack chat room](https://img.shields.io/badge/Slack-Join%20the%20chat%20room-blue)](https://join.slack.com/t/ambianicai/shared_invite/zt-eosk4tv5-~GR3Sm7ccGbv1R7IEpk7OQ)

[![Docker pulls](https://img.shields.io/docker/pulls/ambianic/ambianic-edge?color=dark-green&label=Downloads)](https://hub.docker.com/r/ambianic/ambianic-edge)
![CI Build](https://github.com/ambianic/ambianic-edge/workflows/Ambianic%20Edge%20CI/badge.svg)
[![codecov](https://codecov.io/gh/ambianic/ambianic-edge/branch/master/graph/badge.svg?token=JJlxaW5flS)](https://codecov.io/gh/ambianic/ambianic-edge)
[![FOSSA Status](https://app.fossa.io/api/projects/git%2Bgithub.com%2Fambianic%2Fambianic-edge.svg?type=shield)](https://app.fossa.io/projects/git%2Bgithub.com%2Fambianic%2Fambianic-edge?ref=badge_shield) 
[![CodeFactor](https://www.codefactor.io/repository/github/ambianic/ambianic-edge/badge)](https://www.codefactor.io/repository/github/ambianic/ambianic-edge)
![CodeQL](https://github.com/ambianic/ambianic-edge/workflows/CodeQL/badge.svg)
![Container Security Scan](https://github.com/ambianic/ambianic-edge/workflows/Container%20Security%20Scan/badge.svg)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/ambianic/ambianic-edge.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/ambianic/ambianic-edge/context:python)

![Ambianic logo][ambianic-logo]
 &nbsp; 
<a href="https://landscape.lfai.foundation/format=card-mode&selected=ambianic">
  <img src="https://raw.githubusercontent.com/lfai/artwork/main/lfaidata-assets/lf-member/associate/lf_mem_asso.png"  height="200" style="display:inline;vertical-align:middle;padding:2%">   
</a>
 &nbsp; 
<a href="https://twitter.com/TensorFlow/status/1291071490062983172?s=20">
  <img src="https://pbs.twimg.com/profile_banners/1195860619284664320/1596827858/1500x500"  height="200" style="display:inline;vertical-align:middle;padding:2%">   
</a>

# Project mission
  
[Ambianic.ai](https://ambianic.ai) is an [award winning](https://blog.ambianic.ai/2020/11/05/awards.html) Open Source Ambient Intelligence platform for Home and Business Automation.

It has two main components:
- [Ambianic Edge](https://github.com/ambianic/ambianic-edge) runs on edge devices such as Raspberry Pi. It monitors sensors, cameras and other inputs, passes them through AI inference and makes actionable observations. We recommend deploying Ambianic Edge in an [Ambianic Box](https://github.com/ambianic/ambianic-box) enclosure.
- [Ambianic UI](https://github.com/ambianic/ambianic-ui) is the user interface to Ambianic Edge deployments. Latest live version available at [ui.ambianic.ai](https://ui.ambianic.ai).

Following is a conceptual flow diagram:

![Remote Home Care Flow](https://raw.githubusercontent.com/ambianic/ambianic-docs/master/docs-md/assets/images/Ambianic-Remote-Elderly-Care-Flow.png)

High level architecture diagram below:

![Ambianic.ai High Level Architecture](https://raw.githubusercontent.com/ambianic/ambianic-docs/master/docs-md/assets/images/Ambianic-High-Level-Architecture.png)

A more detailed project background document is available [here](https://docs.ambianic.ai/).

A deep dive technical discussion of the project architecture is available in this [WebRTCHacks article](https://webrtchacks.com/private-home-surveillance-with-the-webrtc-datachannel/).

# Project Status

Ambianic Edge is in now generally available for use in the real world. Here is a [Quick Start Guide](https://docs.ambianic.ai/users/quickstart/).

All constructive feedback is most welcome!

# Product design highlights

- [x] Less than $55 in hardware costs. Get [Ambianic Box](https://github.com/ambianic/ambianic-box).
- [x] Less than 15 minutes setup time. Get [RPI Image](https://github.com/ambianic/ambianic-rpi-image).
- [x] No coding required to get started. Just follow the [Quick Start Guide](https://docs.ambianic.ai/users/quickstart/).
- [x] Decomposable and hackable for DYI and Open Source developers. [Setup Your Dev Environment](https://docs.ambianic.ai/developers/development-environment/)

# How to run in development mode

If you are interested to try the development version, follow [this guide](https://docs.ambianic.ai/developers/development-environment/).

# Documentation

An introduction to the project with user journey, architecture and other high level artifacts are [now available here](https://ambianic.github.io/ambianic-docs/).

Additional content is coming in daily as the project advances to its official release.

# Community Support 

If you have questions, ideas or cool projects you'd like to share with the Ambianic team and community, please use the [Ambianic Twitter channel](https://twitter.com/ambianicai).

# Contributing
Your constructive feedback and help are most welcome!

If you are interested in becoming a contributor to the project, please read the [Contributing](CONTRIBUTING.md) page and follow the steps. Looking forward to hearing from you!

[ambianic-logo]: https://avatars2.githubusercontent.com/u/52052162?s=200&v=4

# Acknowledgements
  
This project has been inspired by the prior work of many bright people. Special gratitude to:
* [Yong Tang](https://github.com/yongtang) for his guidance as Tensorflow SIG IO project lead
* [Robin Cole](https://github.com/robmarkcole) for his invaluable insights and code on home automation AI with Home Assistant
* [Blake Blackshear](https://github.com/blakeblackshear) for his work on Frigate and vision for the home automation AI space
  
 
 