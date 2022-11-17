# Changelog

## v4.0.0 (2022/11/17)
### Breaking Changes
- `calendar_id` is no longer supported as a parameter in service calls. `entity_id` should be used instead. Overall the changes to services calls in this release, improves validation and should make it clearer when calling the service as to what a problem might be.
- Be aware that the location of the o365 token and o365_calendar.yaml files have been moved under the `o365_storage` directory. This helps to group the various o365 files in one place. If you are backing up your configuration to a public GitHub, you will need to change your `.gitignore`

### Enhancements
- Meaningful icons have been added to all sensors. Thanks for @rdeveen for prompting the change.
- Tasks/Todo sensors can be enabled. See [Configuration](https://rogerselwyn.github.io/O365-HomeAssistant/installation_and_configuration.html) for details.

## v3.3.0 (2022/11/10)
### Enhancements
- [Add ability to read group calendars](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/6ba872fea5478bc0727abf559585ca6950039e3d) - @RogerSelwyn

### Maintenance
- [Bump to v3.3.0 Alpha 1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4e9828cc53080da96f247b363da85c53af734147) - @RogerSelwyn
- [Sourcery code recommendations](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/f3d5391c522932a746c4e2f4db23e5b5c7338a05) - @RogerSelwyn
- [Sourcery code improvements](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1be5c9ddec9572d79dd2f80740f360ff27e37863) - @RogerSelwyn
- [Bump to v3.3.0](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b25edce41358d3ca2b6dce0aba21d4e8937ee6de) - @RogerSelwyn

## v3.2.3 (2022/11/05)
### Enhancements
- [Add ability to send for delegated user](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b9c18bc4918415085f092089321cfae76d2bf501) - @RogerSelwyn

### Maintenance
- [Update installation_and_configuration.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/53457035eec5bf0b586d17ff7ea934875ab57f34) - @RogerSelwyn
- [Update errors.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/52b12fc9a2f6433d056535285cbf6987ad2c8fa0) - @PuffinRub
- [Bump to v.3.2.3](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/465d2143843e8a5ee9da7ba202f879c9781cf96c) - @RogerSelwyn

## v3.2.2 (2022/09/26)
### Enhancements
- [Moved documentation to GitHub page](https://rogerselwyn.github.io/O365-HomeAssistant/) - @RogerSelwyn
- [Return line breaks where available](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8f445edfaf7edec48e887ca5f44d730e6525b133) - @RogerSelwyn

### Maintenance
- [Make account type not optional](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/e8135254ec6cc0499fcf18c7a2dc9e52268173df) - @spookyuser
- [Bump o365 to 2.0.20](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/63569ea4ed7a4481678da6a7f70e50e56b8e4400) - @RogerSelwyn
- [Code cleanup](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1c9086554daf5177094271164974e1822d22c753) - @RogerSelwyn
- [Bump o365 module to 2.0.21](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/174b5e2501055188d7ff09414b63a9d71a311c70) - @RogerSelwyn
- [Bump to v3.2.2](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/168d981c2a8dcf59ad536abc16702592508a2ff1) - @RogerSelwyn

## v3.2.1 (2022/05/26)
### Enhancements
- [Add filtering on body](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b593646ca2c073929cdc7025fd59391df149ea4c) - @RogerSelwyn
### Maintenance
- [Remove unnecessary BCC](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/57b2839a94f16085fa13094f37d7f1c9f0d2f1d1) - @RogerSelwyn
- [Update readme](https://github.com/RogerSelwyn/O365-HomeAssistant/pull/57) - @GitHubGoody
- [Update CHANGELOG.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3bd203e9bce7f0da3f70bdb9401eb9ce468a4b88) - @RogerSelwyn
- [Remove domains key from hacs.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/2066cb3b60a40ec9aa181b5404c5b927ec4ab33d) - @RogerSelwyn
- [Bump o365 to 2.0.19](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/880950c2228a11730700a268fc648fa48a972385) - @RogerSelwyn
- [Bump to v3.2.1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4541f66e4dfa81acce7be8f5d906ecaf4f291804) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/9065037f974f1bb09e6368261fbe4223a7765da0) - @actions-user

## v3.2.0 (2022/05/19)
### Breaking change
- [Change default auth method](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/efb3cf2b00d2d32df53691e3c82eb87d077ec814) - @RogerSelwyn
### Enhancements
- [Add Chat Sensor](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/0184872e15b357489edfc56e1d11520fd187ba50) - @RogerSelwyn
### Maintenance
- [Update authentication info](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7c3c1e0aabb8f709925aa99357e2bba5a3f07e25) - @RogerSelwyn
- [Add deprecation warning and change alt_auth config parameter](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7feef161c715b9799a39be18165c90a392b54c85) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4d69ccd0467470fab0e6ccc5cc42626ee3345faa) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/218443692e8762d25ab7a26723159ce632019cf6) - @RogerSelwyn
- [Create stale.yaml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3a93714c918658850840d0e16b3e989c9150e7dc) - @RogerSelwyn
- [Bump to v3.2.0](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/62091cb924abbcafd283ca7a5aad47d4e7e5c790) - @RogerSelwyn

