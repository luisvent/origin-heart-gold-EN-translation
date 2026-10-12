# Releasing

How a version (release candidate or final) goes out. Everything is done from the **developer account**
(`originheartgold`): git over the `github-originheartgold` SSH alias, and the GitHub **web UI** for the release page.
Do not use the `gh` CLI: it is logged in with a personal account.

The patch can't be built in CI (it needs the USA and Chinese ROMs, which never leave your machine), so a release is
half local, half CI. ROMs, saves and build inputs are never uploaded: only the xdelta, README and metadata.

## 1. Prepare (local)

1. Set the notice version: `Current version: 4.0.3-RC<N>` in `work/translate/banks/a027/0816.json`, string 4
   (see [CONTRIBUTING.md](CONTRIBUTING.md#release-notice-version)). It is embedded in the ROM; the release tag does not change it.
2. Add a `## [<version>] - <date>` section to `CHANGELOG.md` (e.g. `## [1.0.0-rc8] - 2026-10-20`). It becomes the release notes.
3. Build, run the gates (`python3 work/tools/check.py --full --strict-release`) and verify the xdelta round-trip.
4. Package into `work/release/<tag>/` (gitignored): the `.xdelta`, `README.txt` (with the `Result ROM SHA-1:` line) and, optionally, the ZIP and `SHA256SUMS.txt`.
5. Write `latest.json` for the website's in-browser patcher: `python3 work/tools/site/patch_manifest.py <tag>`.
6. Commit the version bump and CHANGELOG, and merge to `main`.

## 2. Tag (triggers CI)

```
git tag v1.0.0-rc8        # on the commit you built from
git push origin v1.0.0-rc8
```

`.github/workflows/release.yml` then:
- fails if `CHANGELOG.md` has no matching `## [<version>]` section, or (for `-rcN` tags) if `a027/0816.json` doesn't say `Current version: 4.0.3-RC<N>`;
- creates a **draft** release titled `<version>` with the CHANGELOG section as its notes (nothing happens if the release already exists).

Check the run under *Actions → Release*. If it failed, fix the file, then move the tag
(`git tag -f v1.0.0-rc8 && git push -f origin v1.0.0-rc8`) and the workflow reruns.

## 3. Upload and publish (web UI)

1. *Releases* → open the draft → **Edit**.
2. Drag in from `work/release/<tag>/`: the `.xdelta`, `README.txt`, **`latest.json`** (without it the website patcher stays off), and the ZIP if you made one.
3. Check the notes, tick **Set as the latest release** (or *pre-release* if you want it kept out of "Latest"; rc7 was a normal release).
4. **Publish release.**

Publishing triggers `site.yml` (`release: published`), which downloads `latest.json` and the xdelta, verifies the SHA-1 and redeploys `/patch/`.
Check that run, then open the patch page and try it.

## 4. After

- Confirm the downloaded xdelta applied to a clean USA ROM gives the `Result ROM SHA-1` in the README.
- Announce (Discord / Reddit thread) with the CHANGELOG section.
