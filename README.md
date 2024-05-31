[![Validate with hassfest](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hassfest.yaml) [![HACS Validate](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml/badge.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/actions/workflows/hacs.yaml) [![CodeFactor](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant/badge)](https://www.codefactor.io/repository/github/rogerselwyn/o365-homeassistant) [![Downloads for latest release](https://img.shields.io/github/downloads/RogerSelwyn/O365-HomeAssistant/latest/total.svg)](https://github.com/RogerSelwyn/O365-HomeAssistant/releases/latest)

![GitHub release](https://img.shields.io/github/v/release/RogerSelwyn/O365-HomeAssistant) [![maintained](https://img.shields.io/maintenance/yes/2024.svg)](#) [![maintainer](https://img.shields.io/badge/maintainer-%20%40RogerSelwyn-blue.svg)](https://github.com/RogerSelwyn) [![hacs_badge](https://img.shields.io/badge/HACS-Default-41BDF5.svg)](https://github.com/hacs/integration) [![Community Forum](https://img.shields.io/badge/community-forum-brightgreen.svg)](https://community.home-assistant.io/t/office-365-calendar-access)

# 💥💥💥 Views Wanted 💥💥💥
I'm considering breaking up the monolithic O365 integration into smaller, more manageable items. If you have a view, please comment here:

[O365 --> MS365 - A potential big change - your views needed](https://github.com/RogerSelwyn/O365-HomeAssistant/discussions/234)

# Office 365 Integration for Home Assistant

*This is a fork of the original integration by @PTST which has now been archived.*

This integration enables:
1. Getting and creating calendar events
1. Getting emails from your inbox using one of two available sensor types (e-mail and query)
1. Sending emails via the notify.o365_email service
1. Getting presence from Teams (not for personal accounts)
1. Getting the latest chat message from Teams (not for personal accounts)
1. Getting and creating To-Do tasks
1. Setting Auto Reply/Out of Office response

This project would not be possible without the wonderful [python-o365 project](https://github.com/O365/python-o365).

## [Buy Me A Beer 🍻](https://buymeacoffee.com/rogtp)
I work on this integration because I like things to work well for myself and others. Whilst I have now made significant changes to the integration, it would not be as it stands today without the major work to create it put in by @PTST. Please don't feel you are obligated to donate, but of course it is appreciated.

<a href="https://www.buymeacoffee.com/rogtp" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a> 
<a href="https://www.paypal.com/donate/?hosted_button_id=F7TGHNGH7A526">
  <img src="https://github.com/RogerSelwyn/actions/blob/e82dab9e5643bbb82e182215a748a3024e3e7eac/images/paypal-donate-button.png" alt="Donate with PayPal" height="40"/>
</a>

# Documentation

The full documentation is available here - [O365 Documentation](https://rogerselwyn.github.io/O365-HomeAssistant/)

Nice video from fixtse showing how to install the O365 integration to Home Assistant. Also providing some Lovelace cards for displaying content from O365 - [O365 Card for Home Assistant](https://github.com/fixtse/o365-card)
