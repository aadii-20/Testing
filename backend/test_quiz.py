import requests
try:
    resp = requests.post("http://localhost:9010/generate-quiz", json={
        "subject": "Science",
        "chapter": "Chapter 1",
        "type": "MCQ",
        "num_questions": 5,
        "difficulty": "Medium",
        "standard": "8"
    })
    print("Status:", resp.status_code)
    print("Headers:", resp.headers)
    print("Body:", resp.text)
except Exception as e:
    print("Error:", e)
