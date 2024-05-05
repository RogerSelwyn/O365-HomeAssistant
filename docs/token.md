---
title: Token
nav_order: 18
---

# Token
At some point you are very likely need to delete your token so that you re-authenticate to Office 365. This may be because you have added new features to your configuration or your secret has expired.

To do this delete the relevant token file (according to the account name in your config) from the `<config>/o365_storage/.O365-token-cache` directory. When you restart HA, you will then be prompted to re-authenticate with O365 which will store a new token.