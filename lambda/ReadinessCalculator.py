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


def resp(code, body):
    return {"statusCode": code, "headers": HEADERS, "body": json.dumps(body)}


def compute(student):
    a, c, i = float(student["aptitude"]), float(student["coding"]), float(student["interview"])
    score = round(a * 0.30 + c * 0.45 + i * 0.25, 2)

    if score >= 85:
        category, companies = "Excellent", ["Google", "Amazon", "Microsoft", "PwC", "KaarTech"]
    elif score >= 70:
        category, companies = "Good", ["Infosys", "TCS", "CTS", "PwC"]
    elif score >= 50:
        category, companies = "Needs Improvement", ["Service-based startups", "Training programs"]
    else:
        category, companies = "Critical", ["Focus on fundamentals first"]

    areas = {"aptitude": a, "coding": c, "interview": i}
    strength = max(areas, key=areas.get)
    weak = min(areas, key=areas.get)
    tips = {
        "aptitude": "Practice quantitative and logical reasoning daily (30 min).",
        "coding": "Solve 2 problems/day on LeetCode or HackerRank, focus on arrays, strings, DP.",
        "interview": "Do weekly mock interviews and practise explaining your projects.",
    }
    return {
        "studentId": student["studentId"], "name": student.get("name", ""),
        "aptitude": a, "coding": c, "interview": i,
        "readiness_score": score, "category": category,
        "strength": strength, "weak_area": weak,
        "suggestion": tips[weak], "recommended_companies": companies,
    }


def lambda_handler(event, context):
    sid = (event.get("pathParameters") or {}).get("id")
    if not sid:
        return resp(400, {"error": "studentId missing"})
    try:
        obj = s3.get_object(Bucket=BUCKET, Key=f"students/{sid}.json")
        student = json.loads(obj["Body"].read())
    except s3.exceptions.NoSuchKey:
        return resp(404, {"error": "Student not found"})
    except Exception as e:
        print("Error:", e)
        return resp(500, {"error": "Internal error"})
    return resp(200, compute(student))
