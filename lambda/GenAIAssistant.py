import json, os
import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["DATA_BUCKET"]
HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}

# ---- Step 1: keyword based intent classifier (8 intents) ----
INTENTS = [
    ("company_specific", ["pwc", "kaartech", "cts", "cognizant"]),
    ("product_companies", ["product compan", "faang", "google", "amazon", "microsoft"]),
    ("coding_improvement", ["coding", "code", "dsa", "leetcode", "algorithm"]),
    ("interview_prep", ["interview", "hr round", "mock"]),
    ("company_targeting", ["which compan", "target", "apply", "where should"]),
    ("strength_weakness", ["strength", "weak", "improve", "lacking"]),
    ("my_scores", ["my score", "my result", "readiness", "how am i", "my marks"]),
]


def classify(question):
    q = question.lower()
    for intent, words in INTENTS:
        if any(w in q for w in words):
            return intent
    return "general_help"


# ---- Step 2: retrieval from S3 ----
def load_student(sid):
    try:
        return json.loads(s3.get_object(Bucket=BUCKET, Key=f"students/{sid}.json")["Body"].read())
    except Exception:
        return None


def analyse(s):
    a, c, i = float(s["aptitude"]), float(s["coding"]), float(s["interview"])
    score = round(a * 0.30 + c * 0.45 + i * 0.25, 2)
    cat = "Excellent" if score >= 85 else "Good" if score >= 70 else "Needs Improvement" if score >= 50 else "Critical"
    areas = {"aptitude": a, "coding": c, "interview": i}
    return a, c, i, score, cat, max(areas, key=areas.get), min(areas, key=areas.get)


COMPANY_TIPS = {
    "pwc": "PwC: strong aptitude + communication. Practise case-style questions and Excel/SQL basics.",
    "kaartech": "KaarTech: SAP/ERP exposure helps. Revise OOP, SQL and be ready for technical HR questions.",
    "cts": "CTS: aptitude + basic coding test. Focus on logical reasoning, arrays/strings, and a clear self-introduction.",
    "cognizant": "CTS (Cognizant): aptitude + basic coding. Revise logical reasoning, arrays/strings, self-introduction.",
}


# ---- Step 3: response templates (Context -> Finding -> Data -> Recommendation) ----
def respond(intent, q, s):
    a, c, i, score, cat, strong, weak = analyse(s)
    ctx = f"Hi {s.get('name', 'there')}, based on your latest assessment data: "
    data = f"Aptitude {a}, Coding {c}, Interview {i}, Readiness {score} ({cat})."

    if intent == "my_scores":
        return ctx + f"your readiness score is {score} and category is {cat}. " + data
    if intent == "product_companies":
        ok = score >= 85 and c >= 80
        finding = "You look ready for product companies." if ok else "You are not fully ready for product companies yet."
        return ctx + finding + " " + data + " Recommendation: push coding above 80 and keep readiness above 85."
    if intent == "coding_improvement":
        return ctx + f"your coding score is {c}. " + data + " Recommendation: solve 2 problems a day (arrays, strings, DP) and revisit mistakes weekly."
    if intent == "interview_prep":
        return ctx + f"your interview score is {i}. " + data + " Recommendation: do weekly mock interviews and prepare 3 project stories using STAR format."
    if intent == "company_targeting":
        comps = ("Google, Amazon, Microsoft, PwC, KaarTech" if cat == "Excellent"
                 else "Infosys, TCS, CTS, PwC" if cat == "Good"
                 else "Service-based startups and training programs" if cat == "Needs Improvement"
                 else "Build fundamentals first, then apply")
        return ctx + f"you fall in '{cat}'. " + data + f" Recommended targets: {comps}."
    if intent == "strength_weakness":
        return ctx + f"your strongest area is {strong} and weakest is {weak}. " + data + f" Recommendation: spend most practice time on {weak}."
    if intent == "company_specific":
        tip = next((v for k, v in COMPANY_TIPS.items() if k in q.lower()), "")
        return ctx + tip + " " + data
    return ("I can help with: your scores, product company readiness, coding improvement, interview prep, "
            "company targeting, strengths/weaknesses, and tips for PwC / KaarTech / CTS. Try asking one of these.")


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return {"statusCode": 400, "headers": HEADERS, "body": json.dumps({"error": "Invalid JSON"})}

    sid, question = body.get("studentId"), body.get("question", "")
    if not sid or not question:
        return {"statusCode": 400, "headers": HEADERS,
                "body": json.dumps({"error": "studentId and question are required"})}

    student = load_student(sid)
    if not student:
        return {"statusCode": 404, "headers": HEADERS, "body": json.dumps({"error": "Student not found"})}

    intent = classify(question)
    return {"statusCode": 200, "headers": HEADERS,
            "body": json.dumps({"intent": intent, "answer": respond(intent, question, student)})}
