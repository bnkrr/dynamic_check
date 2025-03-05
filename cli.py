import yaml
from detector import FingerprintDetector, FingerprintDetectionError
import argparse
import json
import sys

def load_template(template_path: str) -> dict:
    try:
        with open(template_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise FingerprintDetectionError(f"Config error: {str(e)}")

def is_url(url: str) -> bool:
    return url.startswith("http://") or url.startswith("https://")

def load_urls(url_path: str) -> list:
    try:
        if is_url(url_path):
            return [url_path]
        with open(url_path) as f:
            return f.read().splitlines()
    except Exception as e:
        raise FingerprintDetectionError(f"URL list error: {str(e)}")

def url_append_path(url, path):
    if url.endswith("/") and path.startswith("/"):
        return url + path[1:]
    elif not url.endswith("/") and not path.startswith("/"):
        return url + "/" + path
    else:
        return url + path

def main():
    parser = argparse.ArgumentParser(description="Web Fingerprint Validation Tool")
    parser.add_argument("-t", "--template", required=True, help="Path to YAML template file")
    parser.add_argument("-u", "--url", required=True, help="Path to url list file or url")
    parser.add_argument("-o", "--output", help="Output file for results (JSON format)")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode")
    
    args = parser.parse_args()
    
    try:
        template = load_template(args.template)
        urls = load_urls(args.url)
        
        if args.output:
            fout = open(args.output, "w")
        results = []
        
        with FingerprintDetector(headless=not args.visible) as detector:
            for url in urls:
                result = detector.check_target(
                    url=url_append_path(url, template.get("path", "/")),
                    checks=template.get("checks", []),
                    timeout=template.get("timeout", 30)
                )
                results.append(result)
                if args.output:
                    fout.write(json.dumps(result)+'\n')
                else:
                    print(json.dumps(result, indent=2))                

        if args.output:
            fout.close()
            
        sys.exit(0 if all(r["success"] for r in results) else 1)
        
    except FingerprintDetectionError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()