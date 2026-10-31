import requests
import json
import time
from benchmark_tests import tests


BASE_URL = "http://127.0.0.1:8000"

results = []


# ============================================================
# RUN ALL BENCHMARK TESTS
# ============================================================

for i, test in enumerate(tests, 1):

    print("\n" + "=" * 70)
    print(f"TEST {i}: {test['name']}")
    print("=" * 70)

    # --------------------------------------------------------
    # STEP 1: Upload / paste source code
    # --------------------------------------------------------

    extension = {
        "Python": ".py",
        "Java": ".java",
        "C++": ".cpp",
        "JavaScript": ".js"
    }.get(test["language"], ".txt")

    filename = f"benchmark_{i}{extension}"

    try:

        upload_response = requests.post(
            f"{BASE_URL}/paste-code",
            json={
                "filename": filename,
                "code": test["code"]
            },
            timeout=60
        )

        print("Paste Code Status:", upload_response.status_code)

        if upload_response.status_code != 200:

            print("UPLOAD ERROR:")
            print(upload_response.text)

            results.append({
                "test": test["name"],
                "language": test["language"],
                "expected": test["expected"],
                "status": "UPLOAD ERROR",
                "error": upload_response.text
            })

            continue

        upload_data = upload_response.json()

        print(
            "Indexed:",
            upload_data.get("message", "Unknown")
        )

        # --------------------------------------------------------
        # STEP 2: Review uploaded source code
        # --------------------------------------------------------

        question = (
            "Perform a comprehensive AI code review of the complete "
            "source code that was just uploaded. "
            "Check bugs, runtime errors, security vulnerabilities, "
            "performance problems, and code quality issues. "
            "Report only issues directly supported by the uploaded "
            "source code. Do not use previous source code."
        )

        review_response = requests.post(
            f"{BASE_URL}/review",
            json={
                "question": question
            },
            timeout=180
        )

        print("Review Status:", review_response.status_code)

        # --------------------------------------------------------
        # STEP 2A: Handle rate limiting
        # --------------------------------------------------------

        if review_response.status_code == 429:

            print("RATE LIMITED - waiting 30 seconds before retry...")

            time.sleep(30)

            review_response = requests.post(
                f"{BASE_URL}/review",
                json={
                    "question": question
                },
                timeout=180
            )

            print(
                "Retry Status:",
                review_response.status_code
            )

            if review_response.status_code == 429:

                print("RETRY ALSO RATE LIMITED.")

                results.append({
                    "test": test["name"],
                    "language": test["language"],
                    "expected": sorted(set(test["expected"])),
                    "status": "RATE_LIMITED",
                    "error": review_response.text
                })

                continue

        # --------------------------------------------------------
        # STEP 2B: Handle other review errors
        # --------------------------------------------------------

        if review_response.status_code != 200:

            print("REVIEW ERROR:")
            print(review_response.text)

            results.append({
                "test": test["name"],
                "language": test["language"],
                "expected": sorted(set(test["expected"])),
                "status": "REVIEW ERROR",
                "error": review_response.text
            })

            continue

        # --------------------------------------------------------
        # STEP 2C: Parse review JSON
        # --------------------------------------------------------

        try:

            review_data = review_response.json()

        except ValueError:

            print("INVALID JSON RESPONSE:")
            print(review_response.text)

            results.append({
                "test": test["name"],
                "language": test["language"],
                "expected": sorted(set(test["expected"])),
                "status": "INVALID JSON",
                "error": review_response.text
            })

            continue

        review = review_data.get("review", {})

        # --------------------------------------------------------
        # Prevent Groq API rate-limit errors
        # Wait after every successful review
        # --------------------------------------------------------

        print("Waiting 8 seconds before next test...")
        time.sleep(8)

        # --------------------------------------------------------
        # STEP 3: Extract detected categories
        # --------------------------------------------------------

        detected = []

        # Bugs
        if review.get("bugs"):
            detected.append("bug")

        # Runtime / execution errors
        if review.get("errors"):
            detected.append("error")

        # Security
        security = review.get("security")

        if security:

            security_issues = security.get("issues")

            if security_issues:
                detected.append("security")

        # Performance
        performance = review.get("performance")

        if performance:

            performance_issues = performance.get("issues")

            if performance_issues:
                detected.append("performance")

        # Remove duplicates
        detected = sorted(set(detected))

        # --------------------------------------------------------
        # Expected categories
        # --------------------------------------------------------

        expected = sorted(set(test["expected"]))

        # --------------------------------------------------------
        # STEP 4: Compare expected vs detected
        # --------------------------------------------------------

        correct = all(
            category in detected
            for category in expected
        )

        print("Expected :", expected)
        print("Detected :", detected)
        print(
            "Result   :",
            "PASS" if correct else "FAIL"
        )

        # --------------------------------------------------------
        # Save successful result
        # --------------------------------------------------------

        results.append({
            "test": test["name"],
            "language": test["language"],
            "expected": expected,
            "detected": detected,
            "correct": correct,
            "status": "SUCCESS"
        })

    # ------------------------------------------------------------
    # Handle unexpected Python errors
    # ------------------------------------------------------------

    except requests.exceptions.Timeout:

        print("REQUEST TIMEOUT.")

        results.append({
            "test": test["name"],
            "language": test["language"],
            "expected": sorted(set(test["expected"])),
            "status": "TIMEOUT"
        })

    except requests.exceptions.ConnectionError:

        print("CONNECTION ERROR.")
        print("Make sure the FastAPI backend is running.")

        results.append({
            "test": test["name"],
            "language": test["language"],
            "expected": sorted(set(test["expected"])),
            "status": "CONNECTION ERROR"
        })

    except Exception as e:

        print("EXCEPTION:", str(e))

        results.append({
            "test": test["name"],
            "language": test["language"],
            "expected": sorted(set(test["expected"])),
            "status": "EXCEPTION",
            "error": str(e)
        })


