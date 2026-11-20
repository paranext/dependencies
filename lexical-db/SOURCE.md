# Source

## Technical Source

The DB files in this directory should be coming from the results of running https://github.com/paranext/marble-tools/actions/workflows/build-english-db.yml. The English DB file is saved here as lexical.db, and the file is compressed using `xz` to save download bandwidth.

`build-info.json` says which build the current `lexical.db.xz` is: the marble-tools and marble-lexicon commits it was built from, the workflow run, and the sha256 of the decompressed `lexical.db`. The database was compressed with `xz -9e -T0 -k lexical.db` (XZ Utils 5.8.4); other thread settings (`-T1`) produce different bytes.

To update the DB:

1. Download the `english-database` artifact of a successful workflow run on marble-tools `main`. It holds `english.db` and `build-info.json`.
2. Rename `english.db` to `lexical.db` and compress it with `xz -9e -T0 -k lexical.db`.
3. Create the checksum file:

   ```
   sha256sum lexical.db.xz > lexical.db.xz.sha256
   ```

4. Copy `lexical.db.xz`, `lexical.db.xz.sha256` and the artifact's `build-info.json` into this directory. If your `xz` version differs, update it above.
5. The `Check lexical DB` workflow checks that the database matches both files and that `build-info.json` names a marble-tools commit on `main`. You can run it locally with `python3 .github/scripts/check_lexical_db.py`.
6. In paranext-core, change the dependencies commit that `extensions/src/platform-lexical-tools/lib/download-db.ts` downloads from to the commit that publishes the new database.

## Data Source

The DB files are generated from private MARBLE repos in the https://github.com/ubsicap organization. Thanks to Reinier de Blois in particular for his help in adapting the data to work with Paratext.

Copyright information below is copied from https://github.com/ubsicap/ubs-open-license. See that URL for the latest.

UBS Dictionary of Biblical Hebrew
© United Bible Societies, 2026. Adapted from Semantic Dictionary of Biblical Hebrew © 2000-2026 United Bible Societies
Licensed under CC BY-SA 4.0

UBS Dictionary of the Greek New Testament
© United Bible Societies, 2023. Adapted from Semantic Dictionary of Biblical Greek: © United Bible Societies 2018-2023, which is adapted from Greek-English Lexicon of the New Testament: Based on Semantic Domains, Eds. J P Louw, Eugene Albert Nida © United Bible Societies 1988, 1989
Licensed under CC BY-SA 4.0

Portions of the DB file are © United Bible Societies and not available under an open source license. They are permitted for distribution in Paratext. To obtain a copy of the open source content, go to https://github.com/ubsicap/ubs-open-license.
