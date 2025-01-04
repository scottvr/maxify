import os
import re
import json
import argparse
import requests
import base64
from urllib.parse import urljoin, urlparse

# Argument parser setup
parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter, 
                                 description="Recreate unminified source paths on disk from (json) .map file", 
                                 epilog='''Examples:
%(prog)s path/to/source.js.map -o ./output_dir

or

%(prog)s --auto_map https://example.com/scripts/main.js -o ./output -v''')
parser.add_argument('sourcemap', nargs='?', type=argparse.FileType('r'), default='-', help="Path to (local) sourcemap file. (defaults to stdin)")
parser.add_argument('-a', '--auto_map', action='store', default=None, help="URL to the .js file to auto-map")
parser.add_argument('-o', '--out_dir', action='store', default='./output', help="Directory to save extracted files")
parser.add_argument('-v', '--verbose', action='store_true', help="Enable verbose output")
args = parser.parse_args()

verbose = args.verbose

def log(message):
    if verbose:
        print(message)

def resolve_sourcemap_url(js_url, sourcemap_path):
    if urlparse(sourcemap_path).scheme:  # Absolute URL
        return sourcemap_path
    else:  # Relative URL
        return urljoin(js_url, sourcemap_path)

def extract_sourcemap(js_content):
    # Regex for sourceMappingURL
    pattern = r"//# sourceMappingURL=(.+)"
    match = re.search(pattern, js_content)
    
    if not match:
        return None, "No sourceMappingURL found in the JavaScript file and no X-SourceMap header present.\nIf you have the sourcemap file, try running with that files as the sourcemap argument, without --auto_map"
    
    sourcemap_url = match.group(1)

    # Check for data URL
    if sourcemap_url.startswith("data:application/json;base64,"):
        # Decode Base64
        base64_data = sourcemap_url[len("data:application/json;base64,"):]
        try:
            decoded = base64.b64decode(base64_data).decode('utf-8')
            return json.loads(decoded), None
        except Exception as e:
            return None, f"Failed to decode Base64 data: {e}"

    # Fallback for external URLs
    try:
        response = requests.get(sourcemap_url)
        response.raise_for_status()
        return response.json(), None
    except Exception as e:
        return None, f"Failed to fetch sourcemap from URL: {e}"

if args.auto_map:
    js_url = args.auto_map
    log(f"Retrieving JavaScript file from: {js_url}")

    try:
        response = requests.get(js_url)
        response.raise_for_status()
        js_content = response.text
    except requests.RequestException as e:
        print(f"Error fetching JavaScript file: {e}")
        exit(1)

    # perhaps unlikely, but if it exists, give it priority (also, no need to request the js twice)
    sourcemap_path = response.headers.get('X-SourceMap')
    if sourcemap_path:
        log(f"Found X-SourceMap header: {sourcemap_path}")
        sourcemap_url = resolve_sourcemap_url(js_url, sourcemap_path)
    else:
        # If no header, search for sourceMappingURL in the file content
        log("No X-SourceMap header found. Searching for //# sourceMappingURL in the file...")
        sourcemap, error = extract_sourcemap(js_content)
        if error:
            log(f"Error: {error}")
        else:
            log("Extracted Sourcemap:")
            log(json.dumps(sourcemap, indent=4))

  if not sourcemap:
    # Fallback to local file
    sourcemap = json.load(args.sourcemap)

out_dir = args.out_dir
log(f"Extracting source files into: {out_dir}")
os.makedirs(out_dir, exist_ok=True)

# Extract sources from sourcemap
for filename, content in zip(sourcemap['sources'], sourcemap['sourcesContent']):
    filename = os.path.normpath(filename)
    while filename.startswith("../"):
        filename = filename[3:]
    file_path = os.path.join(out_dir, *filename.split('/'))
    
    log(f"Generating {file_path}..")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content or '')
    log("..done.")
