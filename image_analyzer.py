import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlsplit
from PIL import ImageFile
from io import BytesIO
import csv
import sys

def get_images_from_url(url, headers):
    """Fetch images from a webpage, handling redirects and multiple tags."""
    images = []
    error_msg = None
    try:
        # Handle schemeless URLs
        if not url.startswith(('http://', 'https://')):
            url = 'http://' + url
        
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        
        # Use effective URL after redirects for relative paths
        effective_url = response.url
        parsed = urlsplit(effective_url)
        base = f"{parsed.scheme}://{parsed.netloc}"
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Collect image sources from common tags
        for tag in soup.find_all(['img', 'object', 'embed']):
            if tag.name == 'img':
                src = tag.get('src')
            elif tag.name == 'object':
                src = tag.get('data')
            elif tag.name == 'embed':
                src = tag.get('src')
            else:
                continue  # unlikely case
            
            if src and not src.startswith('data:'):
                img_url = urljoin(base, src)
                images.append(img_url)
        
        # Deduplicate images
        unique_images = list(dict.fromkeys(images))
        return unique_images, None  # No error
    
    except requests.exceptions.RequestException as e:
        error_msg = f"Error fetching {url}: {e}"
        print(f"Error: {error_msg}", file=sys.stderr)
        return [], error_msg

def get_image_details(image_url, headers):
    """Retrieve image details with robust error handling."""
    try:
        response = requests.get(image_url, headers=headers, stream=True, timeout=10)
        response.raise_for_status()
        content = response.content
        size = len(content)
        
        # Parse dimensions (may fail for SVG, GIF, etc.)
        parser = ImageFile.Parser()
        parser.feed(content)
        img = parser.close()
        
        return {
            'url': image_url,
            'size': size,
            'width': img.width if img else None,
            'height': img.height if img else None
        }
    
    except Exception as e:
        print(f"Error processing {image_url}: {e}", file=sys.stderr)
        return None

def main():
    if len(sys.argv) < 2:
        print("Usage: python script.py <url_list_file>")
        return
    
    user_agent = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    urls = []
    with open(sys.argv[1], 'r') as f:
        urls = [line.strip() for line in f if line.strip()]
    
    failed_websites = []
    
    # Generate image report
    with open('image_report.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['website', 'image', 'bytes', 'width', 'height'])
        writer.writeheader()
        
        for url in urls:
            print(f"Processing {url}...")
            images, error = get_images_from_url(url, user_agent)
            if error:
                failed_websites.append({'url': url, 'error': error})
            else:
                for img in images:
                    details = get_image_details(img, user_agent)
                    if details and details['size'] >= 1024 * 100:  # >=100KB
                        writer.writerow({
                            'website': url,
                            'image': details['url'],
                            'bytes': details['size'],
                            'width': details['width'],
                            'height': details['height']
                        })
    
    # Generate failed websites report
    with open('failed_websites.csv', 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=['url', 'error'])
        writer.writeheader()
        writer.writerows(failed_websites)
    
    print("Reports generated: image_report.csv and failed_websites.csv")

if __name__ == "__main__":
    main()