# ============================================================
# SAVE RESULTS
# ============================================================

with open(
    "benchmark_results.json",
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        results,
        f,
        indent=2,
        ensure_ascii=False
    )


# ============================================================
# SUMMARY
# ============================================================

successful = [
    r
    for r in results
    if r.get("status") == "SUCCESS"
]

passed = [
    r
    for r in successful
    if r.get("correct") is True
]

failed = [
    r
    for r in successful
    if r.get("correct") is False
]

rate_limited = [
    r
    for r in results
    if r.get("status") == "RATE_LIMITED"
]

errors = [
    r
    for r in results
    if r.get("status") not in [
        "SUCCESS",
        "RATE_LIMITED"
    ]
]


# ============================================================
# FINAL BENCHMARK REPORT
# ============================================================

print("\n" + "=" * 70)
print("BENCHMARK COMPLETE")
print("=" * 70)

print(f"Total Tests      : {len(tests)}")
print(f"Successful       : {len(successful)}")
print(f"Passed           : {len(passed)}")
print(f"Failed           : {len(failed)}")
print(f"Rate Limited     : {len(rate_limited)}")
print(f"Other Errors     : {len(errors)}")


# ------------------------------------------------------------
# Accuracy
# ------------------------------------------------------------

if successful:

    accuracy = (
        len(passed) /
        len(successful)
    ) * 100

    print(f"Accuracy         : {accuracy:.2f}%")

else:

    print("Accuracy         : N/A")


# ------------------------------------------------------------
# Test-by-test summary
# ------------------------------------------------------------

print("\n" + "-" * 70)
print("TEST RESULTS")
print("-" * 70)

for index, result in enumerate(results, 1):

    test_name = result.get(
        "test",
        "Unknown"
    )

    status = result.get(
        "status",
        "UNKNOWN"
    )

    if status == "SUCCESS":

        result_text = (
            "PASS"
            if result.get("correct")
            else "FAIL"
        )

        print(
            f"{index:02d}. "
            f"{test_name:<35} "
            f"{result_text}"
        )

    else:

        print(
            f"{index:02d}. "
            f"{test_name:<35} "
            f"{status}"
        )


# ------------------------------------------------------------
# Results file
# ------------------------------------------------------------

print("\nResults saved to:")
print("benchmark_results.json")

print("=" * 70)