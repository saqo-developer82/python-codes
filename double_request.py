import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor
import json


def make_request(request_id):
    """Make a single request to the Laravel endpoint"""

    url = "http://fieldpulse.loc/v2.5/invoice/30744"

    headers = {
        'Connection': 'keep-alive',
        'Authorization': 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJpc3MiOiJodHRwOi8vZmllbGRwdWxzZS5sb2MvYXV0aG9yaXplIiwiaWF0IjoxNzUxMDEyMDE2LCJleHAiOjE3NTM2MDQwMTYsIm5iZiI6MTc1MTAxMjAxNiwianRpIjoiMUJwQnlaZGZsQU01dkJFSiIsInN1YiI6IjIwMyIsInBydiI6IjkyNjRjZTc0YTNkNzhiOTU4Yzc2NmY3MTBkNjJkMzgxOTg1MzQ0ODEiLCJoYXNfdXNlZF9tYXN0ZXJfcGFzc3dvcmQiOnRydWUsInN3aXRjaGVkX2Zyb21fdXNlciI6bnVsbCwiaGFzX2xvZ2dlZF9pbl91c2luZ19zc28iOmZhbHNlLCJoYXNfbG9nZ2VkX2luX2Zyb21femFwaWVyIjpmYWxzZX0.1we_jWxJxoToyal2IEtUxBjRsVigpZrFrZYjMqhm1yQ',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.141 Safari/537.36',
        'Content-Type': 'application/json',
        'Accept': '*/*',
        'Origin': 'https://webapp.fieldpulse.com',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://webapp.fieldpulse.com/',
        'Accept-Language': 'en-US,en;q=0.9,ru-US;q=0.8,ru;q=0.7'
    }

    data = {"status": 3}

    try:
        start_time = time.time()
        response = requests.put(url, headers=headers, json=data, timeout=30)
        end_time = time.time()

        print(f"Request {request_id}:")
        print(f"  Status Code: {response.status_code}")
        print(f"  Response Time: {end_time - start_time:.3f}s")
        print(f"  Response: {response.text[:200]}...")  # First 200 chars
        print("-" * 50)

        return {
            'request_id': request_id,
            'status_code': response.status_code,
            'response_time': end_time - start_time,
            'response_text': response.text
        }

    except requests.exceptions.RequestException as e:
        print(f"Request {request_id} failed: {str(e)}")
        return {
            'request_id': request_id,
            'error': str(e)
        }


def send_simultaneous_requests():
    """Send two requests simultaneously using ThreadPoolExecutor"""

    print("Sending simultaneous requests...")
    start_time = time.time()

    # Using ThreadPoolExecutor for better control
    with ThreadPoolExecutor(max_workers=2) as executor:
        # Submit both requests at the same time
        future1 = executor.submit(make_request, 1)
        future2 = executor.submit(make_request, 2)

        # Wait for both to complete
        results = [future1.result(), future2.result()]

    total_time = time.time() - start_time
    print(f"Total execution time: {total_time:.3f}s")

    return results


def send_with_threading():
    """Alternative method using threading.Thread"""

    print("Sending simultaneous requests using threading...")

    results = []
    threads = []

    def thread_wrapper(request_id):
        result = make_request(request_id)
        results.append(result)

    # Create and start threads
    for i in range(1, 3):
        thread = threading.Thread(target=thread_wrapper, args=(i,))
        threads.append(thread)
        thread.start()

    # Wait for all threads to complete
    for thread in threads:
        thread.join()

    return results


if __name__ == "__main__":
    print("Choose method:")
    print("1. ThreadPoolExecutor (recommended)")
    print("2. Threading")

    choice = input("Enter choice (1 or 2, default 1): ").strip() or "1"

    if choice == "2":
        results = send_with_threading()
    else:
        results = send_simultaneous_requests()

    print("\nSummary:")
    for result in results:
        if 'error' in result:
            print(f"Request {result['request_id']}: FAILED - {result['error']}")
        else:
            print(f"Request {result['request_id']}: {result['status_code']} ({result['response_time']:.3f}s)")