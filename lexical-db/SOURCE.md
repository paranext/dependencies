# Source

## Technical Source

The DB files in this directory should be coming from the results of running https://github.com/paranext/marble-tools/actions/workflows/build-english-db.yml. The English DB file is saved here as lexical.db, and the file is compressed using `xz` to save download bandwidth.

The current `lexical.db.xz` was built from marble-lexicon `9467a4f` (2026-11-13) by marble-tools `cd99615` ([paranext/marble-tools#10](https://github.com/paranext/marble-tools/pull/10)), workflow [run 44412514796](https://github.com/paranext/marble-tools/actions/runs/44412514796). The decompressed `lexical.db` has sha256 `9a9d10103efd803e03e4ed7436aa5d1df8522f7c54e3c29bab117bc42c926b8b`; it was compressed with `xz -9e -T0 -k lexical.db` (XZ Utils 5.8.4). Other thread settings (`-T1`) produce different bytes.

To update the DB:

1. Download the `english-database` artifact of a successful workflow run on marble-tools `main` and rename `english.db` to `lexical.db`.
2. Compress it with `xz -9e -T0 -k lexical.db`.
3. Create the checksum file:

   ```
   sha256sum lexical.db.xz > lexical.db.xz.sha256
   ```

4. Update the paragraph above: the workflow run and its marble-tools commit, the marble-lexicon commit and the decompressed DB's sha256 (both in the run's summary), and the `xz` command and version.

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
