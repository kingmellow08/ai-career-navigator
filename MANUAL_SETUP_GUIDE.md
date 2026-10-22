# Manual Setup Guide — Build the AI STEM Career Navigator in the AWS Console

This guide walks you through building and deploying the whole app **by hand in the AWS Management Console** — no command line or AI tools required. Every step was tested end to end in a real AWS account.

**What you'll build**

```
 Browser (HTML/CSS/JS on AWS Amplify)
      │  POST /generate  {goal, level, interests, hours}
      ▼
 Amazon API Gateway (HTTP API)
      │
      ▼
 AWS Lambda (Python) ── builds the prompt
      │
      ▼
 Amazon Bedrock ── Amazon Nova Pro writes the roadmap
```

**Time:** about 30–40 minutes the first time.
**Cost:** pennies. Lambda and API Gateway stay within the free tier for workshop use; each roadmap costs a fraction of a cent in Bedrock.

---

## Part 0 — Prerequisites

1. An **AWS account** and a user that can use Bedrock, Lambda, IAM, API Gateway, and Amplify (an administrator user is simplest for a workshop).
2. A web browser and a text editor (VS Code, Notepad, TextEdit — anything works).
3. The project files. Either:
   - Go to **https://github.com/kingmellow08/ai-career-navigator** → green **Code** button → **Download ZIP** → unzip it, **or**
   - `git clone https://github.com/kingmellow08/ai-career-navigator.git`

   You'll use these files:

   | File | Used in |
   |---|---|
   | `lambda/lambda_function.py` | Part 2 — Lambda code |
   | `lambda/test-event.json` | Part 2 — Lambda test |
   | `setup/bedrock-invoke-policy.json` | Part 2 — permissions |
   | `frontend/index.html`, `style.css`, `app.js` | Parts 4–5 — website |

4. **Pick one region and stay in it for every step.** This guide uses **US East (N. Virginia) `us-east-1`**. Choose it from the region dropdown in the top-right of the console.

> Using a region outside the US? Nova model IDs start with a geography prefix: `us.` for US regions, `eu.` for Europe, `apac.` for Asia Pacific. See the note in Part 2, step 6.

---

## Part 1 — Try the model in the Bedrock playground (5 min)

1. In the console search bar, type **Bedrock** and open **Amazon Bedrock**.
2. **Check model access** (one time per account):
   - Left menu → **Model access** (sometimes under *Bedrock configurations*).
   - Find **Amazon → Nova Pro**. If it says **Access granted**, continue. If not, click **Modify model access** (or **Enable specific models**), tick **Nova Pro** (and **Nova Lite** if you want to compare), then **Next → Submit**. Amazon models are usually granted instantly.
   - *In many accounts, Amazon models are enabled by default and this page just confirms it.*
3. Left menu → **Playgrounds → Chat / Text**.
4. Click **Select model** → **Amazon** → **Nova Pro** → **Apply**.
5. Paste this prompt and click **Run**:

   ```
   Create a 90-day learning roadmap for a beginner who wants to become a Cloud Engineer,
   is interested in automation, and can study 6 hours per week. Include skills,
   2 entry-level certifications, and 3 portfolio projects.
   ```

6. Change one input (for example, *Cybersecurity Analyst* or *15 hours*) and run it again. Notice how the output changes. **This prompt is the heart of the app.** Next, code will build it automatically from a web form.

✅ **Checkpoint:** the playground returns a roadmap.

---

## Part 2 — Create the Lambda function (10 min)

### 2a. Create the function

1. Search for **Lambda** → open it → **Create function**.
2. Choose **Author from scratch**:
   - **Function name:** `career-navigator`
   - **Runtime:** **Python 3.13** (or the newest Python listed)
   - **Architecture:** leave as default
   - **Permissions:** leave **Create a new role with basic Lambda permissions** selected
3. Click **Create function**.

### 2b. Add the code

4. On the **Code** tab, open `lambda_function.py` in the editor. **Select all and delete** the sample code.
5. Open `lambda/lambda_function.py` from the project files, copy **everything**, and paste it into the editor.
6. Click **Deploy** (or press Ctrl+S / Cmd+S, then Deploy). Wait for *"Successfully updated the function"*.

