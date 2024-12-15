
# Super Simple Cache Warmer

This Python script helps to warm up the cache of a website by fetching URLs from a sitemap and checking their cache status based on the specified cache header. It now includes dynamic rate limiting to adjust the request frequency depending on server responses.

## Requirements

Before using the script, ensure that the following are installed on your system:

- Python 3.6 or later
- `pip` (Python package manager)
- Required Python packages (listed below)

### Install Python

If you don't have Python installed yet, you can download it from the official Python website:  
[https://www.python.org/downloads/](https://www.python.org/downloads/)

Make sure to install Python 3.6 or later and add it to your system's PATH during installation.

### Install Required Python Packages

1. Clone or download the repository containing the script.
2. Navigate to the folder where the script is located.
3. Install the required dependencies using `pip`:

   ```bash
   pip install requests tqdm termcolor
   ```

## Usage

### Initial Setup

The script will prompt you for the following information:

- **Sitemap URL**: The URL of the sitemap you want to process.
- **Cache Header Key**: The HTTP header used to check the cache status.
- **Cache HIT Value**: The value indicating a cache hit in the cache header.
- **Cache MISS Value**: The value indicating a cache miss in the cache header.

You can either provide new values or use previously cached ones (if available). This information is saved in a cache file (`sitemap_cache.txt`) for future use.

### Dynamic Rate Limiting

The script includes dynamic rate limiting, which adjusts the delay between requests based on server response times and status codes:

- **If a `429 Too Many Requests` status is returned**, the delay will increase with exponential backoff.
- **If the server responds quickly (with a `200 OK` status)**, the delay will decrease to prevent unnecessary throttling.

This ensures efficient warming of the cache while respecting server limits.

### How to Run the Script

Run the script with Python:

```bash
python cache_warmer.py
```

You will be prompted to provide the sitemap URL and cache header information. The script will process the URLs in the sitemap, checking the cache status and adjusting the rate limit dynamically based on the server's responses.
