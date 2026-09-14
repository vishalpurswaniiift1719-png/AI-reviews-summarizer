# Problem Statement: AI Reviews Summarizer for Noon

## Overview
The goal is to turn raw mobile-store feedback for the **Noon** platform into a weekly pulse that the team can scan in minutes. This pulse will highlight what users care about, what they actually said, and actionable next steps. 

Reviews are already public; the objective is to aggregate, theme, summarize, and deliver that insight through familiar surfaces—specifically Google Docs for the written pulse and Gmail for a draft email to yourself. This should be achieved using MCP (Model Context Protocol) servers rather than handling credentials or REST wiring manually.

## End-to-End Flow
1. **Pull Reviews:** Fetch recent Google Play Store reviews for the Noon Buyer App (within constraints).
   - *Target App:* [Noon Buyer App (Google Play)](https://play.google.com/store/apps/details?id=com.noon.buyerapp&hl=en)
2. **Theme & Distill:** Cluster the reviews into a small set of themes and distill them into a one-page weekly note.
3. **Publish to Google Docs:** Put that note where stakeholders can read it using Google Docs.
4. **Draft Email Notification:** Create a draft email to yourself (or an alias) that contains or links to that pulse via Gmail.

## Deliverables
The weekly one-page pulse must include:
- **Top Themes:** What people are talking about most.
- **Real User Quotes:** Verbatim snippets from reviews (no invented wording).
- **Action Ideas:** Three concrete next steps grounded in the themes.
- **Email Draft:** A draft email containing this weekly note or a clear pointer to it.

## Target Audience
| Audience | Why this helps |
| :--- | :--- |
| **Product / Growth** | Prioritize fixes and improvements from real signals. |
| **Support** | Align messaging with what users are actually saying. |
| **Leadership** | Provide a one-page health check without drowning in raw reviews. |

## Core Requirements (What You Must Build)
- **Import:** Fetch reviews from roughly the last 8–12 weeks (fields such as rating, title, text, date).
- **Group:** Cluster reviews into at most **5 themes** (e.g., onboarding, KYC, payments, statements, withdrawals—pick what fits Noon).
- **Generate Note:** Create a weekly one-page note with:
  - Top 3 themes (subset of your themes as appropriate).
  - 3 user quotes.
  - 3 action ideas.
- **Email:** Draft an email with the note to yourself or an alias.

## Integrations
- **Google Docs & Gmail via MCP:**
  - Use MCP (Model Context Protocol) servers for Google Docs and Gmail (e.g., creating/updating the pulse document and creating the draft message).
  - Do **not** integrate Google APIs directly (no bespoke OAuth client + REST client code as the primary integration path).
  - Rely on MCP servers that expose tools your agent or app can call to avoid duplicating auth and HTTP plumbing.

## Key Constraints
- **Public Reviews Only:** Use public review exports only. No scraping behind store logins or ToS-violating automation.
- **Themes Limit:** Maximum 5 themes for clustering; the written pulse highlights the top 3.
- **Length:** Keep the note scannable and **≤250 words** where applicable.
- **Privacy:** Do not include PII—no usernames, emails, device IDs, or other identifiable reviewer data in any artifact. Quotes should be anonymous and stripped as needed.
