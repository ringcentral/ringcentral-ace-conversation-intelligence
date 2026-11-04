# RingCentral ACE - Conversation Intelligence

**Turn interactions into business insights.**

Understand your customers, coach your team, and spot opportunities in your business conversations. Ask questions about your analyzed RingCentral calls and meetings directly in **Claude, ChatGPT, or Codex**.

## Included skills

Turn customer conversations into business insights:

- **Conversation briefs:** Find past interactions, prepare for customer calls, and build briefs with key takeaways and next steps.
- **Business insights:** Track call activity, recurring topics, and follow-up completion to spot operational trends.
- **Team performance and coaching:** Compare agents and teams, identify coaching opportunities, and build recommendations backed by real conversations.
- **Voice of customer:** Understand customer sentiment, satisfaction trends, recurring concerns, and issue resolution.
- **Competitive and retention insights:** Identify competitor mentions, customer churn risks, and responses to offers.
- **Getting started:** Discover the data and insights available to you and find useful questions to ask.

## What you'll need

- A **RingCentral account** with the **[AI Conversation Expert](https://www.ringcentral.com/products/ai-conversation-expert)**.
- Access to the interactions you want to analyze.
- A **Claude, ChatGPT, or Codex account** with plugin access.

If your organization manages integrations, your company admin can help you get access.

## Installation

Choose your app below, or ask your AI agent to help you install the plugin.

**Install with your AI agent:** Copy this request into your agent:

```text
Install RingCentral ACE - Conversation Intelligence from https://github.com/ringcentral/ringcentral-ace-conversation-intelligence using the main branch. Follow INSTALL.md, turn on supported automatic updates, help me sign in to RingCentral, and verify the plugin is ready to use. Preserve my existing plugins and settings.
```

[Installation and update guide for agents](https://github.com/ringcentral/ringcentral-ace-conversation-intelligence/blob/main/INSTALL.md)

### Claude

In Claude Desktop or on the web:

1. **Open plugins:** Go to **Customize → Plugins**.
2. **Add the marketplace:** Select **Add → Add marketplace** and paste this repository source:

   ```text
   ringcentral/ringcentral-ace-conversation-intelligence
   ```

   Choose **main** if a branch field is available, leave optional path fields empty, and sync. Turn on automatic updates or sync where available.

3. **Install:** Choose **RingCentral ACE - Conversation Intelligence**.
4. **Connect:** Open the plugin's **Connectors** tab and sign in to RingCentral.
5. **Ask:** Start a new chat and try one of the questions below.

[Claude installation help](https://support.claude.com/en/articles/13837440-use-plugins-in-claude)

<details>
<summary>Install from a terminal with Claude Code</summary>

```sh
claude plugin marketplace add "ringcentral/ringcentral-ace-conversation-intelligence#main"
claude plugin install ringcentral-ace@ringcentral-ace-conversation-intelligence
```

In Claude Code, open `/plugin → Marketplaces`, select this marketplace, and choose **Enable auto-update**. Complete RingCentral sign-in when prompted. [Terminal installation help](https://code.claude.com/docs/en/plugins/cli-reference).

</details>

### ChatGPT & Codex

In Codex or ChatGPT desktop with marketplace access:

1. **Open plugins:** Go to your app's plugin marketplace settings.
2. **Add the marketplace:** Select **Add plugin marketplace** and paste this repository source:

   ```text
   ringcentral/ringcentral-ace-conversation-intelligence
   ```

   Use **main** as the branch or Git ref and leave optional folder and sparse-path fields empty. Turn on automatic updates or sync where available.

3. **Install:** Choose **RingCentral ACE - Conversation Intelligence**.
4. **Connect:** Follow the prompts to sign in to RingCentral.
5. **Ask:** Start a new chat and try one of the questions below.

[ChatGPT and Codex marketplace help](https://developers.openai.com/plugins/build/plugins)

<details>
<summary>Install from a terminal with Codex</summary>

```sh
codex plugin marketplace add ringcentral/ringcentral-ace-conversation-intelligence --ref main
codex plugin add ringcentral-ace@ringcentral-ace-conversation-intelligence
```

Open Codex and complete RingCentral sign-in when prompted. Use the [installation guide](https://github.com/ringcentral/ringcentral-ace-conversation-intelligence/blob/main/INSTALL.md) to check update settings and refresh the plugin.

</details>

## Try asking

> Find an agent's recent recorded calls and extract the key questions asked and next steps.

> Analyze customer satisfaction drivers and summarize the main topics from recent calls.

> Which tracked customer issues rose most this week vs. last week? Show daily counts, percentage changes, and example calls.

Use a real person or team name and the time period you want to explore.

## Need help?

For account access, contact your company admin. For plugin setup or integration help, [contact RingCentral Developer Support](https://developers.ringcentral.com/support/create-case).

## Privacy

Connect your RingCentral account to work with the interactions available to you. Learn how RingCentral handles data in its [privacy notice](https://www.ringcentral.com/privacy).

## For developers and maintainers

See [DEVELOPMENT.md](https://github.com/ringcentral/ringcentral-ace-conversation-intelligence/blob/main/DEVELOPMENT.md) for packaging, validation, releases, GitHub workflows, and optional development hooks.

[Learn about AI Conversation Expert](https://www.ringcentral.com/products/ai-conversation-expert) · [Terms of service](https://www.ringcentral.com/legal) · [License](LICENSE)
