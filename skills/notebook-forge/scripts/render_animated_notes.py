"""Build original GIFs, companion HTML and PDF stills from an authored JSON job."""
import argparse
import json
from pathlib import Path
from animations import build_notes


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('job', type=Path)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.job.resolve().is_relative_to(args.output_dir.resolve()):
            raise ValueError('Keep source job outside output directory')
        job = json.loads(args.job.read_text(encoding='utf-8-sig'))
        print(json.dumps(build_notes(job, args.output_dir)))
    except (ValueError, OSError, KeyError, TypeError) as error:
        parser.exit(2, f'Notebook Forge: {error}\n')


if __name__ == '__main__':
    main()
