"""
AI STEM Career Navigator - Lambda backend

Flow:  Browser --POST /generate--> API Gateway (HTTP API) --> this Lambda --> Amazon Bedrock (Nova)

The function:
  1. Reads the user's answers from the request body
  2. Builds a prompt
  3. Calls Amazon Nova through the Bedrock Converse API
  4. Returns the roadmap as JSON to the browser
"""

import json
import os

import boto3

# Change the model in Lambda > Configuration > Environment variables (no code edit needed).
# "us." / "eu." / "apac." prefixes are cross-region inference profiles, required by Nova in most regions.
MODEL_ID = os.environ.get("MODEL_ID", "us.amazon.nova-pro-v1:0")

bedrock = boto3.client("bedrock-runtime")

CORS_HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "POST,OPTIONS",
}

SYSTEM_PROMPT = (
    "You are a friendly, practical STEM career coach. "
    "You create realistic learning roadmaps for people entering tech careers. "
    "Recommend real, widely recognized certifications and free or low-cost resources. "
    "Respect the learner's weekly study hours when planning. "
    "Always reply with valid JSON only - no markdown, no commentary."
)


def build_prompt(goal, level, interests, hours):
    return f"""Create a personalized career roadmap for this learner.

Career goal: {goal}
Current experience level: {level}
Interests: {interests}
Hours available to study per week: {hours}

Return JSON with exactly this shape:
{{
  "summary": "2-3 sentence encouraging overview of the path",
  "skills": ["5-7 core skills to learn, in order"],
  "certifications": [
    {{"name": "certification name", "why": "one sentence on why it matters"}}
  ],
  "projects": [
    {{"title": "portfolio project", "description": "one or two sentences"}}
  ],
  "plan_90_days": [
    {{"phase": "Days 1-30", "focus": "theme", "tasks": ["3-4 weekly-sized tasks"]}},
    {{"phase": "Days 31-60", "focus": "theme", "tasks": ["..."]}},
    {{"phase": "Days 61-90", "focus": "theme", "tasks": ["..."]}}
  ],
  "next_step": "one concrete thing to do today"
}}

Give 2-3 certifications and 3 projects.
Certifications must be real, well-known industry certifications (not course names) that match the
learner's experience level - entry-level ones for beginners. Do not invent certification names.
Make the 90-day plan fit {hours} hours per week; at most one certification exam in the 90 days."""


def response(status, body):
    return {"statusCode": status, "headers": CORS_HEADERS, "body": json.dumps(body)}


def parse_model_json(text):
    """Models sometimes wrap JSON in ```fences``` or add a sentence - pull out the {...} part."""
    start, end = text.find("{"), text.rfind("}")
    if start == -1 or end == -1:
        return None
    try:
        return json.loads(text[start : end + 1])
    except json.JSONDecodeError:
        return None


def lambda_handler(event, context):
    # Browser CORS preflight
    method = event.get("requestContext", {}).get("http", {}).get("method", "POST")
    if method == "OPTIONS":
        return response(200, {})

    # 1. Read the input
    try:
        data = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return response(400, {"error": "Request body must be JSON."})

    goal = str(data.get("goal", "")).strip()[:100]
    level = str(data.get("level", "Beginner")).strip()[:50]
    interests = str(data.get("interests", "")).strip()[:300]
    hours = str(data.get("hours", "5")).strip()[:10]

    if not goal:
        return response(400, {"error": "Please enter a career goal."})

    # 2. Build the prompt, 3. call Bedrock
    try:
        result = bedrock.converse(
            modelId=MODEL_ID,
            system=[{"text": SYSTEM_PROMPT}],
            messages=[
                {"role": "user", "content": [{"text": build_prompt(goal, level, interests, hours)}]}
            ],
            inferenceConfig={"maxTokens": 2000, "temperature": 0.5},
        )
    except Exception as e:
        print(f"Bedrock error: {e}")  # shows up in CloudWatch Logs
        return response(500, {"error": f"Bedrock call failed: {type(e).__name__}. Check CloudWatch Logs."})

    text = result["output"]["message"]["content"][0]["text"]

    # 4. Return the roadmap
    roadmap = parse_model_json(text)
    if roadmap is None:
        # Still useful: the frontend will show the raw text
        return response(200, {"raw": text})
    return response(200, {"roadmap": roadmap})
