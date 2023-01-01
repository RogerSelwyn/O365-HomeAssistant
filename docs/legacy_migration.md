---
title: Legacy Migration
nav_order: 11
---

# Legacy Migration
Historically the Office 365 Calendar o=integration supported a single account. Over the last year several features have been added including support for multiple accounts. This change to multiple accounts necessitated an alternate configuration schema.

Having two schemas introduces extra complexity into the integration, so the secondary/legacy schema is now being marked as deprecated to encourage migration to the new schema (which has been the preferred one since May 2022).

To assist in this migration, when you restart Home Assistant, the following things will happen:
1.	A modified version of the configuration will be created on the `o365_storage` folder called `o365_converted_configuration.yaml`. You should be able to copy the contents of this file and replace your existing configuration. Your `client_id` and `client_secret` have been obfuscated with `xxxx` so, you will need to replace these.
2.	Your token file has been copied as `o365_converted.token`
3.	Your `o365_calendar.yaml` file has been copied as `o365_calendars_convetted.yaml`

After modifying your config as in (1) above and then restarting Home Assistant, you should no longer have the repair warning and your calendars (and other sensors) should be present as before.

If you decide to change the account name from `converted`, then calendars will be created with `_account_name` on the end, and you will need to re-authenticate and reconfigure your o365_calendars.yaml file. Alternatively, you can perform steps (2) and (3) above using your new account name instead of `converted` in the name.
