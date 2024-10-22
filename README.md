*Please :star: this repo if you find it useful*

[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/hacs/integration)

# EffortlessHome Integration for Home Assistant

EffortlessHome is a custom Home Assistant integration that enables effortless automation and control of your smart home devices. Our integration focuses on ease of use, seamless automation, and enhanced control, all tailored to your home’s needs. We include the best of Home Assistant and it's ecosystem, add our expertise to that including a full set of optional services such as remote backups, secure remote access, best practice automation and script blueprints, automatic device grouping (e.g. motion sensors, lights by area), and much more!

## Features

- **Singular view, integration and control of your smart home from practically any computing device**
- **Fully Integrated Automation**: Automatically manage lights, locks, security systems, and more.
- **Customizable Automations & Blueprints**: EffortlessHome allows you to create custom automations based on your household's behavior and preferences.
- **Seamless Integration with Home Assistant**: This integration works natively within Home Assistant, enabling the effortless setup and control of your home automation systems.
- **Offline Device Management**
- **Low Battery Notifications**
- **Motion and condition-based lighting**
- **Camera motion/person snapshot captures with combined view of history, cleanup, remote backups**
- **Automatic tracking of system home/away modes**
- **Sleeping/Awake awareness**
- **Calendar Integation**
- **System Remote Access**
- **24x7 security and monitoring powered by Noonlight**
- **24x7 Medical Alert monitoring powered by Noonlight**
- **Alarmo built-in**
- **Presence simulation for added security**
- **Offline Device Notifications**
- **Cloud Backups To Your Google Drive**
- **PowerCalc**
- **HACS**
- **SMB**
- **Preconfigured, Customizable Dashboards**
- **Mosquitto MQTT**
- **Zigbee2MQTT**
- **Aircast**
- **Matterbridge**
- **Dumb to Smart Appliance Conversion With Power-Monitoring Plugs**
- **More coming with bug fixes and enhancements every month!**



## Installation

1. Add this Repository to your HACS....


# Installation
## Option 1
- In your Home Assistant configuration directory (`~/.homeassistant` for instance), create a directory `custom_components/presence_simulation` and put the code in it.
- Restart Home Assistant
## Option 2
- Go in your Home Assistant configuration directory (`~/.homeassistant` for instance)
- `git clone https://github.com/slashback100/presence_simulation.git`. It will create the directory `custom_components/presence_simulation`
- Restart Home Assistant
## Option 3 (recommended)
- Have [HACS](https://hacs.xyz/) installed, this will allow you to easily manage and track updates.
- You can either search for "Presence Simulation" or use this link [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?repository=presence_simulation&category=Integration&owner=slashback100).
- Click Install below the found integration.
- Restart Home Assistant

Options:

	•	email: The email address associated with your EffortlessHome account.
	•	system_id: The ID of your home system in EffortlessHome.
	•	url: The URL for system management.

Supported Entities

	•	input_boolean: Controls for various boolean states (e.g., isrenteroccupied).
	•	input_text: Custom text fields like lock codes or user names.
	•	light: Automate and group lights across different areas.
	•	motion: Group motion sensors and automate behavior.

Usage

Once the integration is installed, you can begin configuring automation rules for your devices directly from Home Assistant’s UI. Some examples include:

	•	Automatically turning off lights when no motion is detected.
	•	Triggering security alarms when certain conditions are met.

Contributing

We welcome contributions! Feel free to submit issues or pull requests to enhance the functionality of this integration.

EffortlessHome.co’s primary competitive advantage is our focus on delivering fully integrated, turn-key home automation solutions that eliminate the complexity commonly found in smart home setups. What sets us apart from others in the field includes:

	1.	Seamless Integration: We ensure all smart devices, from security systems to lighting and climate control, work together effortlessly, without requiring customers to have technical expertise.
	2.	Affordability: Unlike competitors that often come with high costs for custom installations, we offer cost-effective solutions that provide a high level of automation without hidden fees or ongoing maintenance costs.
	3.	Ease of Use: Our system is designed for intuitive control, allowing homeowners and renters to manage their smart devices through a user-friendly platform that requires minimal setup.
	4.	Custom Solutions: We offer personalized setups tailored to the specific needs of each household or business, unlike many generic off-the-shelf solutions.

By focusing on simplifying automation and integration while keeping it affordable, we provide a unique experience in the smart home industry.

## Need Help?
<EH Fiverr Info/Link Here>
<EH Website Link Here>