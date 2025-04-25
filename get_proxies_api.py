#!/usr/bin/env python3
import requests
import json
import argparse
import sys


def fetch_proxy_data(country="PL", limit=500, page=1, sort_by="lastChecked", sort_type="desc"):
    """Fetch proxy data from the direct API endpoint."""
    url = f"https://proxyfreeonly.com/api/free-proxy-list?limit={limit}&page={page}&country={country}&sortBy={sort_by}&sortType={sort_type}"
    
    # Set up headers
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.6778.86 Safari/537.36",
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://proxyfreeonly.com/free-proxy-list"
    }
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}", file=sys.stderr)
        sys.exit(1)


def format_proxy_info(proxy_list, include_all=False, include_type=False, include_lat=False, 
                      include_country=False, include_ccode=False, include_uptime=False,
                      include_isp=False, include_response_time=False, include_updated=False):
    """Format the proxy information based on included fields."""
    result = []
    
    for proxy in proxy_list:
        # Default output is always IP:PORT
        output = f"{proxy['ip']}:{proxy['port']}"
        
        additional_info = []
        
        if include_all or include_type:
            protocols = "/".join(proxy.get("protocols", ["unknown"]))
            additional_info.append(f"{protocols}")
            
        if include_all or include_lat:
            # Get latency as a number
            latency = proxy.get("latency", 0)
            additional_info.append(f"{latency}")
            
        if include_all or include_country:
            country = proxy.get("country", "Unknown")
            additional_info.append(f"{country}")
            
        if include_all or include_ccode:
            country_code = proxy.get("country", "Unknown")
            additional_info.append(f"{country_code}")
            
        if include_all or include_uptime:
            uptime = proxy.get("upTime", 0)
            additional_info.append(f"{uptime}")
            
        if include_all or include_isp:
            isp = proxy.get("isp", "Unknown")
            additional_info.append(f"{isp}")
            
        if include_all or include_response_time:
            response_time = proxy.get("responseTime", 0)
            additional_info.append(f"{response_time}")
            
        if include_all or include_updated:
            updated = proxy.get("updated_at", "Unknown")
            additional_info.append(f"{updated}")
        
        if additional_info:
            output += " " + " ".join(map(str, additional_info))
        
        result.append(output)
    
    return result


def main():
    parser = argparse.ArgumentParser(description="Fetch and parse proxy list data.")
    parser.add_argument("-all", action="store_true", help="Include all information fields")
    parser.add_argument("-type", action="store_true", help="Include protocol types")
    parser.add_argument("-lat", action="store_true", help="Include latency information")
    parser.add_argument("-country", action="store_true", help="Include country name")
    parser.add_argument("-ccode", action="store_true", help="Include country code")
    parser.add_argument("-uptime", action="store_true", help="Include uptime percentage")
    parser.add_argument("-isp", action="store_true", help="Include ISP information")
    parser.add_argument("-response", action="store_true", help="Include response time")
    parser.add_argument("-updated", action="store_true", help="Include when proxy was last updated")
    parser.add_argument("-c", "--country", dest="country_filter", default="PL", 
                        help="Filter by country code (default: PL for Poland)")
    parser.add_argument("-l", "--limit", dest="limit", type=int, default=500, 
                        help="Limit number of results (default: 500)")
    parser.add_argument("-p", "--page", dest="page", type=int, default=1, 
                        help="Page number (default: 1)")
    parser.add_argument("-s", "--sort", dest="sort_by", default="lastChecked", 
                        help="Sort by field (default: lastChecked)")
    parser.add_argument("-d", "--direction", dest="sort_type", default="desc", 
                        choices=["asc", "desc"], help="Sort direction (default: desc)")
    
    args = parser.parse_args()
    
    # Fetch data
    proxy_list = fetch_proxy_data(
        country=args.country_filter,
        limit=args.limit,
        page=args.page,
        sort_by=args.sort_by,
        sort_type=args.sort_type
    )
    
    # Format and print proxy information
    proxy_info = format_proxy_info(
        proxy_list,
        include_all=args.all,
        include_type=args.type,
        include_lat=args.lat,
        include_country=args.country,
        include_ccode=args.ccode,
        include_uptime=args.uptime,
        include_isp=args.isp,
        include_response_time=args.response,
        include_updated=args.updated
    )
    
    for proxy in proxy_info:
        print(proxy)


if __name__ == "__main__":
    main()