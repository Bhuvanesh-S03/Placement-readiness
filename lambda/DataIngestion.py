import json, os, datetime
import boto3

s3 = boto3.client("s3")
BUCKET = os.environ["DATA_BUCKET"]          # student-data-bucket-yourname
HEADERS = {
    "Content-Type": "application/json",
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Content-Type",
    "Access-Control-Allow-Methods": "GET,POST,OPTIONS",
}
REQUIRED = ["studentId", "name", "email", "aptitude", "coding", "interview"]


def resp(code, body):
    return {"statusCode": code, "headers": HEADERS, "body": json.dumps(body)}


def lambda_handler(event, context):
    try:
        data = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return resp(400, {"error": "Invalid JSON"})

    missing = [f for f in REQUIRED if f not in data or data[f] in ("", None)]
    if missing:
        return resp(400, {"error": f"Missing fields: {', '.join(missing)}"})

    for f in ("aptitude", "coding", "interview"):
        try:
            data[f] = float(data[f])
        except (TypeError, ValueError):
            return resp(400, {"error": f"{f} must be a number"})
        if not 0 <= data[f] <= 100:
            return resp(400, {"error": f"{f} must be between 0 and 100"})

    data["timestamp"] = datetime.datetime.utcnow().isoformat()
    key = f"students/{data['studentId']}.json"
    try:
        s3.put_object(Bucket=BUCKET, Key=key, Body=json.dumps(data),
                      ContentType="application/json")
    except Exception as e:
        print("S3 error:", e)
        return resp(500, {"error": "Could not save student"})
    return resp(200, {"message": "Student saved", "studentId": data["studentId"]})
