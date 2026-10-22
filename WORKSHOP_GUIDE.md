# AI STEM Career Navigator — 45-Minute Workshop Guide

**Goal:** Every participant leaves having *built* a working generative-AI app on AWS — not just watched one.
**Principle:** Beginner-friendly. No model training, no complex infrastructure. Just connect four cloud services.
**Full click-by-click steps:** see [MANUAL_SETUP_GUIDE.md](MANUAL_SETUP_GUIDE.md) — share it with participants.

```
 Browser (HTML/CSS/JS)
      │  POST /generate  {goal, level, interests, hours}
      ▼
 Amazon API Gateway (HTTP API)
      │
      ▼
 AWS Lambda (Python) ── builds the prompt
      │  converse()
      ▼
 Amazon Bedrock ── Amazon Nova Pro writes the roadmap (JSON)
```

---

## Before the workshop (facilitator checklist)

- [ ] Pick **one region** for everyone (recommended: `us-east-1` or `us-west-2`) and put it on the first slide.
- [ ] Confirm participants' accounts can use **Amazon Nova** in Bedrock (Bedrock console → *Model access*; in most accounts Amazon models are enabled by default, otherwise request access — it's instant for Nova).
- [ ] Do a full dry run in a fresh account/IAM user. Time yourself.
- [ ] Share the starter files (`frontend/` folder + `lambda/lambda_function.py`) via a link or a zip — participants should **paste**, not type, the code.
- [ ] Have a **backup API URL** from your own deployment so anyone who falls behind can still connect their frontend in step 5.
- [ ] Cost note for participants: a workshop's worth of Nova Pro calls costs pennies; Lambda/API Gateway stay within the free tier.

---

## 0–5 min · Introduce cloud AI architecture

Talking points:
- "Today you'll build a real AI app — an AI career coach — in 45 minutes."
- Walk through the diagram above. One sentence per box:
  - **Frontend** — what the user sees.
  - **API Gateway** — the front door; gives us a public URL.
  - **Lambda** — our code; runs only when called, no servers to manage.
  - **Bedrock** — gives us access to foundation models through an API. We *use* a model; we don't train one.
- Key idea: *modern AI apps are mostly about connecting services and writing good prompts.*

---

## 5–10 min · Test a prompt in Amazon Bedrock

1. Console → **Amazon Bedrock** → **Playgrounds → Chat / Text**.
2. Select model: **Amazon → Nova Pro**.
3. Paste:

   > Create a 90-day learning roadmap for a beginner who wants to become a Cloud Engineer, is interested in automation, and can study 6 hours per week. Include skills, 2 certifications, and 3 portfolio projects.

4. Run it. Then change one thing (goal → *Cybersecurity Analyst*, hours → *15*) and run again.

Talking point: "Notice the output changes when the input changes. That prompt is the heart of our app — next we'll have code build it automatically from a form."

---

## 10–20 min · Build the Python Lambda function

1. Console → **Lambda** → **Create function** → *Author from scratch*
   - Name: `career-navigator`
   - Runtime: **Python 3.13** (or latest Python)
   - Leave "Create a new role with basic Lambda permissions" selected → **Create function**.
2. Replace the code in `lambda_function.py` with the workshop file → **Deploy**.
3. **Raise the timeout** (most common failure!):
   *Configuration → General configuration → Edit → Timeout: **30 sec***. The default 3 seconds is too short for an AI call.
4. **Give Lambda permission to call Bedrock:**
   *Configuration → Permissions → click the role name* → in IAM: *Add permissions → Create inline policy → JSON* → paste `setup/bedrock-invoke-policy.json` → name it `BedrockInvokeNova` → Create.
   *(Shortcut for workshops: attach the AWS managed policy `AmazonBedrockLimitedAccess`. Call out that the inline policy is the least-privilege version.)*
5. **Test:** *Test tab → Create new event* → paste `lambda/test-event.json` → **Test**.
   You should see `statusCode: 200` and a `roadmap` in the body.

