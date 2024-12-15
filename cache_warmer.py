# Super Simple Cache Warmer
# Author: Yoeri (https://github.com/YoeriW)
# GitHub: https://github.com/YoeriW/
# Email: contact@yoeriwas.nl
# License: MIT License (Open Source)

import os
import requests
import xml.etree.ElementTree as ET
from tqdm import tqdm
import time
from termcolor import colored

CACHE_FILE = "sitemap_cache.txt"
BASE_RATE_LIMIT_DELAY = 0.2

def get_cache_info():
    """Handles getting the cache header information from the user, or uses the cached values if available."""
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE, "r") as file:
            stored_url = file.readline().strip()
            cache_header = file.readline().strip()
            hit_value = file.readline().strip()
            miss_value = file.readline().strip()

        # Ask user if they want to use the stored URL
        user_input = input(f"Do you want to use the stored sitemap URL ({colored(stored_url, 'yellow')})? (yes/no): ").strip().lower()
        if user_input not in ['yes', 'y']:  # Handle "yes" or "y"
            sitemap_url = input("Please provide the new sitemap URL: ").strip()
        else:
            sitemap_url = stored_url

        # Ask user if they want to use the stored cache header info
        user_input = input(f"Do you want to use the stored cache header ({colored(cache_header, 'yellow')}) with HIT value ({colored(hit_value, 'green')}) and MISS value ({colored(miss_value, 'red')})? (yes/no): ").strip().lower()
        if user_input not in ['yes', 'y']:  # Handle "yes" or "y"
            cache_header = input("Please provide the cache header key: ").strip()
            hit_value = input("Please provide the value for a cache HIT: ").strip()
            miss_value = input("Please provide the value for a cache MISS: ").strip()

        # Now we write only the updated values to the cache file
        with open(CACHE_FILE, "w") as file:
            file.write(f"{sitemap_url}\n{cache_header}\n{hit_value}\n{miss_value}\n")

        return sitemap_url, cache_header, hit_value, miss_value

    # If the cache file doesn't exist, ask for the details and create the file
    sitemap_url = input("Please provide the sitemap URL: ").strip()
    cache_header = input("Please provide the cache header key: ").strip()
    hit_value = input("Please provide the value for a cache HIT: ").strip()
    miss_value = input("Please provide the value for a cache MISS: ").strip()

    # Ensure the file is created and write data
    with open(CACHE_FILE, "w") as file:
        file.write(f"{sitemap_url}\n{cache_header}\n{hit_value}\n{miss_value}\n")

    return sitemap_url, cache_header, hit_value, miss_value

def fetch_sitemap_urls(sitemap_url):
    """Fetches and parses a sitemap URL, returning a list of URLs (both pages and nested sitemaps)."""
    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        tqdm.write(colored(f"[Error]", 'red') + " fetching " + colored(f"{sitemap_url}: {e}", 'yellow'))
        return []

    urls = []
    try:
        root = ET.fromstring(response.content)
        namespace = {'ns': 'http://www.sitemaps.org/schemas/sitemap/0.9'}

        # Parse <sitemap> tags for nested sitemaps
        for sitemap in root.findall('ns:sitemap', namespace):
            loc = sitemap.find('ns:loc', namespace)
            if loc is not None:
                urls.append(loc.text)

        # Parse <url> tags for individual page URLs
        for url in root.findall('ns:url', namespace):
            loc = url.find('ns:loc', namespace)
            if loc is not None:
                urls.append(loc.text)

    except ET.ParseError as e:
        tqdm.write(colored(f"[Error]", 'red') + " parsing " + colored(f"{sitemap_url}: {e}", 'yellow'))

    return urls

def check_cache_status(response, cache_header, hit_value, miss_value):
    """Check if the response was a cache hit or miss based on the specified cache header and values."""
    cache_status = response.headers.get(cache_header, None)
    if cache_status:
        if cache_status.lower() == hit_value.lower():
            return colored("HIT", 'green')
        elif cache_status.lower() == miss_value.lower():
            return colored("MISS", 'red')
    return "NO CACHE INFO"

def adjust_rate_limit(response):
    """Dynamically adjust the rate limit delay based on response status or time taken."""
    global BASE_RATE_LIMIT_DELAY

    # Increase delay on 429 Too Many Requests status
    if response.status_code == 429:
        BASE_RATE_LIMIT_DELAY = min(BASE_RATE_LIMIT_DELAY * 2, 10)  # Exponential backoff, capped at 10s
        tqdm.write(colored(f"[Rate Limiting] Adjusting delay due to 429 status code.", 'yellow'))

    # Decrease delay if the server responds quickly
    elif response.status_code == 200:
        # Reduce delay after successful request to prevent bottleneck
        BASE_RATE_LIMIT_DELAY = max(BASE_RATE_LIMIT_DELAY / 1.5, BASE_RATE_LIMIT_DELAY)  # Minimum delay of 0.2s
        # tqdm.write(colored(f"[Rate Limiting] Adjusting delay due to fast response.", 'yellow'))

def warm_cache(sitemap_url, visited=None, cache_header=None, hit_value=None, miss_value=None):
    """Recursively visits all URLs in the sitemap to warm the cache."""

    if visited is None:
        visited = set()

    tqdm.write("[Processing sitemap] " + colored(f"{sitemap_url}", 'yellow'))
    urls = fetch_sitemap_urls(sitemap_url)

    # Progress bar setup
    total_urls = len(urls)
    with tqdm(total=total_urls, desc="[Warming cache] ", unit="url") as pbar:
        for url in urls:
            if url in visited:
                pbar.update(1)
                continue

            visited.add(url)
            if url.endswith('.xml'):  # If the URL is another sitemap
                warm_cache(url, visited, cache_header, hit_value, miss_value)
            else:  # If the URL is a page
                try:
                    start_time = time.time()
                    response = requests.get(url, timeout=10)
                    elapsed_time = time.time() - start_time
                    adjust_rate_limit(response)
                    cache_status = check_cache_status(response, cache_header, hit_value, miss_value)
                    if response.status_code == 200:
                        tqdm.write("[CACHE] " + cache_status + " [Status] " + colored(f"{response.status_code}", 'green') + " [Time] " + colored(f"{elapsed_time:.2f}s", 'yellow') + " [URL] " + colored(f"{url}", 'yellow'))
                    else:
                        tqdm.write(colored(f"[Error]", 'red') + " while visiting " + colored(f"{url}", 'yellow') + " [Status] " + colored(f"{response.status_code}", 'red'))
                except requests.RequestException as e:
                    tqdm.write(colored(f"[Error]", 'red') + " while visiting " + colored(f"{url} {e}", 'yellow'))
            
            time.sleep(BASE_RATE_LIMIT_DELAY)
            pbar.update(1)

if __name__ == "__main__":
    tqdm.write(colored(f"[Super Simple Cache Warmer]", 'red') + " Starting...")

    sitemap_url, cache_header, hit_value, miss_value = get_cache_info()
    warm_cache(sitemap_url, cache_header=cache_header, hit_value=hit_value, miss_value=miss_value)

    tqdm.write(colored(f"[Super Simple Cache Warmer]", 'green') + " Complete!")
