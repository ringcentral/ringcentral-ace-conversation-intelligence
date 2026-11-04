# Install and keep the plugin up to date

Use this guide when a user asks an agent to install **RingCentral ACE - Conversation Intelligence** from its GitHub link. Follow the steps for the user's target app and use **main** as the update source.

## Installation settings

| Setting | Value |
| --- | --- |
| Repository | `https://github.com/ringcentral/ringcentral-ace-conversation-intelligence` |
| Branch / Git ref | `main` |
| Marketplace | `ringcentral-ace-conversation-intelligence` |
| Plugin ID | `ringcentral-ace` |
| Plugin selector | `ringcentral-ace@ringcentral-ace-conversation-intelligence` |
| Folder / Path / Sparse paths | Leave empty; the catalogs are at the repository root |
| MCP service | `https://mcp.ace.ringcentral.com/mcp` |
| Authentication | RingCentral sign-in through the client's connection flow |

The user needs a RingCentral account with [AI Conversation Expert](https://www.ringcentral.com/products/ai-conversation-expert), access to the interactions they want to analyze, and plugin access in their AI app. Use the Git marketplace for ongoing updates; a downloaded ZIP is a snapshot.

## Agent checklist

1. **Identify the target.** Use the app and account the user requested. If ambiguous, ask which app to configure. A terminal in a remote environment does not necessarily configure the user's desktop app.
2. **Inspect before installing.** Check the client version, available plugin commands, existing marketplace source, installed version, and enabled state. Use the client's tools or `--help`; retain existing plugins and settings.
3. **Configure this marketplace.** Set the source to this repository and the ref to `main`. Reuse a matching installation. If it follows another ref, use the client's supported source-edit flow and verify the result. Do not remove a marketplace as a shortcut: removal can uninstall its plugins.
4. **Install and turn on the plugin.** Use the matching client flow below. Let the package supply the MCP configuration; do not add a duplicate standalone MCP server or ask the user for an API key.
5. **Set up updates.** Turn on the client's supported automatic update or sync control for this marketplace. Inspect its saved state. If the control is unavailable or company-managed, report the exact user or company-admin action needed.
6. **Connect and verify.** Let the user complete RingCentral sign-in and consent in the client. Start a new session or use its supported reload action, then follow the verification checklist below.

Use available installation tools to carry out the authorized setup. If your environment can only read this guide, give the user the relevant app steps and report setup as pending. Keep credentials in the client's authentication flow.

## Claude

**Desktop or web:** Open **Customize → Plugins → Add → Add marketplace**, enter the repository source, and sync. Choose `main` if the client exposes a branch field; otherwise verify the source uses the repository's default branch, `main`. Install **RingCentral ACE - Conversation Intelligence**, then connect RingCentral from the plugin's **Connectors** tab. [Claude installation help](https://support.claude.com/en/articles/13837440-use-plugins-in-claude).

For an organization-managed marketplace, a company admin can configure GitHub sync and keep **Sync automatically** on where available. Verify the sync status and installed version. Organization sync may require repository access the customer does not have; use the permitted personal marketplace flow or report the admin action needed. [Claude organization sync](https://support.claude.com/en/articles/13837433-manage-plugins-for-your-organization).

**Claude Code:** Inspect current state first:

```sh
claude plugin marketplace list --json
claude plugin list --json
```

For a new installation:

```sh
claude plugin marketplace add "ringcentral/ringcentral-ace-conversation-intelligence#main"
claude plugin install ringcentral-ace@ringcentral-ace-conversation-intelligence --scope user
```

In a Claude Code session, open `/plugin`, select **Marketplaces**, select this marketplace, and choose **Enable auto-update**. Third-party marketplaces start with auto-update off. Updates apply to a new session or through `/reload-plugins` after an update notification. Check the state again after changing it. [Claude update controls](https://code.claude.com/docs/en/plugins/install#turn-auto-update-on-or-off-for-a-marketplace).

Installing through the terminal configures Claude Code; verify the desired desktop or web installation separately. [Claude command reference](https://code.claude.com/docs/en/plugins/cli-reference).

## ChatGPT & Codex

**App marketplace:** Open plugin marketplace settings, add the repository, enter **main** in **Git ref** or **Branch, tag, or commit**, and leave optional paths empty. Install and turn on the plugin, then connect RingCentral. Use the client's available marketplace update controls and verify the settings you actually saved.

**ChatGPT workspace import:** An authorized company admin can open **Admin → Plugins → Add → Import marketplace**, enter the repository URL, leave **Path** empty, and set the branch to `main`. Imported marketplaces check for updates daily; **Sync now** requests an immediate refresh. Confirm the workspace allows the plugin and its required connection. Workspace import and a local Codex installation are separate setup steps. [ChatGPT GitHub sync](https://learn.chatgpt.com/docs/enterprise/plugin-management).

**Codex CLI:** Inspect current state first:

```sh
codex plugin marketplace list --json
codex plugin list --json
```

For a new installation:

```sh
codex plugin marketplace add ringcentral/ringcentral-ace-conversation-intelligence --ref main
codex plugin add ringcentral-ace@ringcentral-ace-conversation-intelligence --json
```

Use an automatic-update control if the installed client exposes one, and verify its saved state. The CLI commands checked for this guide provide a marketplace refresh command, not an auto-sync switch. If no supported automatic control is available, report **manual refresh required** and use the refresh procedure below. Do not claim ChatGPT workspace daily sync applies to a local Codex marketplace. [Codex commands](https://learn.chatgpt.com/docs/developer-commands#codex-plugin).

## Verify and report

Check that the marketplace follows `main`, the plugin is installed and enabled, and RingCentral is connected. After reloading, confirm the plugin's skills and tools are available. For a small read-only check, use its getting-started skill to answer:

> What conversation insights are available to me?

Follow the installed skill and tool schemas, and access only the signed-in user's permitted data. An installed package is not proof that authentication or tool calls work. Report empty data accurately; do not request broader permissions just to obtain a nonempty result.

Finish with a short status report:

| Check | Report |
| --- | --- |
| App | Target client and version |
| Source | Repository, `main`, and resolved revision if available |
| Plugin | Installed version and enabled state |
| Updates | Verified automatic setting, managed daily sync, manual refresh required, or pending verification |
| Connection | Connected or sign-in needed |
| Verification | Actual tool check result, or why it remains pending |
| Next step | Any specific action the user or company admin still needs to take |

## Updates and recovery

If you installed a preview with the plugin ID `ace`, refresh the marketplace and install `ringcentral-ace@ringcentral-ace-conversation-intelligence` using the steps above. Clients may treat it as a new plugin and ask you to reconnect RingCentral. Verify the new plugin works, then remove the old `ace` plugin through the client to avoid duplicate skills and tools. Customer-facing names are unchanged.

Keep `main` selected; version tags and fixed commits stay pinned. Native client refresh and session reload determine when changes become usable. Publishing a GitHub release alone does not establish that an installed client has updated.

To refresh Claude Code and the installed plugin:

```sh
claude plugin marketplace update ringcentral-ace-conversation-intelligence
claude plugin update ringcentral-ace@ringcentral-ace-conversation-intelligence
```

For Codex, refresh this marketplace, then inspect the installed and available versions:

```sh
codex plugin marketplace upgrade ringcentral-ace-conversation-intelligence --json
codex plugin list --marketplace ringcentral-ace-conversation-intelligence --json
```

Refreshing the Codex catalog alone is not proof that the installed package changed. If it remains behind, use the client's supported update or reinstall action for this plugin and verify again. Avoid editing cache files or creating background update jobs. For managed marketplaces, check the sync result and use **Sync now** or **Re-sync** when available. If sign-in has expired, reconnect through the app. For account access, contact the company admin; for integration help, use [RingCentral Developer Support](https://developers.ringcentral.com/support/create-case).
