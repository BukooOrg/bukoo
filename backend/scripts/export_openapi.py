#!/usr/bin/env python3
"""Export the FastAPI OpenAPI spec to a JSON file without starting the server."""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from app.main import app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        default="../sdk/openapi.json",
        help="Output path for the spec file (default: ../sdk/openapi.json)",
    )
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    spec = app.openapi()
    output_path.write_text(json.dumps(spec, indent=2))
    print(f"Spec exported to {output_path} ({len(spec['paths'])} paths)")


if __name__ == "__main__":
    main()
