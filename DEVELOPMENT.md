# Maintaining the plugin

This repository contains the installable packages for **RingCentral ACE - Conversation Intelligence**. See [README.md](README.md) for installation and examples, and [INSTALL.md](INSTALL.md) for the agent installation and update checklist.

## Layout

| Location | Contents |
| --- | --- |
| `plugin-manifest.json` | Shared public identity, version, descriptions, and listing metadata |
| `mcp-manifest.json` | Shared connection and client authentication settings |
| `marketplace.json` | Shared marketplace identity and publisher metadata |
| `skills/` | Readable definitions for the six skills |
| `shared-references/` | Shared guidance used by the skills |
| `assets/` | Shared plugin artwork |
| `plugins/claude/` | Claude manifest, MCP connection, skills, references, assets, README, and MIT license |
| `plugins/openai/` | ChatGPT/Codex manifests, MCP connection, skills, references, assets, README, and MIT license |
| `.claude-plugin/marketplace.json` | Claude marketplace catalog |
| `.agents/plugins/marketplace.json` | ChatGPT/Codex marketplace catalog |
| `scripts/` | Package validation, archive creation, and release preparation |
| `dist/` | Locally built ZIPs and checksums; excluded from Git |

The public display name is **RingCentral ACE - Conversation Intelligence**. Keep the technical plugin ID and MCP connector key `ringcentral-ace` stable. Both catalogs use `ringcentral-ace-conversation-intelligence`. Each package includes its own skills and references so it can be installed independently.

## Validate and build