## v3.1.1 (2022/05/06)
### Fixes
- [Fix error on device update](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d5ed3cc98e95cdebfae334cb44b7009a5463f09e) - @RogerSelwyn
### Maintenance
- [Bump to v3.1.1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/9caac0960f198f4c24c75fac5d94f6b96cc8ffda) - @RogerSelwyn

## v3.1.0 (2022/05/05)
### Enhancements
- [Move setup_platform to async](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/dc8974b83858b7f4e401e0e0e36b6c0c15c3bf99) - @RogerSelwyn
- [Move calls to o365 async](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/f9dfedd42f70c03f49760ba6fba8adcce4fd2cdc) - @RogerSelwyn
### Fixes
- [Fix issue with photo embedding](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d0eff81b6d6fa39246ed37113a300b4a88288a73) - @RogerSelwyn
### Maintenance
- [Use CalendarEntity instead of CalendarEventDevice](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/712daf59e92436664f75e4a3a053f408243abb16) - @RogerSelwyn
- [Rename device to entity](https://github.com/RogerSelwyn/O365-HomeAssistant/cpmmit/fcab07dc520e9e09c876ea3c6e1ecc81b83ea67b) - @RogerSelwyn
- [Bump to v3.1.0](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/0d1032c8855ed439c28e32f3c8267bbf5b0badf6) - @RogerSelwyn
- [Sourcery recommended code change](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3f086fe7184276698d0e9d685a99b81debba89fd) - @RogerSelwyn

## v3.0.1 (2022/05/02)
### Fixes
- [Fix photo embedding](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/2b26133711c3f87e614b13c66799f9a7ff164f0c) - @RogerSelwyn
 
### Maintenance
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b5fb1f35dad975d3a939b4ec71a8c2e436d3c279) - @RogerSelwyn
- [Updated README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/912272b3c276a71b2944f728d4d18325864a589b) - @GitHubGoody
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7566dc035955c087a7e23f9ca69a20698fc288d8) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/e95504f2bc74abbdb4ae62b0ac6e460e0ec6b01f) - @RogerSelwyn
- [Create FUNDING.yml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4b7b9038b8aaacd76d27a403d3c79f09f08876af) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3962a234aa2800e412af63df496f48f264803846) - @RogerSelwyn
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8e78e2423f199f75abdacbc137c95629e301d032) - @actions-user

## v3.0.0 (2022/04/17)
### Enhancements
- Support for multiple accounts
- Reduced permissions requirements for multiple accounts style config
- Enable use of Entity_ID instead of Calendar_ID for service calls (mandatory for multi-account)
- Complete list of changes - [#26](https://github.com/RogerSelwyn/O365-HomeAssistant/pull/26)

## v2.4.1 (2022/03/30)
### Fixes
- [Fix validation of service data and improve attachment handling](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/adbe61de8e8bd0b6b4f91fc8f400d519e8072bdd) - @RogerSelwyn
- [Fix for breaking change in HA](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4d616e96e8f6c59a8a208e07641261dbac736fdb) - @RogerSelwyn
- [Correct handling for DST](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/f7bcf29ec621b7fbc474f7d6663f8e633218ba8c) - @RogerSelwyn

### Maintenance
- [Sourcery code improvements](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3983c3ab9a84f52a4213922f625ed66309a1d568) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d98a34d248faa04c1615924b5324d4efe1bed243) - @RogerSelwyn
- [Bump to v2.4.1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8e1f585def6ee1ab433e69438d47e69ed79eb511) - @RogerSelwyn

## v2.4.0 (2022/03/07)
**Note:** This release has a radical change to the permissions structure to reduce the scope of the permissions requested. To further reduce the permissions please set 'enables_update' to False in your configuration. This will disable the various update services and remove the request for write access to calendars and send access to mail.

