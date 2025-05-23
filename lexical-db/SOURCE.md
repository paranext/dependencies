# Source

## Technical Source

The DB files in this directory should be coming from the results of running https://github.com/paranext/marble-tools/actions/workflows/build-english-db.yml. The English DB file is saved here as lexical.db, and the file is compressed using `xz` to save download bandwidth.

To create the checksum file, run:

```
sha256sum lexical.db.xz > lexical.db.xz.sha256
```

## Data Source

The DB files are generated from private MARBLE repos in the https://github.com/ubsicap organization. Thanks to Reinier de Blois in particular for his help in adapting the data to work with Paratext.

Copyright information below is copied from https://github.com/ubsicap/ubs-open-license. See that URL for the latest.

UBS Dictionary of Biblical Hebrew
© United Bible Societies, 2023. Adapted from Semantic Dictionary of Biblical Hebrew © 2000-2023 United Bible Societies
Licensed under CC BY-SA 4.0

UBS Dictionary of the Greek New Testament
© United Bible Societies, 2023. Adapted from Semantic Dictionary of Biblical Greek: © United Bible Societies 2018-2023, which is adapted from Greek-English Lexicon of the New Testament: Based on Semantic Domains, Eds. J P Louw, Eugene Albert Nida © United Bible Societies 1988, 1989
Licensed under CC BY-SA 4.0

Portions of the DB file are © United Bible Societies and not available under an open source license. They are permitted for distribution in Paratext and Platform.Bible. To obtain a copy of the open source content, go to https://github.com/ubsicap/ubs-open-license.
