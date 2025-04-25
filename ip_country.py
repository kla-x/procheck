#!/usr/bin/env python3
import argparse
import json
import re
import sys
import time
from typing import List, Dict, Any, Tuple
import requests


def parse_ip(ip_string: str) -> Tuple[str, str]:
    """
    Parse IP address or proxy string, returning both clean IP and original format.
    Returns: (clean_ip, original_ip)
    """
    # Remove any whitespace
    original_ip = ip_string.strip()
    
    # Extract IP without port for API query
    clean_ip = re.sub(r':\d+$', '', original_ip)
    
    return clean_ip, original_ip


def chunk_list(items: List[Any], chunk_size: int) -> List[List[Any]]:
    """Split list into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def get_country_codes(ip_data: List[Tuple[str, str]], batch_size: int = 100) -> List[Dict[str, str]]:
    """
    Query the IP-API batch endpoint to get country codes for IPs.
    Handles batching requests to respect the 100 entry limit.
    Preserves original IP format in the results.
    """
    base_url = "http://ip-api.com/batch?fields=countryCode,query"
    results = []
    
    # Extract clean IPs for API requests
    clean_ips = [item[0] for item in ip_data]
    
    # Create a mapping of clean IPs to original IPs
    ip_mapping = {item[0]: item[1] for item in ip_data}
    
    # Split IPs into batches
    batches = chunk_list(clean_ips, batch_size)
    
    for i, batch in enumerate(batches):
        try:
            print(f"Processing batch {i+1}/{len(batches)} ({len(batch)} IPs)...")
            response = requests.post(base_url, json=batch)
            
            if response.status_code == 200:
                batch_results = response.json()
                
                # Replace clean IPs with original format in results
                for item in batch_results:
                    clean_ip = item['query']
                    original_ip = ip_mapping.get(clean_ip, clean_ip)  # Fallback to clean IP if not found
                    item['original'] = original_ip
                
                results.extend(batch_results)
            else:
                print(f"Error in batch {i+1}: HTTP {response.status_code}", file=sys.stderr)
                print(response.text, file=sys.stderr)
            
            # Add a short delay between batches to be nice to the API
            if i < len(batches) - 1:
                time.sleep(0.5)
                
        except Exception as e:
            print(f"Error processing batch {i+1}: {str(e)}", file=sys.stderr)
    
    return results


def main():
    # Set up command line argument parsing
    parser = argparse.ArgumentParser(
        description="Look up country codes for a list of IP addresses using ip-api.com"
    )
    parser.add_argument("-in", "--input", required=True, help="Input file with IPs (one per line)")
    parser.add_argument("-o", "--output", required=True, help="Output file for results")
    parser.add_argument("-b", "--batch-size", type=int, default=100, 
                        help="Number of IPs per batch request (max 100)")
    parser.add_argument("-f", "--format", choices=["csv", "json", "txt"], default="txt",
                        help="Output format (default: txt)")
    
    args = parser.parse_args()
    
    # Read IPs from input file
    try:
        with open(args.input, 'r') as f:
            raw_ips = [line.strip() for line in f if line.strip()]
    except Exception as e:
        print(f"Error reading input file: {str(e)}", file=sys.stderr)
        sys.exit(1)
    
    # Parse IPs (get both clean and original formats)
    ip_data = [parse_ip(ip) for ip in raw_ips]
    print(f"Loaded {len(ip_data)} IPs from {args.input}")
    
    # Get country codes
    batch_size = min(100, args.batch_size)  # Ensure we don't exceed API limit
    results = get_country_codes(ip_data, batch_size)
    
    # Write results to output file
    try:
        with open(args.output, 'w') as f:
            if args.format == "json":
                json.dump(results, f, indent=2)
            elif args.format == "csv":
                f.write("ip,countryCode\n")
                for item in results:
                    f.write(f"{item['original']},{item.get('countryCode', 'UNKNOWN')}\n")
            else:  # txt format
                for item in results:
                    f.write(f"{item['original']} {item.get('countryCode', 'UNKNOWN')}\n")
        
        print(f"Results written to {args.output} in {args.format} format")
    
    except Exception as e:
        print(f"Error writing output file: {str(e)}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()