### Enhancements
- [Initial change to permissions](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/0d3eeb064745b0d70a75893ea31b2cbf76200500) - @RogerSelwyn
- [Add 'enable_update' switch so update capability can be disabled.](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8ceccffec922caf95fdb82ee2d94813e4118b6e8) - @RogerSelwyn

### Fixes
- [Remove extraneous error](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/f0adb5067c6fde20c6d4b750f6c9018685695d2f) - @RogerSelwyn

### Maintenance
- [Move more of calendar and sensor to async](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/becf8454a60aab3cc50a3c38ff92715a064f3263) - @RogerSelwyn
- [Remove the already deprecated YAML Calendar configuration](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/6cb631078b628e6bf4dd0b67adb2232ef6430f39) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1bbc3e4627d66a4b62a147b0a7a65a702d41d5c2) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1832b3094a7064e1652df34a1042dbb752210e5b) - @RogerSelwyn
- [Code tidy up](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4ffaf6779057b0a694a00e89467c679a48128cfa) - @RogerSelwyn
- [Bump to v2.4.0](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/9d2cb2744daa06798a1a846497bef91f60851f5b) - @RogerSelwyn


## v2.3.1 (2022/02/12)
### Enhancements
- [Add ability to stop dowloading of attachments (to increase performance)](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/37ad1b7cb6b6aeb1de0b7a17216719311a9b5407) - @RogerSelwyn

### Maintenance
- [Update CHANGELOG.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/28c7da2c7d2e2de5bd57e8219592e2f4f6eb4bce) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/55360e0c2a559501304c5c8fe83b4a58a25def30) - @RogerSelwyn
- [Minor code tidy up](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/a14564d46e8c6ce70e1f4f2f6c0acc0dafd8dd34) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8d75bc665389feb4f9ab55ea664f374853974e0c) - @RogerSelwyn
- [Bump to v2.3.1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/32eb8d0140bf5763d365ec36a45ee02f09a77b73) - @RogerSelwyn

## v2.3.0 (2022/02/11)
### Enhancements
- [Add Teams Presence Sensor](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/a92a0a66cc140bca33fcbc81593e52579d1efa21) - @RogerSelwyn

### Fixes
- [Fix storing of o365_calendars.yaml to store/retrieve from config directory](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7ccc053beb6b0aed88d4005570ec7ff2e2241e35) - @RogerSelwyn
- [Fix storing of token in the config directory](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/42a2f3fa38d433b00d8271ce1eef8ed434ea2d3a) - @RogerSelwyn

### Maintenance
- [Update CHANGELOG.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/323b3396c61817f4f354c938a068c1d72ebc0bb1) - @RogerSelwyn
- [Bump O365 to 2.0.18.1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/57dc3ded8231cd0243f5c9757d74af4746681efb) - @RogerSelwyn
- [Code tidy up to remove redundant code](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1e95e1dc00dcfa6a3ddbb936c7748adb4418b240) - @RogerSelwyn
- [Pylint code improvements](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4e5f2f7a19cc193a448a7e8c3ffa40d8d35964d0) - @RogerSelwyn
- [Code simplification from sourcery](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/5734711729d017a08e19f86b120049314d3e99d0) - @RogerSelwyn
- [Bump to v2.3.0](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3fd836647092e0d1f1c8de5e8508dda71e345326) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/55a592bfad9dba11b3ed0caaf456a8d8842d5015) - @actions-user

## v2.2.8 (2022/02/02)
### Maintenance
- [Bump o365 from 2.0.16 to 2.0.17](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/66f669314668130d78c81568f5edad520c50b456) - @dependabot[bot]
- [Update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d465d61c1bb3aef551f35b1acbf262668389871d) - @RogerSelwyn
- [Bump to v2.2.9](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b236ab93c2594f5af6f8cb1e88019af0b071dec3) - @RogerSelwyn

## v2.2.8 (2022/01/19)
### Enhancements
- [Add importance as query filter](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/cf1055bca377c2dc42fd5337693b88fc305a4b0e) - @RogerSelwyn

