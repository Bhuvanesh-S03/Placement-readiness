"""Generate 50 synthetic students (STU001-STU050) and upload to S3.
Usage:  pip install boto3
        aws configure            (or set credentials from Learner Lab -> AWS Details)
        python generate_data.py student-data-bucket-yourname
"""
import json, random, sys
import boto3

bucket = sys.argv[1]
s3 = boto3.client("s3", region_name="us-east-1")
branches = ["IT", "CSE", "ECE", "EEE", "MECH"]

for n in range(1, 51):
    sid = f"STU{n:03d}"
    s = {
        "studentId": sid, "name": f"Student {n}", "email": f"{sid.lower()}@college.edu",
        "batch": "2026", "branch": random.choice(branches),
        "aptitude": random.randint(35, 98),
        "coding": random.randint(40, 95),
        "interview": random.randint(30, 92),
    }
    s3.put_object(Bucket=bucket, Key=f"students/{sid}.json", Body=json.dumps(s),
                  ContentType="application/json")
    print("uploaded", sid)
