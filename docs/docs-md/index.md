
[![Ambianic logo](https://avatars2.githubusercontent.com/u/52052162?s=200&v=4)](https://ambianic.ai)

# Project mission
## Helpful AI for Home and Business Automation

Ambianic is an Open Source AI platform that puts local control and privacy
first. It enables users to run and train custom AI models
without compromising privacy and without sharing data with cloud providers.

[View on Github](https://github.com/ambianic/ambianic-core)

# Why?

What's the root cause for Ambianic.ai to exist? Below is a
[5 Whys](https://en.wikipedia.org/wiki/Five_whys) diagram that
tries to answer this key question objectively.

![Ambianic 5 Whys](assets/ambianic-5whys.svg)

Needless to say there are
subjective reasons which are equally if not more influential for the existence
of this project such as basic human excitement to serve a bigger purpose
via open source AI.

# User Journey

Ambianic's roadmap is inspired by user stories and community feedback.
The following diagram illustrates an example user journey.

![Ambianic example user journey](assets/ambianic-example-user-journey.svg)


User journeys help us align on the bigger picture and segue into  
agile development constructs such as user stories and sprints.
More user journeys will be added over time as the project evolves. Some of the
candidate topics include:

- **Home Automation**
    - Turn traditional door locks into smart locks with Face Recognition.
    - Alert parents if a crying toddler is left unattended for more than 15 minutes.
    - Raise an alert if a baby is seated near a car door without child lock enabled while in motion.

- **Business Automation**
    - Prevent accidents by alerting drivers who act sleepy or distracted.
    - Make sure that a factory floor position is not left unattended for more than 15 minutes.
    - Recognize presence of unauthorized people in a restricted access work area.

# Project Status
At this time, Ambianic is in active early formation stages. Design and implementation decisions are made daily with focus on advancing the project to an initial stable version as soon as possible.

If you are willing to take the risk that comes with early stage code and are able to dive deep into Python, Javascript, Gstreamer, and Tensorflow code, then please keep reading. Otherwise you can register to [watch for new releases](https://github.com/ambianic/ambianic-core). We will notify you as soon as a stable release is out.

# Product design guidelines

Our goal is to build a product that is useful out of the box:

 - Less than 15 minutes setup time
 - Less than $75 in hardware costs
   + Primary platform: Raspberry Pi 4 B, 4GB RAM, 32GB SDRAM
 - No coding required to get started
 - Decomposable and hackable for open source developers

# How to run in development mode
If you are interested to try the development version, follow these steps:

1. Clone this git repository.
2. `./ambianic-start.sh`
3. Study `config.yaml` and go from there.

# Contributors
If you are interested in becoming a contributor to the project, please read the [Contributing](legal/CONTRIBUTING.md) page and follow the steps. Looking forward to hearing from you!

# Documentation

At this time there is not much documentation in place. The goal is to fill in the gaps as the project advances closer to a stable version. The latest dev docs are available here:
[Developer Documentation](https://ambianic.github.io/ambianic-core/ambianic-python-api/)
