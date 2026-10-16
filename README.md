# PlacementIQ

Cloud-Based Placement Readiness Analytics System. Fully serverless, costs a few cents.

## Tech stack

| Layer | Technology |
|---|---|
| Frontend | HTML, CSS, JavaScript (static site) hosted on **Amazon S3** |
| API | **Amazon API Gateway** (REST, 4 endpoints) |
| Backend | **AWS Lambda**, Python 3.11, boto3 |
| Storage | **Amazon S3** (JSON files, versioning + SSE-S3 encryption) |
| Cataloging | **AWS Glue** crawler |
| Analytics | **Amazon Athena** (SQL on S3) |
| Security | **IAM** role, S3 Block Public Access, SSE-S3 (AES-256) |
| Monitoring | **Amazon CloudWatch** Logs |
| "AI" | Weighted scoring model + rule-based RAG assistant (no Bedrock needed) |

Replace `yourname` below with something unique (S3 bucket names are global). Use region **us-east-1**.

---

## Part A – Storage (S3)

1. Console -> **S3** -> Create bucket: `student-data-bucket-yourname`. Turn on **Block all public access**, **Versioning**, and default encryption **SSE-S3**.
2. Create `analytics-results-bucket-yourname` with the same settings.
3. Create `frontend-hosting-bucket-yourname`. Versioning + SSE-S3 on, but **untick Block public access** (needed for the website).

## Part B – Data

4. Get credentials on your machine (`aws configure`), then:
   ```
   pip install boto3
   python generate_data.py student-data-bucket-yourname
   ```
   This uploads STU001-STU050 into the `students/` folder.

## Part C – Glue + Athena (analytics)

5. **Glue** -> Crawlers -> Create: name `student-data-crawler`, source `s3://student-data-bucket-yourname/students/`, IAM role (your Glue role), target database `placement_db` (create it), run **on demand**. Run it -> table `student_data` appears.
6. **Athena** -> Settings -> set query result location `s3://analytics-results-bucket-yourname/`.
7. Run the queries in `athena_queries.sql`. Take screenshots.

## Part D – Lambda (4 functions)

8. **IAM role**: in your own account create a role `PlacementLambdaRole` with trusted entity *Lambda* and policies `AmazonS3FullAccess` and `AWSLambdaBasicExecutionRole` (a student sandbox's `LabRole` is not available in a personal account).
9. For each file in `lambda/` create a function (Python 3.11, role `PlacementLambdaRole`, timeout 30 s, 128 MB), paste the code, **Deploy**:

   | Function name | File |
   |---|---|
   | DataIngestion | `DataIngestion.py` |
   | ReadinessCalculator | `ReadinessCalculator.py` |
   | GenAIAssistant | `GenAIAssistant.py` |
   | ListStudents | `ListStudents.py` |

10. For **every** function: Configuration -> Environment variables -> add `DATA_BUCKET` = `student-data-bucket-yourname`.
11. Test with a test event, e.g. for ReadinessCalculator: `{"pathParameters": {"id": "STU001"}}`.

## Part E – API Gateway

12. **API Gateway** -> Create **REST API** `placement-readiness-api`.
13. Create resources and methods, each with **Lambda Proxy integration** ON:

    | Resource | Method | Lambda |
    |---|---|---|
    | `/ingest` | POST | DataIngestion |
    | `/readiness` -> `/{id}` | GET | ReadinessCalculator |
    | `/assistant` | POST | GenAIAssistant |
    | `/students` | GET | ListStudents |

14. On each resource: Actions -> **Enable CORS** (this also adds OPTIONS).
15. Actions -> **Deploy API** -> new stage `prod`. Copy the **Invoke URL**.
16. Quick test in browser: `INVOKE_URL/students`.

## Part F – Frontend

17. Open `frontend/index.html`, set `const API = "<your invoke url>"` (no trailing slash).
18. Upload `index.html` to `frontend-hosting-bucket-yourname`. Properties -> **Static website hosting** -> Enable, index document `index.html`.
19. Permissions -> Bucket policy (replace the name):
    ```json
    {
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": "*",
        "Action": "s3:GetObject",
        "Resource": "arn:aws:s3:::frontend-hosting-bucket-yourname/*"
      }]
    }
    ```
20. Open the **website endpoint URL** from the Properties tab. Add a student as faculty, then check readiness and chat as a student.

## Part G – Security checklist (Module 4)

- SSE-S3 on all 3 buckets (Properties -> Default encryption).
- Block Public Access ON for student-data and analytics buckets.
- Versioning ON for all buckets.
- Lambda logs visible in CloudWatch -> Log groups.

---

## How the model works

- `readiness = aptitude*0.30 + coding*0.45 + interview*0.25`
- Excellent >= 85, Good 70-85, Needs Improvement 50-70, Critical < 50
- Assistant: keyword **intent classifier** (8 intents) -> **retrieve** student JSON from S3 -> **fill response template**.

## Quick test checklist

- Ingest: POST `/ingest` with `{"studentId":"STU051","name":"Test","email":"t@t.com","aptitude":88,"coding":92,"interview":85}`
- GET `/readiness/STU051` -> score 89.65, Excellent
- POST `/assistant` with `{"studentId":"STU051","question":"Am I ready for product companies?"}`
- GET `/students` -> sorted list

## Notes

- Your report also mentions faculty/student login, a quiz creator and a leaderboard. The included `index.html` covers add student, analyse students, readiness view and chatbot. Login, quiz and leaderboard are extras you can add later (leaderboard = the sorted `/students` result).
- Delete the API, Lambdas and buckets when done to avoid charges.
