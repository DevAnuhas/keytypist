# Fork identity and first-run safety

The app is KeyTypist (`dev.anuhas.keytypist`); internal Swift modules retain TabType names. Keep the isolated identity and storage boundaries below when changing startup or distribution.

## Existing coupling to inspect

- `Resources/Info.plist`: display/executable/bundle identifiers.
- `Scripts/build.sh`, `Scripts/setup-signing.sh`, `Scripts/release.sh`: output names, signing certificate label, identifier and release packaging.
- `Sources/TabType/App/Updater.swift`: only the pinned KeyTypist feed and public key may activate Sparkle. Test processes remain inert.
- `Sources/TabTypeKit/Catalog/ModelCatalog.swift`: the moving upstream catalog endpoint.
- `Sources/TabTypeKit/Catalog/ModelStore.swift`, `Sources/TabType/Core/WritingStore.swift`, settings/statistics/logging: Application Support and preference namespaces.
- `Sources/TabType/App/SyncManager.swift`: `app.tabtype.sync` Keychain service and `TabType Sync` iCloud Drive folder.
- `Sources/TabType/Core/ScreenContextProvider.swift`: own-app exclusion list.
- User-facing views, URLs, icons and menu text. Preserve upstream attribution and third-party licenses even after rebranding.

## Intended boundary

Use `KeyTypist` as the working display/bundle output name and a distinct application identifier, provisionally `dev.anuhas.keytypist`. Keep internal Swift module names if renaming them creates unnecessary risk. The signer may require a different final identifier; verify it before distribution.

Give the fork its own Application Support, preferences, Keychain service and cloud-sync namespace. Do not silently read, migrate, overwrite, delete or synchronize TabType/Cotypist data. Import, if added later, is explicit and reversible. Models may be large; do not duplicate or move another app's installed weights without permission and license checks.

Disable inherited automatic updates until a KeyTypist-owned distribution source and publisher verification exist. Repointing a URL alone is not enough: asset naming, bundle identity, checksum, signing trust and recovery must agree. A new fork with no releases must show a benign no-update state, not install an upstream TabType build.

Choose whether to pin or own the remote model catalog; do not inherit unreviewed future catalog changes silently. Preserve model-license notices and download verification.

For local development, use a distinct stable development signing identity rather than borrowing `TabType Dev`. Do not import or share private signing keys. Self-signing can support stable local identity, but does not establish Developer ID signing or notarization.

## Evidence required

- Static test/check of all product identity, update and storage endpoints; intentional attribution strings may still mention TabType.
- Real Mac build with bundle metadata and signature readback.
- Coexistence test using synthetic stores: the other apps' files/settings remain unchanged.
- Fork updater tests for no release, wrong application/publisher, bad checksum and failed replacement.
- Relaunch/rebuild permissions behavior recorded; no promise that the old app's grants transfer to a new bundle identity.

The production app uses these isolated namespaces. In-app updates require a signed KeyTypist feed, EdDSA archive verification before extraction, and Developer ID verification; the [release runbook](runbooks/releasing.md) owns publishing instructions.

## Rename history: KeyWeave to KeyTypist

The product was renamed from KeyWeave to KeyTypist after 2.4.0, including the bundle identifier (`dev.anuhas.keyweave` to `dev.anuhas.keytypist`) and the GitHub repository (`DevAnuhas/keytypist`; GitHub redirects the old path, so never create a new repository named `keyweave`).

- The rename moved every namespace: Application Support, Caches, Logs, preferences, the `dev.anuhas.keytypist.sync` Keychain service, the `Keytypist Sync` iCloud folder and `.keytypistsync` files. Nothing is migrated from KeyWeave, TabType or Cotypist automatically. A KeyWeave user's models, settings and learned writing stay in the old locations until an explicit, reversible import exists.
- macOS treats KeyTypist as a new app: Accessibility, Input Monitoring and Screen Recording must be granted again.
- Release 2.4.0 and earlier stay published as KeyWeave. Their signed, notarized assets are not renamed; `Scripts/appcast.py` pins the 2.4.0 feed entry to its original `KeyWeave-2.4.0-arm64.dmg` URL (`FORMER_NAME_RELEASES`). Git tags (`v*`) never contained the product name and are unchanged.
- The Sparkle EdDSA public key is unchanged and the private key stays in the login Keychain under the legacy account label `dev.anuhas.keyweave.sparkle`. Relabeling it would orphan the key.
- Installed KeyWeave copies still read the feed at the old raw URL, which redirects to the new repository. Whether Sparkle will install an update across a bundle-identifier change is **unverified**; tell KeyWeave 2.4.0 users to install KeyTypist manually and test the upgrade path before relying on in-app update.
