# Changelog

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