Use Python 3.12 and the Claude Code version recorded in `.claude-code-version`.

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements-dev.txt
python scripts/plugin_repo.py check
claude plugin validate ./plugins/claude --strict
claude plugin validate . --strict
python scripts/plugin_repo.py build
```

Validation downloads the official Agent Plugins 1.0.0 schemas from a fixed upstream commit and verifies their SHA-256 checksums. Network access to `raw.githubusercontent.com` is required; download failures or checksum mismatches stop validation. Schemas are kept only in memory for the current process and are not bundled in this repository or plugin packages. Customer installation does not run this validator.

Checks cover manifests, matching versions and shared content, skill references, listing links, assets, licensing, and safe package paths. Building creates reproducible ZIPs and `SHA256SUMS` from the validated packages.

Keep the root skills, references, assets, and JSON files aligned with both packages and catalogs. Package validation checks these copies for consistency. When updating the root README, update each package README too; package copies link to the public development guide on GitHub. Preserve client-specific manifest formats and OpenAI skill metadata.

Optionally install a local Git hook:

```sh
python scripts/plugin_repo.py install-hooks
```

The hook validates staged files without editing or staging them. Existing hook configurations are preserved. GitHub CI validates pull requests and pushes to `main`, checks the Claude package and catalog, and builds the downloadable artifacts. Both workflows use Ubuntu 24.04 LTS, Node.js 24.22.2, and GitHub Actions pinned to immutable commits with the Node.js 24 runtime. Keep these pins current with supported security releases; the runner image and the runtime bundled with GitHub Actions are maintained by GitHub.

## Client-specific listing metadata

Portable MCP configuration follows the [official Agent Plugins 1.0.0 schema](https://agent-plugins.org/schemas/1.0.0/mcp.schema.json): the ACE server uses `type: "streamable-http"` and its HTTPS `url`. Validate the complete file without stripping unknown fields. Per-server `extensions.com.openai.auth` is described by current OpenAI packaging guidance, but is excluded by that schema and rejected by Codex 0.165.0. OAuth remains discovery-driven through the service's challenge and authorization metadata, including dynamic client registration and PKCE. Keep legacy callback settings in `.mcp.json`. Verify connector discovery with the actual target client as well as package checks.

The Claude Git-distributed manifest intentionally omits `documentationUrl`, `icon`, `privacyPolicyUrl`, `supportUrl`, and `termsOfServiceUrl`. Claude's Desktop/web marketplace sync importer strips those fields and reports warnings. Keep `homepage` in the manifest and product, support, privacy, and terms links in the README. The package validator rejects reintroducing these fields into this Git-distribution profile.

These are valid fields for [Anthropic directory submissions](https://code.claude.com/docs/en/plugins/manifest-reference#directory-listing-fields); prepare them separately if submitting to that directory. A directory advisory from the local Claude validator is distinct from a Git sync warning.

Keep `plugin-manifest.json` in the standard Codex compatibility shape with a top-level `interface`. The generated `plugins/openai/plugin.json` contains only portable identity metadata and its official schema declaration. Preserve listing links, icons, and starter prompts in `plugins/openai/.codex-plugin/plugin.json`; both OpenAI hosts use that supported compatibility interface when the portable manifest has no inline OpenAI extension. Their supported field names and locations differ from Claude's. Preserve the shared identity, descriptions, skills, assets, and connection settings across the appropriate client formats. Verify cloud sync in Claude after publication; local CLI validation alone does not exercise its cloud importer.

## Installation instructions

Keep `INSTALL.md` as the shared setup guide for humans and agents. `AGENTS.md` routes installation requests there and repository changes here. The README provides a copyable installation request and the two client entry points. Keep its packaged copies aligned when editing it.

Use the GitHub repository's `main` branch for customer installations. Keep the repository's default branch set to `main`. Publish a new package version for changes users need to receive; client caches can retain an installed version even after the branch changes. Verify installed versions and marketplace sync after publishing. For organization-managed Claude marketplaces, check the actual sync result and use **Re-sync** if needed. A release or direct push is not evidence that every client has updated. See the [client-specific update guidance](INSTALL.md#updates-and-recovery).

## Releases

**`main` is the stable distribution branch.** Merge reviewed, validated changes into `main`; add a short customer-facing entry under **Unreleased** in `CHANGELOG.md`.

1. Write the release description under **Unreleased** in `CHANGELOG.md` and merge it into `main`. Keep the Markdown headings and bullets you want users to see.
2. Verify installation, sign-in, a representative query, update, and removal in the supported clients.
3. Open **Actions → Release → Run workflow** and select **main**.
4. Enter a version greater than the current package version, such as **v1.1.0**. Entering `1.1.0` also works.

The workflow uses the Unreleased text as the GitHub release description, without adding commit messages. It moves those notes into a dated `1.1.0` changelog entry and leaves an empty Unreleased section for the next release. An empty Unreleased section stops a new release before files or tags change.

The workflow updates the root plugin manifest and all three package manifest versions to `1.1.0`, validates the packages, and builds the ZIPs. It commits the version changes and atomically pushes `main` and the matching **v1.1.0** tag. It then publishes a GitHub release titled **v1.1.0**, attaches both plugin ZIPs and checksums, and verifies the downloaded assets byte for byte. Version changes happen only when this workflow is run. It does not create or promote a separate distribution branch.

The workflow saves its current release tooling before any older-tag checkout, so retries keep the same publication protections. A concurrent update to `main` rejects the atomic push. If publication fails after the tag is pushed, rerun the same version to resume publication using the notes stored at that tag. The workflow refuses to replace published assets or move an existing tag. Review permission or asset mismatches before retrying.

Configure reviewers for the **release** environment. Normal CI uses read-only repository permissions; only the release job has `contents: write`. Repository rules must permit the approved release identity to update `main` and create tags. The workflow does not bypass or modify those rules.

Git-backed installations tracking `main` receive available changes according to the client's refresh and update settings. A fixed tag or commit stays pinned. Publishing a release does not force an immediate client update.

## Client and directory verification

Static validation does not establish successful RingCentral sign-in or live client compatibility. Record the client and package versions when testing installation, authentication, queries, updates, and removal.

Run the additional public-directory check with:

```sh
python scripts/plugin_repo.py submission-check
```

The agreed display name has 43 characters; the current OpenAI public-listing limit is 30. This check reports that condition without renaming the plugin. Directory submission needs a separate listing-name decision and live-client verification.

Format references: [Claude](https://code.claude.com/docs/en/plugin-marketplaces) · [OpenAI](https://developers.openai.com/plugins/build/plugins).

See [SECURITY.md](SECURITY.md) for private vulnerability reporting.
