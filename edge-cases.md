# Edge Cases & Corner Scenarios: AI Reviews Summarizer for Noon

> **Reference Documents:**
> - [implementation-plan.md](file:///c:/AI%20reviews%20summarizer/implementation-plan.md)
> - [architecture.md](file:///c:/AI%20reviews%20summarizer/architecture.md)
> - [problemStatement.md](file:///c:/AI%20reviews%20summarizer/problemStatement.md)

---

## Overview

This document catalogs every edge case and corner scenario across all pipeline stages. Each entry includes the scenario description, potential impact, detection strategy, and recommended handling approach.

---

## 1. Review Ingestion Edge Cases

### 1.1 Zero Reviews Returned
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `google-play-scraper` returns an empty list for the configured time window. |
| **Cause** | App ID typo, API change, network failure, or genuinely no new reviews. |
| **Impact** | 🔴 Pipeline cannot proceed — no data to analyze. |
| **Detection** | Check `len(reviews) == 0` after fetch. |
| **Handling** | 1. Log warning. 2. Widen window by 2 weeks and retry once. 3. If still empty, abort with a clear error message: `"No reviews found for com.noon.buyerapp in the last {N} weeks."` |

### 1.2 Rate Limiting / IP Block
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Google Play blocks requests due to too many calls in a short period. |
| **Cause** | Aggressive pagination, running the script too frequently, or shared IP. |
| **Impact** | 🔴 Partial or no data fetched. |
| **Detection** | HTTP 429 response or `google-play-scraper` exception. |
| **Handling** | Exponential backoff: wait 2s → 4s → 8s, max 3 retries. If all fail, use cached `data/raw/google_play_reviews.json` from the last successful run (if exists) and log a warning. |

### 1.3 Extremely Large Review Volume
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | 10,000+ reviews in the 8–12 week window (e.g., after a viral event or major release). |
| **Cause** | Noon is a popular app; spikes happen during sales events. |
| **Impact** | 🟡 Memory pressure, slow processing, LLM token limit exceeded. |
| **Detection** | `len(reviews) > REVIEW_THRESHOLD` (e.g., 5000). |
| **Handling** | 1. Sample reviews: stratified random sample by rating (e.g., 1000 reviews max). 2. Log: `"Sampled {N} of {total} reviews for analysis."` 3. Ensure sampling preserves rating distribution. |

### 1.4 Reviews in Non-English Languages
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Noon operates in UAE/Saudi Arabia; reviews may be in Arabic, Hindi, Urdu, etc. |
| **Cause** | Multi-lingual user base. |
| **Impact** | 🟡 LLM may cluster non-English reviews incorrectly or produce garbled themes. |
| **Detection** | Language detection on `review.text` (e.g., using `langdetect` or the LLM itself). |
| **Handling** | **Option A:** Filter to English-only reviews (`language == "en"`), log count of excluded reviews. **Option B (future):** Translate non-English reviews via LLM before clustering. Document the chosen approach in the pulse footer. |

### 1.5 Malformed / Corrupt Review Data
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A review has `null` text, empty string body, or missing date. |
| **Cause** | Google Play API returning incomplete data, or scraper parsing error. |
| **Impact** | 🟡 Crashes during processing or produces nonsensical themes. |
| **Detection** | Schema validation: check `text is not None and len(text.strip()) > 0` and `date is not None`. |
| **Handling** | Skip reviews with missing/empty `text`. Log: `"Skipped {N} reviews with missing text."` Keep reviews with missing `title` (title is optional). |

### 1.6 Stale Cached Data
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | The fallback to cached data (from 1.2) uses reviews from weeks ago. |
| **Cause** | Multiple consecutive fetch failures. |
| **Impact** | 🟡 Pulse reflects outdated user sentiment. |
| **Detection** | Compare file modification timestamp of `google_play_reviews.json` against current date. |
| **Handling** | If cache is >14 days old, add a warning banner to the pulse: `"⚠️ Based on cached data from {date}. Live fetch failed."` |

### 1.7 Google Play Scraper API Breaking Change
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | The `google-play-scraper` package changes its API or field names in a new version. |
| **Cause** | Library update, Google Play Store HTML changes. |
| **Impact** | 🔴 Ingestion completely breaks. |
| **Detection** | `KeyError` or `AttributeError` during field extraction. |
| **Handling** | Pin the package version in `requirements.txt`. Wrap field access in try/except with clear error messages. |

---

## 2. Data Processing Edge Cases

### 2.1 All Reviews Are Duplicates
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | After deduplication, zero or very few unique reviews remain. |
| **Cause** | Bot-generated reviews, scraper fetching the same page multiple times. |
| **Impact** | 🔴 Insufficient data for meaningful clustering. |
| **Detection** | `len(deduplicated) < MIN_REVIEWS` (e.g., 10). |
| **Handling** | If <10 unique reviews remain, abort with: `"Insufficient unique reviews ({N}) for analysis. Minimum required: 10."` |

### 2.2 PII in Review Text That Regex Misses
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A user writes: `"My name is Ahmed and my order 9876543 never arrived to my apartment in JBR Tower 5."` |
| **Cause** | PII embedded in natural language that regex patterns don't cover (names, addresses). |
| **Impact** | 🔴 PII leaks into the pulse document — violates privacy constraint. |
| **Detection** | LLM-assisted PII scan (Layer 2). |
| **Handling** | 1. Regex strips emails, phones, device IDs. 2. LLM scans remaining text for contextual PII (names, addresses, order numbers). 3. Final PII scan on the assembled pulse before delivery. 4. If PII still detected at delivery time, halt and log error. |

### 2.3 Review Text Contains Only Emojis or Special Characters
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Review text is `"👍👍👍"` or `"!!!"` or `"..."`. |
| **Cause** | Users submitting low-effort reviews. |
| **Impact** | 🟡 No meaningful content to cluster; wastes LLM tokens. |
| **Detection** | `len(re.sub(r'[^\w\s]', '', text).strip()) < MIN_TEXT_LENGTH` (e.g., 5 characters). |
| **Handling** | Skip reviews with <5 alphanumeric characters. Log count of skipped emoji-only reviews. |

### 2.4 Extremely Long Individual Reviews
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A single review is 5,000+ words (a detailed rant or pasted support transcript). |
| **Cause** | Passionate user writing an essay. |
| **Impact** | 🟡 Consumes disproportionate LLM context window; may skew theme clustering. |
| **Detection** | `len(review.text.split()) > MAX_REVIEW_WORDS` (e.g., 500). |
| **Handling** | Truncate to first 500 words with a `[truncated]` marker. Log the truncation. |

### 2.5 Date Parsing Failures
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Review date is in an unexpected format or timezone. |
| **Cause** | `google-play-scraper` returning different date formats across locales. |
| **Impact** | 🟡 Date filtering may include/exclude wrong reviews. |
| **Detection** | `try/except` around `datetime.fromisoformat()` or `dateutil.parser.parse()`. |
| **Handling** | Use `dateutil.parser.parse()` for flexible parsing. If still fails, skip the review and log: `"Unparseable date for review {id}: {raw_date}"`. |

### 2.6 Unicode / Encoding Issues
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Reviews contain mixed Arabic/English text with RTL characters, or special Unicode (e.g., zero-width spaces). |
| **Cause** | Multi-lingual Noon user base. |
| **Impact** | 🟡 Text processing breaks; PII regex fails to match. |
| **Detection** | Check for encoding errors during JSON serialization. |
| **Handling** | Normalize all text to NFC Unicode form. Strip zero-width characters. Ensure all file I/O uses `encoding='utf-8'`. |

---

## 3. LLM Theme Clustering Edge Cases

### 3.1 LLM Returns Invalid JSON
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM output contains markdown fences, trailing commas, or conversational text mixed with JSON. |
| **Cause** | Non-deterministic LLM behavior, prompt ambiguity. |
| **Impact** | 🔴 `JsonOutputParser()` crashes. |
| **Detection** | `json.JSONDecodeError` exception. |
| **Handling** | 1. Strip markdown code fences (`` ```json ... ``` ``). 2. Attempt `json.loads()` on cleaned output. 3. If still fails, retry with an explicit prompt: `"Output ONLY valid JSON. No markdown, no explanations."` 4. Max 2 retries; abort if all fail. |

### 3.2 LLM Returns More Than 5 Themes
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Despite the prompt saying "up to 5", the LLM returns 7 or 8 themes. |
| **Cause** | LLM not following instructions precisely. |
| **Impact** | 🟡 Violates the ≤5 themes constraint. |
| **Detection** | `len(themes) > 5` after parsing. |
| **Handling** | Take only the top 5 by `review_count`. Log: `"LLM returned {N} themes; trimmed to top 5."` |

### 3.3 LLM Returns Only 1 Theme
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | All reviews are clustered into a single theme (e.g., "General Feedback"). |
| **Cause** | Too few reviews, very homogeneous feedback, or weak prompt. |
| **Impact** | 🟡 Pulse has only 1 theme instead of 3. |
| **Detection** | `len(themes) < 2`. |
| **Handling** | If 1 theme: re-prompt with `"Try to identify at least 2-3 distinct sub-themes within the reviews."` If still 1 theme after retry: generate pulse with 1 theme, add note: `"Reviews were predominantly about a single topic this week."` |

### 3.4 Theme Names Are Vague or Overlapping
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM returns themes like "App Issues" and "Technical Problems" which are essentially the same. |
| **Cause** | Insufficient prompt guidance on differentiation. |
| **Impact** | 🟡 Redundant themes reduce pulse value. |
| **Detection** | Semantic similarity check (could use embeddings, or a simple LLM call asking "Are these themes distinct?"). |
| **Handling** | Add prompt instruction: `"Ensure each theme is distinct and non-overlapping. Merge similar themes."` If detected post-hoc, merge and re-rank. |

### 3.5 Quotes Are Not Verbatim
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM paraphrases or slightly modifies a user quote instead of using the exact text. |
| **Cause** | LLM's tendency to rephrase for clarity. |
| **Impact** | 🔴 Violates the "real user quotes, no invented wording" requirement. |
| **Detection** | Cross-reference selected quotes against the original review corpus using exact string matching or fuzzy matching (e.g., `fuzzywuzzy` ratio > 95%). |
| **Handling** | 1. After LLM returns quotes, verify each against the cleaned review corpus. 2. If a quote doesn't match (fuzzy ratio < 90%), find the closest matching review and use its exact text. 3. Log: `"Quote for theme '{theme}' was non-verbatim; replaced with closest match."` |

### 3.6 LLM Assigns Reviews to Wrong Themes
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A review about "delivery delay" is assigned to the "Payments" theme. |
| **Cause** | LLM misclassification, ambiguous review content. |
| **Impact** | 🟡 Theme counts and representative quotes may be inaccurate. |
| **Detection** | Difficult to auto-detect; rely on LLM quality and prompt engineering. |
| **Handling** | Accept as a known limitation. Include a note in README: `"Theme assignments are AI-generated and may occasionally misclassify ambiguous reviews."` Consider a human-in-the-loop review step for critical pulses. |

### 3.7 LLM Token Limit Exceeded
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | The cleaned review corpus is too large to fit in a single LLM context window. |
| **Cause** | >2000 reviews with substantial text; Gemini Flash has ~1M token limit but cost/latency increases. |
| **Impact** | 🔴 LLM API returns a token limit error. |
| **Detection** | Estimate token count before sending: `len(corpus) / 4` (rough char-to-token ratio). |
| **Handling** | 1. If estimated tokens > threshold (e.g., 100K), batch reviews into chunks of 500. 2. Cluster each batch separately, then merge themes across batches. 3. Alternatively, send only review text (no metadata) to reduce tokens. |

### 3.8 LLM Generates Offensive or Inappropriate Theme Names
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM creates a theme name that is offensive, sarcastic, or unprofessional (e.g., "Trash App"). |
| **Cause** | LLM reflecting the tone of negative reviews in theme naming. |
| **Impact** | 🟡 Unprofessional pulse shared with leadership. |
| **Detection** | Basic profanity filter or LLM moderation check on theme names. |
| **Handling** | Add prompt instruction: `"Use professional, neutral theme names suitable for executive reporting."` Post-process: run theme names through a moderation check. |

---

## 4. Pulse Generation Edge Cases

### 4.1 Pulse Exceeds 250-Word Limit
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Generated pulse is 300+ words despite the prompt asking for ≤250. |
| **Cause** | LLM being verbose; long quotes or action items. |
| **Impact** | 🟡 Violates length constraint. |
| **Detection** | `len(pulse_text.split()) > 250`. |
| **Handling** | 1. Re-prompt with stricter instruction: `"The note MUST be under 250 words. Current: {count} words. Condense."` 2. Max 2 re-prompts. 3. If still over, programmatically truncate action items to 1 sentence each. |

### 4.2 Pulse Contains PII That Slipped Through
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A quote contains a name or address that wasn't caught during processing. |
| **Cause** | PII stripping failed for an edge case pattern. |
| **Impact** | 🔴 Privacy violation. |
| **Detection** | Final PII regex scan on the assembled pulse text. |
| **Handling** | If PII detected: 1. Strip the PII from the pulse. 2. Log the incident. 3. If the PII was in a quote, replace with a different quote from the same theme. 4. Never halt delivery silently — either fix and deliver, or abort with a clear error. |

### 4.3 Average Rating Calculation With Missing Ratings
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Some reviews have `rating: null` or `rating: 0`. |
| **Cause** | Scraper returning incomplete data. |
| **Impact** | 🟡 Average rating is skewed or produces `NaN`. |
| **Detection** | Filter: `rating is not None and 1 <= rating <= 5`. |
| **Handling** | Exclude reviews with invalid ratings from the average calculation. Log count of excluded ratings. |

### 4.4 Date Range Formatting for Different Locales
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Pulse shows "Based on reviews from 09/13/2026 – 07/05/2026" which is ambiguous (MM/DD vs DD/MM). |
| **Cause** | Date formatting not standardized. |
| **Impact** | 🟡 Confusing for international teams. |
| **Detection** | N/A — proactive design decision. |
| **Handling** | Always use unambiguous format: `"Sep 13, 2026"` or ISO 8601 `"2026-09-13"`. |

### 4.5 All Reviews Are 5-Star (or All 1-Star)
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Every review in the window is 5 stars with "Great app!" text. |
| **Cause** | Rating manipulation, review bombing, or genuinely happy users. |
| **Impact** | 🟡 Themes may be meaningless; action ideas may be empty. |
| **Detection** | `std_dev(ratings) < 0.1` or all reviews share the same rating. |
| **Handling** | Generate the pulse anyway, but note: `"📊 All reviews this period were {N}-star rated."` Action ideas should focus on "maintaining momentum" rather than "fixing issues." |

---

## 5. MCP Delivery Edge Cases

### 5.1 MCP Server Unreachable
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | MCP server at `localhost:3001` (Docs) or `localhost:3002` (Gmail) is not running. |
| **Cause** | Server not started, port conflict, or crashed. |
| **Impact** | 🔴 Pulse cannot be delivered to Google Docs/Gmail. |
| **Detection** | Connection refused / timeout on MCP client connect. |
| **Handling** | 1. Retry 3 times with 2s/4s/8s backoff. 2. If all fail, save pulse locally to `data/pulses/pulse_YYYY-MM-DD.md`. 3. Log: `"⚠️ MCP server unreachable. Pulse saved locally: {path}"`. 4. Continue to attempt the other delivery channel (Docs failure shouldn't block Gmail). |

### 5.2 MCP Authentication Expired
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | MCP server's OAuth token for Google has expired or been revoked. |
| **Cause** | Token not refreshed, user revoked app access in Google settings. |
| **Impact** | 🔴 API calls to Google Docs/Gmail fail with 401. |
| **Detection** | MCP server returns auth error in tool response. |
| **Handling** | 1. Log error with clear instructions: `"MCP auth expired. Re-authenticate with: [re-auth command/URL]"`. 2. Save pulse locally as fallback. 3. Do not retry — auth issues won't resolve with retries. |

### 5.3 Google Doc Already Exists With Same Title
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A Google Doc named "Noon App Pulse" already exists from a previous run. |
| **Cause** | Running the pipeline multiple times without changing the title. |
| **Impact** | 🟡 Duplicate documents or overwritten content. |
| **Detection** | Check if a doc with the same title exists before creating. |
| **Handling** | **Strategy A (Append):** Update the existing doc with the new pulse, adding a date separator. **Strategy B (New Doc):** Create a new doc with a date-stamped title: `"Noon App Pulse — Week of Sep 13, 2026"`. Recommend Strategy B for auditability. |

### 5.4 Gmail Draft Recipient Is Invalid
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `EMAIL_RECIPIENT` is misconfigured (e.g., `"team@"`, `""`, or `"not-an-email"`). |
| **Cause** | Typo in `.env` file. |
| **Impact** | 🟡 Gmail draft creation may fail or create an unsendable draft. |
| **Detection** | Validate email format with regex before calling MCP. |
| **Handling** | If invalid: log error `"Invalid EMAIL_RECIPIENT: {value}"`. Create the draft with the authenticated user's own email as fallback. |

### 5.5 Pulse Content Too Large for Email Body
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Despite the 250-word limit, the formatted HTML version of the pulse exceeds Gmail's draft size limit. |
| **Cause** | Unlikely given the constraints, but possible with heavy formatting. |
| **Impact** | 🟢 Very unlikely, low impact. |
| **Detection** | Check formatted body size before sending. |
| **Handling** | If body exceeds limit: include only a summary + Google Doc link in the email body. |

### 5.6 Network Timeout During Delivery
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | MCP tool call hangs indefinitely due to network issues. |
| **Cause** | Network instability, MCP server overloaded. |
| **Impact** | 🔴 Pipeline hangs forever. |
| **Detection** | Set timeout on MCP client calls (e.g., 30 seconds). |
| **Handling** | Timeout after 30s. Treat as MCP unreachable (fallback to local save). Log: `"MCP call timed out after 30s."` |

---

## 6. LangChain Agent Edge Cases

### 6.1 Agent Enters Infinite Loop
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Agent keeps re-invoking the same tool or cycling between tools without progressing. |
| **Cause** | Ambiguous agent prompt, tool returning unclear results, LLM confusion. |
| **Impact** | 🔴 Pipeline never completes; wastes API credits. |
| **Detection** | `AgentExecutor(max_iterations=10)` — agent stops after 10 iterations. |
| **Handling** | 1. Set `max_iterations=10` on `AgentExecutor`. 2. Set `max_execution_time=300` (5 minutes). 3. If limit hit, log the last 3 tool calls for debugging. 4. Save any partial results generated so far. |

### 6.2 Agent Calls Tools in Wrong Order
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Agent tries to cluster themes before fetching reviews, or publishes to Docs before generating the pulse. |
| **Cause** | ReAct agent making autonomous (incorrect) decisions. |
| **Impact** | 🔴 Tools fail because their input data doesn't exist yet. |
| **Detection** | Tool raises `FileNotFoundError` or returns an error message. |
| **Handling** | 1. Each tool validates its prerequisites (e.g., `cluster_themes` checks that `cleaned_reviews.json` exists). 2. If prerequisite missing, return a clear message: `"Error: Run process_reviews first. cleaned_reviews.json not found."` 3. Agent should self-correct based on the error. 4. Consider using LangGraph `StateGraph` for deterministic ordering (future enhancement). |

### 6.3 Agent Parsing Error
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `AgentExecutor` fails to parse the LLM's action/tool selection output. |
| **Cause** | LLM outputs free-form text instead of the expected tool-call format. |
| **Impact** | 🟡 Pipeline stalls on one step. |
| **Detection** | `OutputParserException` raised by LangChain. |
| **Handling** | Set `handle_parsing_errors=True` on `AgentExecutor`. This auto-retries with a correction prompt. Max 3 parsing retries before abort. |

### 6.4 API Key Exhausted Mid-Pipeline
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Gemini API key hits its quota limit during theme clustering (Phase 4) after reviews are already fetched and processed. |
| **Cause** | Quota limits, especially on free-tier keys. |
| **Impact** | 🔴 Pipeline partially complete; can't finish LLM-dependent steps. |
| **Detection** | `ResourceExhausted` or `429` error from Gemini API. |
| **Handling** | 1. Save all progress so far (raw + processed reviews). 2. Log: `"API quota exhausted. Resume with: python src/main.py --resume"`. 3. Implement `--resume` flag that skips already-completed steps (checks for existing output files). |

### 6.5 Tool Returns Unexpected Output Type
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A tool returns a dict when the agent expects a string, or vice versa. |
| **Cause** | Bug in tool implementation, LLM misinterpretation. |
| **Impact** | 🟡 Agent confusion; may re-invoke the tool or error out. |
| **Detection** | Type validation in tool return. |
| **Handling** | All tools should return `str` type (LangChain `@tool` convention). Serialize complex data to JSON strings. |

---

## 7. Data Integrity Edge Cases

### 7.1 Concurrent Pipeline Runs
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | Two instances of `main.py` run simultaneously (e.g., cron overlap). |
| **Cause** | Cron job fires before the previous run finishes. |
| **Impact** | 🟡 File write conflicts in `data/` directory; duplicate Google Docs. |
| **Detection** | File lock check at startup. |
| **Handling** | 1. Create a lock file (`data/.lock`) at pipeline start. 2. If lock file exists and is <1 hour old, abort: `"Another pipeline run is in progress."` 3. Delete lock file on completion (or on crash via `atexit`). |

### 7.2 Disk Full
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `data/raw/` or `data/processed/` writes fail because the disk is full. |
| **Cause** | Accumulated pulse archives, large raw review files. |
| **Impact** | 🔴 Pipeline crashes during file write. |
| **Detection** | `OSError` / `IOError` on file write. |
| **Handling** | 1. Catch `IOError` and log: `"Disk write failed. Check available disk space."` 2. Implement optional cleanup: delete raw/processed files older than 30 days. |

### 7.3 Corrupted JSON Files
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `cleaned_reviews.json` is partially written (e.g., crash during write) and contains invalid JSON. |
| **Cause** | Power failure, process kill during file write. |
| **Impact** | 🔴 Next pipeline stage fails to load data. |
| **Detection** | `json.JSONDecodeError` when loading. |
| **Handling** | 1. Write to a temp file first, then atomic rename: `write → .tmp → rename to .json`. 2. If loading fails, delete the corrupt file and re-run the previous stage. |

---

## 8. Privacy & Security Edge Cases

### 8.1 PII in Theme Names
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM generates a theme name containing a person's name: `"Ahmed's Delivery Complaints"`. |
| **Cause** | LLM incorporating review content into theme labels. |
| **Impact** | 🔴 PII in the pulse document. |
| **Detection** | Run PII stripper on theme names (not just review text). |
| **Handling** | Run the same PII regex + LLM scan on theme names and descriptions. Strip or replace any detected PII. |

### 8.2 PII in Action Items
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | LLM generates: `"Fix the delivery issue reported by user Ahmed in JBR."` |
| **Cause** | LLM referencing specific review content in generated actions. |
| **Impact** | 🔴 PII in the pulse document. |
| **Detection** | Final PII scan covers the entire pulse (themes + quotes + actions). |
| **Handling** | Same as 8.1 — PII scan on all generated text, not just quotes. |

### 8.3 API Key Leaked in Logs
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `config.py` logs the full API key during startup, or an error message includes the key. |
| **Cause** | Overly verbose logging, debug mode left on. |
| **Impact** | 🔴 Security breach — API key compromised. |
| **Detection** | Code review; grep logs for key patterns. |
| **Handling** | 1. Never log API keys — mask them: `"GEMINI_API_KEY=***{last4}"`. 2. Use `.env` (not hardcoded). 3. `.gitignore` includes `.env`. |

### 8.4 Sensitive Review Content
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | A review contains hate speech, threats, or illegal content. |
| **Cause** | User-generated content is unpredictable. |
| **Impact** | 🟡 Inappropriate content surfaces in the pulse shared with leadership. |
| **Detection** | Content moderation via Gemini's safety filters. |
| **Handling** | 1. Rely on Gemini's built-in safety filters during clustering. 2. Add prompt instruction: `"Exclude any reviews containing hate speech, threats, or explicit content."` 3. If a selected quote contains inappropriate content, replace it. |

---

## 9. Environment & Configuration Edge Cases

### 9.1 Missing `.env` File
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | User runs `python src/main.py` without creating `.env`. |
| **Cause** | Forgot to copy `.env.example` to `.env`. |
| **Impact** | 🔴 All API calls fail; pipeline crashes. |
| **Detection** | Check `os.path.exists('.env')` at startup. |
| **Handling** | Print clear error: `"❌ .env file not found. Copy .env.example to .env and fill in your keys."` Exit with code 1. |

### 9.2 Missing or Empty API Key
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `GEMINI_API_KEY=` is empty or `GEMINI_API_KEY=your-key-here` (placeholder). |
| **Cause** | User didn't update the placeholder. |
| **Impact** | 🔴 LLM calls fail with auth error. |
| **Detection** | Validate at startup: key is not None, not empty, not equal to placeholder. |
| **Handling** | Print: `"❌ GEMINI_API_KEY is not configured. Update your .env file."` Exit with code 1. |

### 9.3 Invalid `REVIEW_WEEKS` Value
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | `REVIEW_WEEKS=abc` or `REVIEW_WEEKS=-5` or `REVIEW_WEEKS=200`. |
| **Cause** | User misconfiguration. |
| **Impact** | 🟡 Fetch too many/few reviews, or crash on int conversion. |
| **Detection** | Validate: is integer, in range 1–52. |
| **Handling** | If invalid, warn and default to 10: `"⚠️ Invalid REVIEW_WEEKS={value}. Defaulting to 10."` |

### 9.4 Python Version Incompatibility
| Aspect | Detail |
| :--- | :--- |
| **Scenario** | User runs with Python 3.8 which doesn't support `match` statements or newer syntax. |
| **Cause** | Older Python installation. |
| **Impact** | 🔴 `SyntaxError` on startup. |
| **Detection** | Check `sys.version_info >= (3, 11)` at startup. |
| **Handling** | Print: `"❌ Python 3.11+ required. Current: {version}"` Exit with code 1. |

---

## Edge Case Summary Matrix

| # | Category | Scenario | Severity | Likelihood |
| :---: | :--- | :--- | :---: | :---: |
| 1.1 | Ingestion | Zero reviews returned | 🔴 High | Medium |
| 1.2 | Ingestion | Rate limiting / IP block | 🔴 High | Medium |
| 1.3 | Ingestion | Extremely large volume | 🟡 Medium | Low |
| 1.4 | Ingestion | Non-English reviews | 🟡 Medium | High |
| 1.5 | Ingestion | Malformed review data | 🟡 Medium | Medium |
| 1.6 | Ingestion | Stale cached data | 🟡 Medium | Low |
| 1.7 | Ingestion | Scraper API change | 🔴 High | Low |
| 2.1 | Processing | All duplicates | 🔴 High | Low |
| 2.2 | Processing | PII regex misses | 🔴 High | Medium |
| 2.3 | Processing | Emoji-only reviews | 🟡 Medium | Medium |
| 2.4 | Processing | Extremely long reviews | 🟡 Medium | Low |
| 2.5 | Processing | Date parsing failure | 🟡 Medium | Medium |
| 2.6 | Processing | Unicode / encoding | 🟡 Medium | Medium |
| 3.1 | Clustering | Invalid JSON from LLM | 🔴 High | Medium |
| 3.2 | Clustering | >5 themes returned | 🟡 Medium | Medium |
| 3.3 | Clustering | Only 1 theme | 🟡 Medium | Low |
| 3.4 | Clustering | Vague/overlapping themes | 🟡 Medium | Medium |
| 3.5 | Clustering | Non-verbatim quotes | 🔴 High | High |
| 3.6 | Clustering | Misclassified reviews | 🟡 Medium | Medium |
| 3.7 | Clustering | Token limit exceeded | 🔴 High | Low |
| 3.8 | Clustering | Offensive theme names | 🟡 Medium | Low |
| 4.1 | Pulse | Exceeds 250 words | 🟡 Medium | Medium |
| 4.2 | Pulse | PII in final output | 🔴 High | Low |
| 4.3 | Pulse | Missing ratings | 🟡 Medium | Low |
| 4.4 | Pulse | Ambiguous date format | 🟡 Medium | Low |
| 4.5 | Pulse | Uniform ratings | 🟡 Medium | Low |
| 5.1 | Delivery | MCP server down | 🔴 High | Medium |
| 5.2 | Delivery | Auth expired | 🔴 High | Medium |
| 5.3 | Delivery | Duplicate Google Doc | 🟡 Medium | Medium |
| 5.4 | Delivery | Invalid email recipient | 🟡 Medium | Low |
| 5.5 | Delivery | Email body too large | 🟢 Low | Low |
| 5.6 | Delivery | Network timeout | 🔴 High | Medium |
| 6.1 | Agent | Infinite loop | 🔴 High | Low |
| 6.2 | Agent | Wrong tool order | 🔴 High | Medium |
| 6.3 | Agent | Parsing error | 🟡 Medium | Medium |
| 6.4 | Agent | API quota exhausted | 🔴 High | Low |
| 6.5 | Agent | Unexpected tool output | 🟡 Medium | Low |
| 7.1 | Data | Concurrent runs | 🟡 Medium | Low |
| 7.2 | Data | Disk full | 🔴 High | Low |
| 7.3 | Data | Corrupted JSON | 🔴 High | Low |
| 8.1 | Privacy | PII in theme names | 🔴 High | Low |
| 8.2 | Privacy | PII in actions | 🔴 High | Low |
| 8.3 | Privacy | API key in logs | 🔴 High | Low |
| 8.4 | Privacy | Offensive content | 🟡 Medium | Medium |
| 9.1 | Config | Missing .env | 🔴 High | Medium |
| 9.2 | Config | Empty API key | 🔴 High | Medium |
| 9.3 | Config | Invalid REVIEW_WEEKS | 🟡 Medium | Low |
| 9.4 | Config | Python version | 🔴 High | Low |
