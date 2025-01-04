# maxify
Maxify is a command-line tool that automates the unpacking and deminification of JavaScript projects from sourcemap files.

When such a need arose for me, searching the obvious terms yielded only many, *many* online "paste javascript here" BeautifyJS-type sites and nothing that would actually extract multiple files and write them to my disk. Maxify recreates the original directory structure of the minified/uglified js app and unpacks all source files to their unminified, human-readable form - ideal for debugging, reverse engineering, or forensic analysis. 

### usage: 
`maxifier.py [-h] [-a AUTO_MAP] [-o OUT_DIR] [-v] [sourcemap]`

Recreate unminified source paths on disk from (json) .map file

### positional arguments:
  `sourcemap`             Path to (local) sourcemap file. (defaults to stdin)

### options:
  `-h, --help`            show this help message and exit
  
  `-a AUTO_MAP, --auto_map AUTO_MAP`
                        URL to the .js file to auto-map
                        
  `-o OUT_DIR, --out_dir OUT_DIR`
                        Directory to save extracted files
                        
  `-v, --verbose`         Enable verbose output

### Examples:
``` bash
cat /tmp/json.map | python ./maxifier.py -v
```
``` bash
maxifier.py path/to/source.js.map -o ./output_dir
```
``` bash
maxifier.py --auto_map https://example.com/scripts/main.js -o ./output -v
```

# Additional info:
if passing a URL to a js file with --auto_map, maxify will check for a X-SourceMap HTTP header in the response to its request for the js URL and if the header is populated, will use the value for the .map file URL. If the HTTP header is not found or is empty, maxify will search the .js for a `//# sourceMapURL=` directive, and use the value for the URL to the .map file. 

If you already have a json .map file, maxify can read it directly.
