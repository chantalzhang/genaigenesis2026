# Agent² — Presentation Script

> Target: ~3-4 minutes. Adjust pacing to your demo flow.
> 
> Judging priorities: **Creativity**, **Practical Impact**, **Technical Depth**, **User Experience**

---

## OPENING (30s)

Imagine you're looking for a home. You download three apps, set up accounts, toggle filters, scroll through hundreds of listings. Or you hire a real estate agent — but they work on commission, so their interests aren't always your interests. Either way, you're spending hours on a process that should be simple. 

What if finding a home was as easy as making a phone call — and you had an agent that actually worked for *you*?

**We built Agent² — your real estate agent *agent*.** You text a number. An AI calls you back. You describe your dream home in plain English — or however you naturally talk. And behind the scenes, Agent² does everything else — finds listings, scores them, and contacts agents on your behalf. No apps. No accounts. No forms. No screens at all. Just a conversation.

---

## THE DEMO (90s)

Let me show you.

**Step 1 — The user experience.**
This is the entire user interface: your phone. You text our number. Agent² replies and calls you back. On the call, our AI voice agent has a natural conversation — not a menu, not "press 1 for English." It listens, it asks follow-ups, it confirms. *"What are you looking for?" "A two-bedroom house in Toronto, pet-friendly, near schools." "Got it — any budget in mind?" "I make about twenty bucks an hour." "No problem, I can work with that."* That's it. That's the whole experience for the user. Hang up and wait for your text.

Think about who this helps — someone who's never used Zillow, someone who's more comfortable talking than typing, someone who just wants to say what they need and have it handled. That's the user experience we designed for.

**Step 2 — The intelligence.**
Behind the scenes, we now have a raw transcript — messy, full of filler words, speech-to-text errors, the AI sometimes mishearing numbers. We feed that into our criteria extraction pipeline built on **Railtracks**. The LLM doesn't just pull out keywords — it *reasons*. From *"I make twenty bucks an hour"* it calculates a realistic home budget. From *"I have a small dog"* it flags pet-friendly as a required feature. It cross-checks the AI's recap against what the caller actually said, because speech-to-text errors in the recap could send the search in the wrong direction. The output is a precise, structured search query.

*[Show the JSON output on screen]*

This is the creative core of Agent² — turning the most natural human interface, a conversation, into structured data that machines can act on.

**Step 3 — The search.**
That query hits Zillow through ScraperAPI. But here's the thing — we don't trust Zillow's filters. We scrape broadly, then score every listing ourselves against the caller's full criteria. We go deep: we scrape each listing's detail page to check pet policies, parking, school proximity — things you'd normally have to click into every single listing to find. Every listing gets a transparency score. The user sees *why* something matched and *why* something didn't. No black boxes.

*[Show ranked listings with scores and violations]*

**Step 4 — The action.**
Most tools stop at "here are your results." Agent² goes further. We launch a real browser, navigate to the listing page, click "Contact Agent," and fill out the inquiry form — name, phone, email, a personalized message — character by character, like a real person. The listing agent receives the inquiry. The user gets their matched listings by text. The entire loop — from spoken words to an agent receiving a lead — is closed automatically.

*[Show the browser filling the form in real time]*

That's not a simulation. That's a real Zillow page, a real form, being filled right now.

---

## TECHNICAL DEEP DIVE

### 1. Messaging and Call Initiation — Telnyx

Everything starts with a text message. Telnyx handles both our SMS and telephony layer. When a user texts our number, a webhook fires into our FastAPI backend. We run a lightweight state machine — greeting, confirmation, call trigger. The user replies YES, and we fire an outbound call through Telnyx Call Control. That call opens a media stream — a live WebSocket connection streaming raw audio in both directions. The user doesn't download anything. They just pick up the phone.

### 2. The Voice Agent — PersonaPlex

On the other end of that call is PersonaPlex — our AI voice agent. PersonaPlex runs on its own WebSocket server, streaming Opus-encoded audio at 24 kHz. But Telnyx sends us raw L16 PCM at 8 kHz. Two completely different formats, two different sample rates.

So we built a real-time audio bridge. It's full-duplex — two concurrent async pipelines running simultaneously. User audio comes in at 8 kHz. We run echo cancellation to remove the agent's own voice bleeding back through the speaker, apply RNNoise for background noise reduction, upsample from 8 to 24 kHz, encode to Opus, and forward to PersonaPlex. When PersonaPlex responds, we reverse the chain — decode Opus, downsample from 24 to 8 kHz, feed the output back into the echo canceller as a reference signal, and stream it to Telnyx. All of this happens per audio chunk, under 50 milliseconds. The user hears a natural conversation. Underneath it's a live audio transcoding pipeline.