### Fixes
- [Fix issue with no events retrieved if none in next 24h](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/80e99833d7aada408911c7ac7d878530f62a83a4) - @RogerSelwyn - [#13](https://github.com/RogerSelwyn/O365-HomeAssistant/issues/13) 
- [Fix error with filter not including receivedDateTime](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/26fcb30be5be22c84f66b7e8297ae66776eeacbe) - @RogerSelwyn

### Maintenance
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/ca2b3190c6fd80c904a7129c530471f0709a768a) - @RogerSelwyn
- [Documenation clarifications](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/aab090a53b65e01cde91aebd01dfe7c406d5587a) - @uSlackr
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4cfb23620b7466dd38278496c8bd1d705b0466a5) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d1d231192ea7f0a870be8730afbf38ef58c20dcc) - @RogerSelwyn
- [Bump to 2.2.8 Beta 1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/c5cef0214a8db234bdfc0f0a193f3fa9a277f775) - @RogerSelwyn
- [Revert "Bump to 2.2.8 Beta 1"](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/19829afe5bdfcc441e775fb334115f4eb90a3439) - @RogerSelwyn
- [Bump to 2.2.8 Beta 1](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/beafec4c46923a1aa290aed5a02374bd41d567aa) - @RogerSelwyn
- [Bump to 2.2.8 Beta 2](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/726ac8c03dac1e49beb0cd7869b506c69f07cc5d) - @RogerSelwyn
- [Simplify Code](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/14a1f1945a2147d2e1633a785f0d761c323ac578) - @RogerSelwyn
- [Remove duplicate code](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b917935c6f572f43b2045ff3cff30bcc3514a104) - @RogerSelwyn
- [Bump to 2.2.8 Beta 3](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1c3a4f3e034f6a554f4fd032933db7deab8e6307) - @RogerSelwyn
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/c8d28ff0da03651e7d2ce964a235b3467f6a70a1) - @actions-user

## v2.2.7 (2021/12/12)
### Fixes
- [Fix device_state_attributes warning](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/4ba056b01c8dcc824cd39256d0751009ce49740a) - @RogerSelwyn

### Maintenance
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/25a9e248362042daa0fad8541ea77f17c82f9a59) - @RogerSelwyn
- [Bump to 2.2.7](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/674d398e5af1c92764e270c15e6a28d085c9715a) - @RogerSelwyn
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/296fc51bad89cc0f57ad32c04e0f9bcbd91d8530) - @actions-user

## v2.2.6 (2021/09/28)
### Fixes
- [Fix incorrect handling of all days events](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/a8d02bf63e727f27e32ac88f3295e4ba2df3643c) - @RogerSelwyn - [#6](https://github.com/RogerSelwyn/O365-HomeAssistant/issues/6) 

### Maintenance
- [Remove unrequired iot_class](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d56fcf68832979a82df7de4de732f417c438f409) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/1ea49358593dddf588c261075ddb8365a58c8e20) - @RogerSelwyn
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/03a9de89f00a1718840c1b9df397d10b4609b686) - @actions-user
- [Handle beta releases](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/24202179acaba12bfd49423e286717aaf5830e98) - @RogerSelwyn
- [Update to use rogerselwyn/actions](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/ae2b49790fbc462e2562b00d15408515190ef411) - @RogerSelwyn
- [Correct step name in release](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/ddd085f8f8db38b84c7c42ad8b7d6598afd65bed) - @RogerSelwyn
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b1d575622660e866a2a743c9e08426d9c82be469) - @actions-user


## v2.2.5 (2021/09/13)
### Fixes
- [Prefer external url for authentication over internal](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/5a949bb78b20c80e69994537c9774b614f2e3e09) - @RogerSelwyn - [#5](https://github.com/RogerSelwyn/O365-HomeAssistant/issues/5) 

### Maintenance
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/6c1f569be2d846748c9ec7039704b0537462555f) - @RogerSelwyn
- [Bump o365 from 2.0.15 to 2.0.16](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/01f4124e4f2a6b99d24cfdead8f3f3376e0da8cc) - @dependabot[bot]
- [Bump to 2.2.5](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b1957443ade157614a84492e953905e718d318a7) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/76c1fc94b654c02e5bd7eef02d72750c308bf8c1) - @actions-user

## v2.2.4 (2021/09/12)
### Maintenance
- [Update for recommendations by sourcery](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/475cc4de0a5624dc9e320afaca44c16e6b184663) - @RogerSelwyn
- [Code recommendations from codefactor](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d290dadfe7e67e53bb3bb15a7e04d3b892168f31) - @RogerSelwyn
- [Bump to 2.2.4](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7315271fed296d60c67f51848aac808c0167181c) - @RogerSelwyn