> **Model note:** line 20 sets the model: `us.amazon.nova-pro-v1:0`. If you're in an EU region, either change `us.` to `eu.` here, or add an environment variable (Configuration → Environment variables → Edit → Add) with key `MODEL_ID` and value `eu.amazon.nova-pro-v1:0`.

### 2c. Raise the timeout ⚠️ (the #1 cause of failures)

7. **Configuration** tab → **General configuration** → **Edit**.
8. Set **Timeout** to **0 min 30 sec**. (Optionally set Memory to 256 MB.) → **Save**.

   *The default of 3 seconds is too short. An AI response takes about 3–8 seconds.*

### 2d. Allow Lambda to call Bedrock

9. **Configuration** tab → **Permissions** → under *Execution role*, click the **role name** (it looks like `career-navigator-role-abc123`). The IAM console opens in a new tab.
10. **Add permissions** → **Create inline policy**.
11. Click the **JSON** toggle, delete what's there, and paste the contents of `setup/bedrock-invoke-policy.json`:

    ```json
    {
      "Version": "2012-10-17",
      "Statement": [
        {
          "Sid": "InvokeNovaModels",
          "Effect": "Allow",
          "Action": ["bedrock:InvokeModel", "bedrock:InvokeModelWithResponseStream"],
          "Resource": [
            "arn:aws:bedrock:*::foundation-model/amazon.nova-*",
            "arn:aws:bedrock:*:*:inference-profile/*amazon.nova-*"
          ]
        }
      ]
    }
    ```

12. **Next** → Policy name: `BedrockInvokeNova` → **Create policy**. Close the IAM tab.

    *This policy only allows calling Amazon Nova models, a "least privilege" setup. A quicker but broader option is to attach the AWS managed policy `AmazonBedrockLimitedAccess`.*

### 2e. Test the function

13. Back in Lambda → **Test** tab → **Create new event**.
    - Event name: `cloud-engineer`
    - Delete the sample JSON and paste the contents of `lambda/test-event.json`
    - **Save** → **Test**.
14. Expand **Details**. You should see:
    - `"statusCode": 200`
    - a `body` containing `"roadmap"` with `summary`, `skills`, `certifications`, `projects`, `plan_90_days`, and `next_step`.