While this is happening, we're recording both sides of the call. When the call ends, the recording gets transcribed — and that transcript is what kicks off everything downstream.

### 3. Transcript to Search Criteria — Railtracks + LLM

Raw transcripts are messy — filler words, garbled speech-to-text, the AI agent sometimes mishearing numbers. This is where Railtracks comes in. We use the Railtracks agent framework to orchestrate a call to our hackathon LLM endpoint. The LLM receives two carefully engineered Jinja prompts: a system prompt defining the exact JSON schema we need — location, price, bedrooms, bathrooms, property type, size, year built, required features, nice-to-haves, keywords — and a user prompt containing the raw transcript.

This design gives us maximum flexibility in what the user can say, while enforcing a perfectly consistent output every time. The caller says *"I make twenty bucks an hour"* — the LLM calculates a realistic home budget from income. They say *"I have a small dog"* — it maps that to a pet-friendly requirement. It cross-checks what the AI agent summarized against what the caller actually said, because speech-to-text errors in the agent's recap could send the search in the wrong direction. Natural language in, structured JSON out — no matter how casual or messy the conversation was.

### 4. Live Scraping and Listing Analysis — Zillow + ScraperAPI

That structured JSON now drives a live scrape of Zillow. We hit Zillow's search page through ScraperAPI, which handles proxy rotation, IP management, and server-side rendering — so we don't get blocked or served CAPTCHAs. We parse the results two ways: first we look for Zillow's embedded JSON in the page source, which is the most reliable path. If that's missing, we fall back to HTML card scraping with BeautifulSoup. Either way, we normalize and deduplicate.

But the search page only gives basics — price, beds, address. We go deeper. For each listing, we scrape the individual detail page. We dig into Zillow's Next.js server data — deeply nested JSON embedded in the page — to extract building attributes, pet policies, parking availability, school assignments, amenity details. Things like *"Is this pet-friendly?" "Are there schools nearby?" "Is there parking?"* — those answers only live on the detail page, and we pull them out programmatically.

Then we score every listing against the caller's full criteria. Price fit, bedroom match, square footage, property type, keywords, and real feature verification from the detail page data. Required features confirmed absent become hard violations. Nice-to-haves boost the score. The result is a transparently ranked list — the user sees exactly *why* each listing matched or didn't. If nothing's a perfect match, we surface the closest alternatives and explain the gaps. No black boxes.

### 5. Live Contact Form — Playwright

Agent² doesn't just find listings — it reaches out on your behalf. We launch a real Chromium browser using Playwright with stealth anti-detection plugins. We navigate to the listing page and locate the "Contact Agent" button using resilient locators — role-based and label-based pattern matching, not brittle CSS selectors, so it survives Zillow's frequent UI changes.

We click the CTA, wait for the contact form modal to render, and fill every field — name, phone, email, a personalized message — character by character with realistic typing delays and pauses between fields. It looks and behaves exactly like a human filling out a form, because it *is* a real browser performing real interactions on a live website. The listing agent receives the inquiry. The user gets their matched listings by text. The entire loop — from a spoken sentence to an agent receiving a lead — is closed automatically.

---

## THE CLOSE (30s)

Agent² turns a three-hour process into a three-minute phone call.

It's accessible — anyone with a phone can use it, no tech literacy required. It's practical — it solves a real problem that millions of people deal with every year. It's technically deep — five autonomous systems chained together, end to end, from voice to action. And it's creative — we rethought the entire interface. The best UX for finding a home isn't a better app. It's no app at all.

**Agent² — your real estate agent *agent*.**

---

## TIPS FOR DELIVERY

- **During Step 4**, have the browser demo running live or as a screen recording — the form filling in real-time is the biggest wow moment. Let it run while you talk.
- **Pause after the JSON output** — let the audience see how a messy conversation becomes clean structured data. This is the "intelligence" moment.
- **Call out accessibility** — the phone-first design means anyone can use it, which lands well with impact-focused judges.
- **The "character by character" typing** is intentionally slow for demo effect — mention this, it shows the system is interacting with a real website, not faking it.
- **If asked about reliability**: scoring transparency (users see *why*), retry logic (tries multiple listings), broad-then-filter strategy (never zero results).
- **If asked about scale**: ScraperAPI handles proxy rotation, LLM endpoint is stateless and horizontally scalable, voice pipeline is per-call WebSocket streams.
- **If asked "why not just use ChatGPT?"**: ChatGPT can't call you, can't scrape live listings, can't fill real forms, and can't text you results. Agent² is an end-to-end autonomous pipeline, not a chatbot.
