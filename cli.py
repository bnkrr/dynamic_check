import yaml
from detector import FingerprintDetector, FingerprintDetectionError
import argparse
import json
import sys

def load_config(config_path: str) -> dict:
    try:
        with open(config_path) as f:
            return yaml.safe_load(f)
    except Exception as e:
        raise FingerprintDetectionError(f"Config error: {str(e)}")

def main():
    parser = argparse.ArgumentParser(description="Web Fingerprint Validation Tool")
    parser.add_argument("-c", "--config", required=True, help="Path to YAML config file")
    parser.add_argument("-o", "--output", help="Output file for results (JSON format)")
    parser.add_argument("--visible", action="store_true", help="Run browser in visible mode")
    
    args = parser.parse_args()
    
    try:
        config = load_config(args.config)
        results = []
        
        with FingerprintDetector(headless=not args.visible) as detector:
            for target in config.get("targets", []):
                result = detector.check_target(
                    url=target["url"],
                    checks=target.get("checks", []),
                    timeout=target.get("timeout", 30)
                )
                results.append(result)
        
        output = json.dumps(results, indent=2)
        
        if args.output:
            with open(args.output, "w") as f:
                f.write(output)
        else:
            print(output)
            
        sys.exit(0 if all(r["success"] for r in results) else 1)
        
    except FingerprintDetectionError as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()