✅ **Checkpoint:** status 200 with a roadmap. If not, see [Troubleshooting](#troubleshooting).

---

## Part 3 — Create the API Gateway HTTP API (8 min)

1. Search for **API Gateway** → open it → **Create API**.
2. Under **HTTP API**, click **Build**.
3. **Create and configure integrations:**
   - **Add integration** → choose **Lambda**
   - **AWS Region:** `us-east-1`
   - **Lambda function:** select `career-navigator`
   - **API name:** `career-navigator-api`
   - → **Next**
4. **Configure routes:**
   - **Method:** `POST`
   - **Resource path:** `/generate`
   - **Integration target:** `career-navigator`
   - → **Next**
5. **Define stages:** keep **`$default`** with **Auto-deploy** on → **Next** → **Create**.
6. **Enable CORS** (lets the browser call your API from another website):
   - Left menu → under *Develop*, click **CORS** → **Configure**
   - **Access-Control-Allow-Origin:** type `*` → **Add**
   - **Access-Control-Allow-Headers:** type `content-type` → **Add**
   - **Access-Control-Allow-Methods:** select `POST` and `OPTIONS`
   - **Save**
7. Left menu → **API: career-navigator-api** (top of the menu) → copy the **Invoke URL**. It looks like:

   ```
   https://abc123xyz.execute-api.us-east-1.amazonaws.com
   ```

   **Your full app URL is the Invoke URL + `/generate`.** Write it down.

### Test the API (optional but recommended)

8. Open **AWS CloudShell** (the `>_` icon in the top bar of the console) and run, with your URL:

   ```bash
   curl -X POST "https://abc123xyz.execute-api.us-east-1.amazonaws.com/generate" \
     -H "Content-Type: application/json" \
     -d '{"goal":"Data Analyst","level":"Complete beginner","interests":"sports stats","hours":"5"}'
   ```

✅ **Checkpoint:** a JSON roadmap comes back after a few seconds.

---

## Part 4 — Connect the frontend (5 min)

1. Open `frontend/app.js` in your text editor.
2. Replace the placeholder on **line 5** with your full URL (Invoke URL + `/generate`, no trailing slash):

   ```js
   const API_URL = "https://abc123xyz.execute-api.us-east-1.amazonaws.com/generate";
   ```

3. Save the file.
4. Double-click `frontend/index.html` to open it in your browser.
5. Fill in the form (for example *Cloud Engineer*, *Complete beginner*, *automation*, *6 hours*) → **Generate my roadmap**.

✅ **Checkpoint:** after about 5–10 seconds you see cards for Summary, Skills, Certifications, Projects, the 90-Day Plan, and Do This Today.

---

## Part 5 — Deploy the website with AWS Amplify (5 min)

1. **Make a zip of the frontend files.** The files must be at the *root* of the zip, not inside a folder:
   - **Windows:** open the `frontend` folder → select `index.html`, `style.css`, `app.js` → right-click → **Send to → Compressed (zipped) folder**.
   - **Mac:** open the `frontend` folder → select the 3 files → right-click → **Compress 3 Items**.
   - ❌ Don't zip the `frontend` folder itself. Amplify would then show a blank page or a 404.
2. Search for **AWS Amplify** → open it → **Create new app** (or **Deploy an app**).
3. Choose **Deploy without Git** → **Next**.
4. **App name:** `career-navigator` · **Branch name:** `main`.
5. **Drag and drop** your zip file → **Save and deploy**.
6. Wait about 30 seconds for the status to show **Deployed**. Click the **Domain** link, which looks like:

   ```
   https://main.d1a2b3c4d5.amplifyapp.com
   ```

7. Generate a roadmap from the live site. 🎉 Share the link!

**Updating the site later:** change the files, zip them again, then in Amplify open the app → **Deploy updates** → drag in the new zip.

### Protect your API (recommended if you share the link publicly)

Anyone with the link can generate roadmaps on your AWS bill. To cap usage:
API Gateway → `career-navigator-api` → left menu **Protect → Throttling** → select the `$default` stage → **Edit** → set **Rate limit** `5` and **Burst limit** `10` → **Save**.

---

## Troubleshooting

| What you see | Fix |
|---|---|
| Lambda test: `Task timed out after 3.00 seconds` | Part 2c: set the timeout to 30 seconds. |
| `AccessDeniedException` | The Lambda role is missing the Bedrock policy (Part 2d), **or** Nova model access isn't granted in this region (Part 1, step 2). |
| `ValidationException ... on-demand throughput isn't supported` | Use the model ID **with** the geography prefix: `us.amazon.nova-pro-v1:0` (or `eu.` / `apac.`). |
| `Bedrock call failed` in the response | Open Lambda → **Monitor** → **View CloudWatch logs** → newest log stream to see the real error. |
| Browser: *"Something went wrong: Failed to fetch"* | CORS isn't configured (Part 3, step 6), or the URL in `app.js` is wrong. Press F12 → Console to see the error. |
| Browser: `Not Found` | The URL must end in `/generate`, and the route must be `POST /generate`. |
| Browser: `Service Unavailable` after about 30 seconds | API Gateway has a 30-second limit. Try again. |
| Amplify site is blank or 404 | You zipped the folder instead of the files. Re-zip the 3 files and redeploy. |
| Roadmap shows as plain text | The model didn't return JSON. The app falls back to showing the text, so it still works. |
| Wrong or made-up certification names | Make sure you're using **Nova Pro**. In testing, Nova Lite invented a certification name. |

---

## Clean up (when you're done)

Delete in this order:

1. **Amplify** → select `career-navigator` → **Actions** (or App settings → General) → **Delete app**.
2. **API Gateway** → select `career-navigator-api` → **Delete**.
3. **Lambda** → select `career-navigator` → **Actions → Delete**.
4. **IAM** → **Roles** → search `career-navigator` → select the role → **Delete**.
5. *(Optional)* **CloudWatch** → **Log groups** → delete `/aws/lambda/career-navigator`.

If you leave everything running, it costs essentially nothing while idle.

---

## Ideas to extend it

- Save each roadmap to **DynamoDB** and add a "My roadmaps" page.
- Add **Amazon Cognito** sign-in.
- Compare models by changing the `MODEL_ID` environment variable.
- Improve the prompt: add salary ranges, local job market tips, or free learning resources for each skill.
