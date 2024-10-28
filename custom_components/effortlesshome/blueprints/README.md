EffortlessHome Blueprints

Welcome to the EffortlessHome Blueprints repository! This repository contains a collection of blueprints designed to simplify and enhance your home automation experience with Home Assistant. These blueprints are crafted specifically to help users streamline their automation setups and maximize the benefits of home automation using the EffortlessHome system.

Table of Contents

	•	About
	•	Installation
	•	Available Blueprints
	•	How to Use
	•	Contributing
	•	License

### Sections:
- **Overview**: A general introduction to the repository and what it offers.
- **Installation**: Instructions for installing via Home Assistant.
- **Configuration**: Directions on configuring.
- **Development**: Information for developers who want to contribute or modify the repository.
- **License**: Licensing information.

### EffortlessHome Options:
- **System Restore**: Includes all of the EffortlessHome capabilities below (and other must have components) in one simple sytem restore file. Get up and running quickly and easily.
- **Add-Ons**: Add-ons for cloud backups and remote access
- **Integration**: The Core EffortlessHome Native Integration
- **Blueprints**: A large set of easy to use automation and script blueprints
- **Theme**: A stylish theme to get the EffortlessHome look and feel

About

EffortlessHome provides turn-key solutions for home automation, removing the complexity often associated with integration and setup. These blueprints are designed to offer easy-to-use automation templates that can be quickly deployed for common home automation scenarios.

Our blueprints cover a wide range of automation needs, from lighting control to security system management, allowing you to set up powerful automations with just a few clicks.

Installation

To install a blueprint in Home Assistant:

	1.	Navigate to the Settings > Automations & Scenes > Blueprints section in Home Assistant.
	2.	Click on Import Blueprint.
	3.	Paste the URL of the desired blueprint from this repository and click Preview.
	4.	Once previewed, click Import to save the blueprint to your Home Assistant instance.
	5.	Now you can create an automation from the imported blueprint.

Alternatively, you can manually download the blueprint YAML files and place them in the /config/blueprints/ directory in your Home Assistant configuration.

Available Blueprints

Here is a list of some of the available blueprints in this repository:

	1.	Motion-Based Lighting Control
Automate your lights based on motion detection in specific areas of your home.
	2.	Security System Arm/Disarm with PIN
Automatically arm or disarm your security system with a configurable PIN code.
	3.	Presence-Based HVAC Control
Adjust the temperature of your home automatically based on presence detection.
	4.	Timed Lights Automation
Set lights to turn on and off at specific times, with customizable settings.

More blueprints are being added regularly, so check back often!

How to Use

Each blueprint has its own configuration options that allow you to customize the behavior of the automation. After importing a blueprint, go to the Automations section in Home Assistant and create a new automation based on the blueprint.

Make sure to review the blueprint’s documentation in this repository or directly in Home Assistant to understand the available options for each blueprint.

Example

To create a motion-based lighting control automation:

	1.	Import the Motion-Based Lighting Control blueprint.
	2.	Go to Automations & Scenes > Create Automation.
	3.	Select From Blueprint and choose the Motion-Based Lighting Control blueprint.
	4.	Configure the settings (such as the area and motion sensors to use).
	5.	Save the automation, and your lights will now automatically turn on when motion is detected.

Contributing

We welcome contributions from the community! If you have a blueprint that you’d like to share or improve, feel free to submit a pull request. Please ensure that your blueprints are well-documented, and include clear instructions on how they should be used.

For bug reports or feature requests, please open an issue in this repository.

License

This repository is licensed under the Apache 2.0 License. See the LICENSE file for more details.

