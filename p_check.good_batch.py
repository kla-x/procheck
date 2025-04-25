import requests
import json
from typing import List, Dict
import time
import os
import argparse
import csv
from requests.exceptions import RequestException

def chunk_list(lst: List[str], chunk_size: int) -> List[List[str]]:
    """Split a list into chunks of specified size."""
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]

def prepare_request_data(proxies: List[str]) -> Dict[str, List[str]]:
    """Prepare the request data in the format expected by the API."""
    return {
        f"ip_addr[]": [f"{proxy}-{i}" for i, proxy in enumerate(proxies)]
    }

def check_proxies(proxies: List[str], api_url: str, session: requests.Session, max_retries: int = 3, retry_delay: int = 10) -> List[Dict]:
    """Send a request to check the given proxies and return the results."""
    data = prepare_request_data(proxies)
    for attempt in range(max_retries):
        try:
            response = session.post(api_url, data=data, timeout=30)
            response.raise_for_status()
            return json.loads(response.text)
        except RequestException as e:
            print(f"Error on attempt {attempt + 1}/{max_retries}: {str(e)}")
            if attempt < max_retries - 1:
                print(f"Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                print("Max retries reached. Moving to next batch.")
                return []

def process_proxy_list(proxy_list: List[str], batch_size: int = 1000, api_url: str = "https://api.proxyscrape.com/v2/online_check.php", session: requests.Session = None, resume_from: int = 0) -> List[Dict]:
    """Process the entire list of proxies in batches."""
    all_results = []
    batches = chunk_list(proxy_list, batch_size)
    
    if session is None:
        session = requests.Session()
    
    for i, batch in enumerate(batches[resume_from:], start=resume_from):
        print(f"Processing batch {i+1}/{len(batches)}...")
        results = check_proxies(batch, api_url, session)
        all_results.extend(results)
        
        # Save progress after each batch
        save_progress(i + 1, all_results)
        
        # Add a delay to avoid overwhelming the API
        time.sleep(5)
    
    return all_results

def create_session_with_proxy(proxy: str = None) -> requests.Session:
    """Create a requests Session with the specified proxy."""
    session = requests.Session()
    if proxy:
        session.proxies = {
            'http': proxy,
            'https': proxy
        }
    return session

def load_proxies_from_file(filename: str) -> List[str]:
    """Load proxies from a file, one proxy per line."""
    with open(filename, 'r') as f:
        return [line.strip() for line in f if line.strip()]

def save_results_to_file(results: List[Dict], filename: str, output_format: str, only_working: bool = False):
    """Save the results to a file in the specified format."""
    if only_working:
        results = [r for r in results if r.get('working', False)]

    if output_format == 'json':
        with open(filename, 'w') as f:
            json.dump(results, f, indent=2)
    elif output_format == 'txt':
        with open(filename, 'w') as f:
            for result in results:
                f.write(f"{result['ip']}:{result['port']}\n")
    elif output_format == 'csv':
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=results[0].keys() if results else [])
            writer.writeheader()
            writer.writerows(results)

def save_progress(batch_number: int, results: List[Dict]):
    """Save the current progress to a file."""
    with open('progress.json', 'w') as f:
        json.dump({'batch': batch_number, 'results': results}, f)

def load_progress() -> (int, List[Dict]):
    """Load the progress from a file if it exists."""
    if os.path.exists('progress.json'):
        with open('progress.json', 'r') as f:
            data = json.load(f)
        return data['batch'], data['results']
    return 0, []

def main():
    parser = argparse.ArgumentParser(description="Proxy Checker Script")
    parser.add_argument("--list", required=True, help="Path to the proxy list file")
    parser.add_argument("--output", default="results", help="Output file name (without extension)")
    parser.add_argument("--format", choices=['json', 'txt', 'csv'], default='json', help="Output format")
    parser.add_argument("--only-working", action="store_true", help="Output only working proxies")
    parser.add_argument("--proxy", help="Proxy to use for checking (e.g., http://proxy:port)")
    parser.add_argument("--resume", action="store_true", help="Resume from last saved progress")
    args = parser.parse_args()

    proxy_list = load_proxies_from_file(args.list)
    print(f"Loaded {len(proxy_list)} proxies from {args.list}")

    session = create_session_with_proxy(args.proxy)

    resume_from, previous_results = load_progress() if args.resume else (0, [])
    if args.resume:
        print(f"Resuming from batch {resume_from}")

    results = process_proxy_list(proxy_list, session=session, resume_from=resume_from)
    results = previous_results + results

    output_file = f"{args.output}.{args.format}"
    save_results_to_file(results, output_file, args.format, args.only_working)
    print(f"Results saved to {output_file}")

    # Clean up progress file
    if os.path.exists('progress.json'):
        os.remove('progress.json')

if __name__ == "__main__":
    main()