Walk through the code together (it's ~100 lines, 4 labeled steps): read input → build prompt → call `bedrock.converse()` → return JSON.

Optional: *Configuration → Environment variables* → `MODEL_ID` lets you switch models without editing code.

---

## 20–28 min · Connect API Gateway

1. Console → **API Gateway** → **Create API** → **HTTP API** → *Build*.
2. *Add integration* → **Lambda** → choose `career-navigator`. API name: `career-navigator-api` → Next.
3. Configure routes: Method **POST**, Resource path **`/generate`** → Next.
4. Stage: keep **`$default`** with auto-deploy → Next → **Create**.
5. **Enable CORS** (left menu → *CORS* → Configure):
   - Access-Control-Allow-Origin: `*`
   - Access-Control-Allow-Headers: `content-type`
   - Access-Control-Allow-Methods: `POST`, `OPTIONS`
   - Save.
6. Copy the **Invoke URL** from the API's main page.

Quick test from CloudShell (the `>_` icon in the console top bar):
```bash
curl -X POST "<INVOKE_URL>/generate" \
  -H "Content-Type: application/json" \
  -d '{"goal":"Data Analyst","level":"Complete beginner","interests":"sports stats","hours":"5"}'
```

Talking point: "We now have a public AI API. Anything — a website, a mobile app, a chatbot — could call it."

---

## 28–37 min · Connect the frontend

1. Open `frontend/app.js` and set line 5:
   ```js
   const API_URL = "https://abc123.execute-api.us-east-1.amazonaws.com/generate";
   ```
   (Invoke URL **+ `/generate`**, no trailing slash.)
2. Open `frontend/index.html` in the browser (double-click works).
3. Walk through `app.js`: collect form values → `fetch()` POST → render the JSON into cards.
   Point out `esc()` — we never put AI output into the page without escaping it.

---

## 37–41 min · Test the application

Have participants try at least two personas and compare:
- Cloud Engineer · Complete beginner · automation · 6 hrs
- Cybersecurity Analyst · Career changer · healthcare · 10 hrs
- Their own real goal

Discussion prompt: "Is the plan realistic for the hours entered? How would you improve the prompt?"

---

## 41–44 min · Deploy the app

**Option A — AWS Amplify Hosting (recommended, no Git needed):**
1. Zip the **contents** of `frontend/` (so `index.html` is at the root of the zip).
2. Console → **AWS Amplify** → *Create new app* → **Deploy without Git** → drag in the zip → Save and deploy.
3. Open the `https://...amplifyapp.com` URL and share it.

**Option B — S3 static website:** create bucket → upload the 3 files → *Properties → Static website hosting* → enable → allow public read. (More steps; use only if Amplify is unavailable.)

---

## 44–45 min · Wrap up

- Recap: "You connected **API Gateway + Lambda + Bedrock** into a working generative-AI app."
- Ideas to extend: save roadmaps to DynamoDB, add a chat follow-up, compare Nova Lite (`us.amazon.nova-lite-v1:0`, faster/cheaper but invented a certification name in testing) via `MODEL_ID`, add Amazon Cognito sign-in.
- **Clean up** (or leave it and know it costs ~nothing when idle): delete the Amplify app, API, and Lambda function.

---

## Troubleshooting cheat sheet

| Symptom | Fix |
|---|---|
| Lambda test: `Task timed out after 3.00 seconds` | Raise timeout to 30 s (step 10–20, #3). |
| `AccessDeniedException` | Lambda role is missing the Bedrock policy, **or** Nova model access isn't enabled in this region. |
| `ValidationException ... on-demand throughput isn't supported` | Use the inference-profile ID with region prefix: `us.amazon.nova-pro-v1:0` (or `eu.` / `apac.` to match region). |
| Browser: "Failed to fetch" / CORS error in console | Configure CORS on the HTTP API (step 20–28, #5); check URL ends in `/generate`. |
| Browser: `{"message":"Not Found"}` | Wrong path — URL must be Invoke URL + `/generate`, route must be POST. |
| Browser: `Service Unavailable` after ~30 s | API Gateway's 30 s limit — lower `maxTokens` or retry. |
| Roadmap shows as plain text | Model returned non-JSON; app falls back to raw text. Still works — good prompt-engineering discussion point. |
| Where are the errors? | Lambda → *Monitor* → **View CloudWatch logs**. |
