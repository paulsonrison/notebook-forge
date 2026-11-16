"""Verify technical integrity and explicit visual/topic audit evidence."""
import argparse
import json
from pathlib import Path
from animations import verify_bundle


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('bundle', type=Path)
    parser.add_argument('--technical-only', action='store_true', help='Draft check; does not pass final delivery gate')
    args = parser.parse_args()
    try:
        job = json.loads((args.bundle / 'job.json').read_text(encoding='utf-8'))
        report = verify_bundle(job, args.bundle, require_review=not args.technical_only)
        if not args.technical_only:
            (args.bundle / 'verification.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
        print(json.dumps(report))
    except (ValueError, OSError, KeyError, TypeError) as error:
        (args.bundle / 'verification.json').unlink(missing_ok=True)
        parser.exit(2, f'GIF verification: {error}\n')


if __name__ == '__main__':
    main()
