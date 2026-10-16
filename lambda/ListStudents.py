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

def category_of(score):
    if score >= 85: return "Excellent"
    if score >= 70: return "Good"
    if score >= 50: return "Needs Improvement"
    return "Critical"

def lambda_handler(event, context):
    students = []
    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=BUCKET, Prefix="students/"):
        for item in page.get("Contents", []):
            if not item["Key"].endswith(".json"):
                continue
            s = json.loads(s3.get_object(Bucket=BUCKET, Key=item["Key"])["Body"].read())
            score = round(float(s["aptitude"]) * 0.30 + float(s["coding"]) * 0.45
                          + float(s["interview"]) * 0.25, 2)
            students.append({
                "studentId": s["studentId"], "name": s.get("name", ""),
                "aptitude": s["aptitude"], "coding": s["coding"], "interview": s["interview"],
                "readiness_score": score, "category": category_of(score),
            })
    students.sort(key=lambda x: x["readiness_score"], reverse=True)
    return {"statusCode": 200, "headers": HEADERS,
            "body": json.dumps({"count": len(students), "students": students})}