## v2.2.3 (2021/09/10)
### Maintenance
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/2aaad7bcb86ddd5c700c59b171c2866f6e6b7c3b) - @RogerSelwyn
- [Create dependabot.yml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/601fce70844b150ea5c8bf1d1f654a8e35e52e99) - @RogerSelwyn
- [Correct dependency versions](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/48d0634123cb30ad878b8c2565af911760e964ec) - @RogerSelwyn
- [Bump to v2.2.3](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/792872bdf9db8adf8fb9028f83d10068a6871cfa) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/973c13e500a55d6d7b11856f3c2cb85dd376e1bc) - @actions-user

## v2.2.2 (2021/09/09)
### Maintenance
- [Change code owner](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/c31333fd0b9fd8115f92a776e025b9d78bc5b07b) - @RogerSelwyn
- [Update update_version.py](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/e47746b0055a11870b4bd106681cf3c201d9451c) - @RogerSelwyn
- [Update CHANGELOG.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/6326d079b97c52f91d60f9de2a6b96894a56402c) - @RogerSelwyn
- [Correct hacs.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/61edff5bcb2a32463d8c3d32ae5bd7791ced912a) - @RogerSelwyn

## v2.2.1 (2021/09/07)
### Fixes
- [Fix issue with authentication I/O within the event loop](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/2dfa7859c1a29f775965b3d73b323093bb8848db) - @RogerSelwyn

### Maintenance
- [Deconstrain requirements](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3a546ec608eb07bfdca22645481911ad41a8b43b) - @RogerSelwyn
- [Correct version](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7631c0a4a64f55d198a4b0cda1ba7db2bad766d8) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/f4690f8a133c652cdaa15f95c62f6d15bf7d4c03) - @actions-user

## v2.2.0 (2021/09/06)
### Maintenance

- [Updated to remove deprecation warning on base_url use](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/afb9e98203c405cfdb41b98c3bb46aedc946279f) - @RogerSelwyn
- [Fix for all day_event](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/debf019e085d445fae1749f31c872592bd32ad7d) - @PTST
- [Now actually implements the offsets](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3fc4c9af68435156e77e03cf0aaf97bfbd2d20a8) - @PTST
- [Black formatting](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d61a26d607ff080b880d02854de4476cbeec9587) - @PTST
- [Update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/619c733475e5814048f2c76edf7d39d1fcbaab08) - @RogerSelwyn
- [Create o365release.yaml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b1182ff33b58a1c02217cc43bc75fedaf0314f70) - @RogerSelwyn
- [Create pushpull.yaml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/0a8579b265c123c0dbaac5351561ba90d0ec68f4) - @RogerSelwyn
- [Create pushpull.yaml](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/ecd897fb82385776f516a9d7a725303f1932e13d) - @RogerSelwyn
- [Move](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/ab2ed7b96927b54da4ea3f9871c643b9a8205680) - @RogerSelwyn
- [Update .gitignore](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/881f10baf9e727cf719ab26814d80736204b52b5) - @RogerSelwyn
- [Add management components](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/0087c426a2613ad037a3ac078e5776cf2b8ece55) - @RogerSelwyn
- [Update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/b53202150473153c6f94ad833784fe14bfa03e01) - @RogerSelwyn
- [Hassfest corrections](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/7a3afd87b4d103377c573e3f9b399d671fc3c432) - @RogerSelwyn
- [Auto update requirements.txt](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/8a1633a88ea1ba803b8cddc265dad6a561c51f17) - @actions-user
- [Auto update manifest.json](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/e0421b126d600503a97174e511078ddf804c3331) - @actions-user
- [Split workflows](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/14ab44459088a7c76d29f7a11e9fbb3858128256) - @RogerSelwyn
- [Update README.md](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/262b82f9648cb705eefd37b9ccbab7edbed77b02) - @RogerSelwyn


## Earlier
### Maintenance
- [Updated to remove deprecation warning on base_url use](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/afb9e98203c405cfdb41b98c3bb46aedc946279f) - @RogerSelwyn
- [Fix for all day_event](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/debf019e085d445fae1749f31c872592bd32ad7d) - @PTST
- [Now actually implements the offsets](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/3fc4c9af68435156e77e03cf0aaf97bfbd2d20a8) - @PTST
- [Black formatting](https://github.com/RogerSelwyn/O365-HomeAssistant/commit/d61a26d607ff080b880d02854de4476cbeec9587) - @PTST


