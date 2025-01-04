import os
import re
import json
import argparse
import requests
from urllib.parse import urljoin, urlparse

# Argument parser setup
parser = argparse.ArgumentParser(description="Recreate unminified source paths on disk from (json) .map file")
parser.add_argument('sourcemap', nargs='?', type=argparse.FileType('r'), default='-', help="Path to (local) sourcemap file")
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
        pattern = r"//# sourceMappingURL=([\w\-.\/]+)"
        match = re.search(pattern, js_content)
        if match:
            sourcemap_path = match.group(1)
            log(f"Found sourceMappingURL in file: {sourcemap_path}")
            sourcemap_url = resolve_sourcemap_url(js_url, sourcemap_path)
        else:
            print("No sourceMappingURL found in the JavaScript file and no X-SourceMap header present.\nIf you have the sourcemap file, try running with that files as the sourcemap argument, without --auto_map")
            exit(1)

    try:
        log(f"Retrieving sourcemap from: {sourcemap_url}")
        response = requests.get(sourcemap_url)
        response.raise_for_status()
        sourcemap = response.json()
    except requests.RequestException as e:
        print(f"Error fetching sourcemap file: {e}")
        exit(1)
    except json.JSONDecodeError as e:
        print(f"Error decoding sourcemap JSON: {e}")
        exit(1)

else:
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
