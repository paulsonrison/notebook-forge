"""Local storyboard drawing, animated note bundles and fail-closed verification.

No network, downloaded images, model credentials or auto-approved editorial audit.
"""
from __future__ import annotations

import hashlib
from html import escape
import io
import json
from pathlib import Path
import re
import shutil
import tempfile

from PIL import Image, ImageDraw, ImageFont, ImageSequence
import reportlab

SIZE = (960, 540)
PAPER, INK = '#FFFEF6', '#193963'


def digest(value):
    data = value if isinstance(value, bytes) else json.dumps(value, sort_keys=True, ensure_ascii=False).encode('utf-8')
    return hashlib.sha256(data).hexdigest()


def local_path(root, relative):
    if not isinstance(relative, str) or '\\' in relative or ':' in relative:
        raise ValueError('Asset path must be local and relative')
    path = Path(relative)
    resolved = (Path(root) / path).resolve()
    if path.is_absolute() or '..' in path.parts or not resolved.is_relative_to(Path(root).resolve()):
        raise ValueError('Asset path escapes the notebook')
    return resolved


def entries(job):
    """Stable section keys identify a block, including in grouped-page notebooks."""
    for pi, page in enumerate(job['pages']):
        for bi, block in enumerate(page['blocks']):
            if 'animation' in block:
                yield f'page-{pi}-block-{bi}', page, block, block['animation']


def required_text(obj, key):
    value = obj.get(key)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'animation.{key} requires text')
    return value


def validate_animations(job):
    seen = {key: set() for key in ('id', 'concept', 'layout', 'pattern')}
    for section, page, block, animation in entries(job):
        if block['type'] != 'paragraph' or not isinstance(animation, dict):
            raise ValueError('Attach animation only to its core explanation paragraph')
        for field in (*seen, 'motion_reason', 'alt', 'caption'):
            value = required_text(animation, field)
            if field == 'id' and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
                raise ValueError('animation.id must be a lowercase filename slug')
            if field in seen:
                canonical = ' '.join(value.casefold().split())
                if canonical in seen[field]:
                    raise ValueError(f'duplicate animation {field}: {value}')
                seen[field].add(canonical)
        board = animation.get('storyboard')
        if not isinstance(board, dict):
            raise ValueError('animation requires a locally authored storyboard')
        required_text(board, 'title')
        frames = board.get('frames')
        if not isinstance(frames, list) or not 2 <= len(frames) <= 30:
            raise ValueError('storyboard requires 2–30 keyframes')
        for index, frame in enumerate(frames):
            required_text(frame, 'label')
            duration = frame.get('duration_ms')
            if type(duration) is not int or duration % 10:
                raise ValueError('duration_ms must be an integer multiple of 10')
            if index < len(frames)-1 and not 500 <= duration <= 1200:
                raise ValueError('Keyframe duration must be 500–1200 ms')
            if index == len(frames)-1 and not max(1500, frames[-2]['duration_ms']+500) <= duration <= 3000:
                raise ValueError('Final duration must pause 1500–3000 ms, longer than the preceding frame')
            if not isinstance(frame.get('objects'), list) or not 1 <= len(frame['objects']) <= 80:
                raise ValueError('Each frame requires 1–80 locally drawn objects')


def font(size):
    if type(size) is not int or not 24 <= size <= 48:
        raise ValueError('Use readable 24–48 px font sizes')
    return ImageFont.truetype(str(Path(reportlab.__file__).parent / 'fonts/Vera.ttf'), size)


def rgb(value):
    if not isinstance(value, str) or not re.fullmatch(r'#[0-9a-fA-F]{6}', value):
        raise ValueError('Use #RRGGBB colours')
    return tuple(bytes.fromhex(value[1:]))


def contrast(a, b):
    def lum(c):
        channels = [v/255 for v in rgb(c)]
        return sum(w*(v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4) for w, v in zip((.2126, .7152, .0722), channels))
    l1, l2 = sorted((lum(a), lum(b)))
    return (l2+.05)/(l1+.05)


def text(draw, xy, value, size=26, fill=INK, background=PAPER):
    if not isinstance(value, str) or not value.strip() or '\n' in value:
        raise ValueError('Use concise single-line text objects')
    f = font(size)
    # Use the same supported character inventory as PDF output.
    from render_notebook import register_fonts, check_glyphs
    register_fonts()
    check_glyphs(value)
    bounds = draw.textbbox(xy, value, font=f)
    if bounds[0] < 12 or bounds[1] < 8 or bounds[2] > SIZE[0]-12 or bounds[3] > SIZE[1]-12:
        raise ValueError(f'Text clips canvas bounds: {value}')
    if contrast(fill, background) < 4.5:
        raise ValueError('Text contrast must be at least 4.5:1 against its declared background')
    draw.text(xy, value, font=f, fill=rgb(fill))


def coordinates(obj, key, count, min_y=140):
    values = obj.get(key)
    if not isinstance(values, list) or len(values) != count or any(type(v) not in (int, float) for v in values):
        raise ValueError(f'{key} requires {count} numeric coordinates')
    for x, y in zip(values[::2], values[1::2]):
        if not 12 <= x <= SIZE[0]-12 or not min_y <= y <= SIZE[1]-12:
            raise ValueError('Object clips canvas bounds or overlaps title/step label')
    return values


def draw_frames(animation, static=False):
    board = animation['storyboard']
    frames = []
    for index, frame in enumerate(board['frames'], 1):
        image = Image.new('RGB', SIZE, PAPER)
        draw = ImageDraw.Draw(image)
        text(draw, [28, 18], board['title'], 32)
        text(draw, [28, 76], frame['label'] if static else f'{index}/{len(board["frames"])}  {frame["label"]}', 26)
        for obj in frame['objects']:
            kind = obj.get('type')
            fill = obj.get('fill', INK)
            rgb(fill)
            if kind == 'text':
                text(draw, coordinates(obj, 'xy', 2), required_text(obj, 'text'), obj.get('size', 26), fill, obj.get('background', PAPER))
            elif kind in ('rect', 'ellipse'):
                box = coordinates(obj, 'box', 4)
                if box[0] >= box[2] or box[1] >= box[3]:
                    raise ValueError('Shape bounds must have positive dimensions')
                getattr(draw, 'rectangle' if kind == 'rect' else 'ellipse')(box, fill=rgb(fill))
            elif kind in ('line', 'arrow'):
                xy = coordinates(obj, 'xy', 4)
                draw.line(xy, fill=rgb(fill), width=4)
                if kind == 'arrow':
                    import math
                    x0, y0, x1, y1 = xy
                    angle = math.atan2(y1-y0, x1-x0)
                    draw.polygon([(x1, y1), (x1-16*math.cos(angle-.5), y1-16*math.sin(angle-.5)), (x1-16*math.cos(angle+.5), y1-16*math.sin(angle+.5))], fill=rgb(fill))
            else:
                raise ValueError(f'Unsupported storyboard primitive: {kind}')
        frames.append(image)
    return frames


def inspect_gif(path):
    try:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError(f'Missing or empty GIF: {path}')
        with Image.open(path) as image:
            if image.format != 'GIF' or image.n_frames < 2 or image.size != SIZE or image.info.get('loop') != 0:
                raise ValueError('Expected looping multi-frame GIF with 960x540 playable dimensions')
            pixels, durations = [], []
            for frame in ImageSequence.Iterator(image):
                pixels.append(digest(frame.convert('RGB').tobytes()))
                durations.append(frame.info.get('duration', 0))
            if len(set(pixels)) < 2:
                raise ValueError('Animation has no visual progression')
            if any(not 500 <= n <= 1200 for n in durations[:-1]) or not max(1500, durations[-2]+500) <= durations[-1] <= 3000:
                raise ValueError('Unreadable decoded GIF timing')
        return {'sha256': digest(path.read_bytes()), 'visual_sha256': digest(pixels), 'frame_count': len(pixels), 'durations_ms': durations, 'dimensions': list(SIZE)}
    except (OSError, EOFError) as error:
        raise ValueError(f'Invalid GIF {path}: {error}') from error


def generator_hash():
    scripts = Path(__file__).parent
    return digest({p.name: digest(p.read_text(encoding='utf-8').encode('utf-8')) for p in sorted(scripts.glob('*.py'))})


def render_html(job, manifest):
    e = lambda value: escape(str(value), quote=True)
    by_section = {item['section']: item for item in manifest['gifs']}
    pictures = {item['section']: item for item in manifest.get('images', [])}
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8">',
             '<meta name="viewport" content="width=device-width, initial-scale=1">',
             f'<title>{e(job["title"])}</title>',
             '<style>body{margin:0;background:#fffef6;color:#193963;font:18px/1.7 system-ui}main{max-width:960px;margin:auto;padding:28px}section{margin:40px 0}h1,h2{line-height:1.3}h2{background:#fff068;padding:12px}p,li,pre,figcaption{background:#fffef6}img{max-width:100%;height:auto}figure{margin:20px 0}pre{overflow:auto;padding:16px;background:#f3f8ff}figcaption{font-size:16px}summary{cursor:pointer}@media(prefers-reduced-motion:reduce){.motion{display:none}}@media(prefers-reduced-motion:no-preference){.still{display:none}}</style>',
             f'<main><h1>{e(job["title"])}</h1>']
    for pi, page in enumerate(job['pages']):
        parts.append(f'<article><h2>{e(page["title"])}</h2>')
        for bi, block in enumerate(page['blocks']):
            key = f'page-{pi}-block-{bi}'
            parts.append(f'<section id="{key}"><h3>{e(block["label"])}</h3>')
            if block['type'] == 'bullets':
                parts.append('<ul>'+''.join(f'<li>{e(item)}</li>' for item in block['items'])+'</ul>')
            elif block['type'] == 'code':
                parts.append(f'<pre>{e(block["text"])}</pre>')
            else:
                parts.append(f'<p>{e(block["text"])}</p>')
            if key in pictures:
                item = pictures[key]
                parts.append(f'<figure data-topic="{e(item["topic"])}" data-section="{key}"><img src="{e(item["path"])}" alt="{e(item["alt"])}"><figcaption>{e(item["caption"])}<br>Alt text: {e(item["alt"])}</figcaption></figure>')
            if key in by_section:
                item = by_section[key]
                parts.append(f'<figure data-section="{key}"><img class="motion" src="{e(item["path"])}" alt="{e(item["alt"])}"><img class="still" src="{e(item["still"])}" alt="{e(item["alt"])}"><figcaption>{e(item["caption"])}<br>Alt text: {e(item["alt"])}</figcaption></figure>')
            parts.append('</section>')
        parts.append('</article>')
    parts.append('</main></html>')
    return '\n'.join(parts)


def build_notes(job, output_dir):
    """Build draft bundle after Pass 1. Final delivery requires a separate review."""
    from render_notebook import validate_job, preflight, render_notebook
    from illustrations import build_images
    validate_job(job)
    preflight(job)
    validate_animations(job)
    output_dir = Path(output_dir)
    output_dir.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix='.forge-', dir=output_dir.parent) as temp:
        root = Path(temp)
        (root / 'assets/gifs').mkdir(parents=True)
        manifest = {'version': 2, 'job_sha256': digest(job), 'generator_sha256': generator_hash(), 'gifs': [], 'images': build_images(job, root)}
        for section, page, block, animation in entries(job):
            relative = f'assets/gifs/{animation["id"]}.gif'
            path = local_path(root, relative)
            frames = draw_frames(animation)
            # Retry encoding once if decoder verification detects a failed write.
            for attempt in range(2):
                frames[0].save(path, save_all=True, append_images=frames[1:], duration=[f['duration_ms'] for f in animation['storyboard']['frames']], loop=0, disposal=2, optimize=False)
                try:
                    info = inspect_gif(path)
                    if info['frame_count'] != len(frames):
                        raise ValueError('Keyframes collapsed; author distinct educational states')
                    break
                except ValueError:
                    if attempt:
                        raise
            still = relative.replace('.gif', '.png')
            frames[-1].save(local_path(root, still))
            # Contact sheet contains every decoded frame, not a source-only preview.
            sheet = Image.new('RGB', (SIZE[0], SIZE[1]*len(frames)), PAPER)
            with Image.open(path) as encoded:
                for index, frame in enumerate(ImageSequence.Iterator(encoded)):
                    sheet.paste(frame.convert('RGB'), (0, index*SIZE[1]))
            contact = relative.replace('.gif', '-frames.png')
            sheet.save(local_path(root, contact))
            geometry = [[{k: v for k, v in obj.items() if k in ('type', 'xy', 'box')} for obj in frame['objects']] for frame in animation['storyboard']['frames']]
            manifest['gifs'].append({'section': section, 'heading': page['title'], 'label': block['label'], 'path': relative, 'still': still, 'still_sha256': digest(local_path(root, still).read_bytes()), 'contact_sheet': contact, 'contact_sheet_sha256': digest(local_path(root, contact).read_bytes()), 'concept': animation['concept'], 'layout': animation['layout'], 'pattern': animation['pattern'], 'alt': animation['alt'], 'caption': animation['caption'], 'storyboard_sha256': digest(animation['storyboard']), 'geometry_sha256': digest(geometry), **info})
        (root / 'job.json').write_text(json.dumps(job, indent=2), encoding='utf-8')
        (root / 'notebook.html').write_text(render_html(job, manifest), encoding='utf-8')
        render_notebook(job, root / 'notebook.pdf', asset_root=root)
        manifest['pdf_sha256'] = digest((root / 'notebook.pdf').read_bytes())
        (root / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
        verify_bundle(job, root, require_review=False)
        output_dir.mkdir(parents=True, exist_ok=True)
        # Resolve every destination before any copy: existing junctions/symlinks
        # may otherwise redirect valid staged paths outside the output folder.
        targets = [(source, local_path(output_dir, source.relative_to(root).as_posix()))
                   for source in root.rglob('*') if source.is_file()]
        old_manifest = output_dir / 'manifest.json'
        stale_assets = []
        if old_manifest.is_file():
            previous = json.loads(old_manifest.read_text(encoding='utf-8'))
            current_paths = {source.relative_to(root).as_posix() for source, _ in targets}
            for item in previous.get('gifs', []) + previous.get('images', []):
                for key in ('path', 'still', 'contact_sheet'):
                    relative = item.get(key)
                    if relative and relative not in current_paths:
                        if not re.fullmatch(r'assets/(?:gifs|images)/[a-z0-9-]+\.(?:gif|png)', relative):
                            raise ValueError('Invalid stale generated asset path')
                        stale_assets.append(local_path(output_dir, relative))
        for source, target in targets:
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        for path in stale_assets:
            path.unlink(missing_ok=True)
    # An old verification report must never attest to a newly built draft.
    (output_dir / 'verification.json').unlink(missing_ok=True)
    (output_dir / 'review.json').unlink(missing_ok=True)
    return {'output': str(output_dir.resolve()), 'gifs': len(manifest['gifs']), 'images': len(manifest['images']), 'pass1': True, 'pass2': False, 'status': 'draft: visual/topic review required'}


def verify_bundle(job, root, require_review=True):
    """Technical checks + hash-bound editorial attestations; no semantic auto-pass."""
    root = Path(root)
    from illustrations import validate_media, verify_images
    validate_media(job)
    validate_animations(job)
    manifest = json.loads((root / 'manifest.json').read_text(encoding='utf-8'))
    if manifest.get('job_sha256') != digest(job) or manifest.get('generator_sha256') != generator_hash():
        raise ValueError('Job or generator changed; manifest/review is stale: rebuild and re-audit')
    expected = list(entries(job))
    records = manifest.get('gifs')
    if not isinstance(records, list) or len(records) != len(expected):
        raise ValueError('Manifest section count does not match notes')
    seen = {key: set() for key in ('path', 'section', 'sha256', 'visual_sha256', 'geometry_sha256')}
    for record, (section, page, block, animation) in zip(records, expected):
        if record['section'] != section or record['heading'] != page['title'] or record['label'] != block['label']:
            raise ValueError('Wrong target section mapping')
        if record['path'] != f'assets/gifs/{animation["id"]}.gif':
            raise ValueError('GIF path does not match exact relative path in notes')
        for field in ('concept', 'layout', 'pattern', 'alt', 'caption'):
            if record[field] != animation[field]:
                raise ValueError(f'Manifest {field} changed')
        actual = inspect_gif(local_path(root, record['path']))
        for key, value in actual.items():
            if record.get(key) != value:
                raise ValueError(f'GIF {key} changed; regenerate and re-audit')
        if record['storyboard_sha256'] != digest(animation['storyboard']):
            raise ValueError('Storyboard changed')
        geometry = [[{k: v for k, v in obj.items() if k in ('type', 'xy', 'box')} for obj in frame['objects']] for frame in animation['storyboard']['frames']]
        if record['geometry_sha256'] != digest(geometry):
            raise ValueError('Geometry changed')
        for key in seen:
            if record[key] in seen[key]:
                raise ValueError(f'duplicate or repeated animation {key}')
            seen[key].add(record[key])
        for key in ('still', 'contact_sheet'):
            expected_path = record['path'].replace('.gif', '.png' if key == 'still' else '-frames.png')
            if record[key] != expected_path or digest(local_path(root, record[key]).read_bytes()) != record[key+'_sha256']:
                raise ValueError(f'{key} changed: regenerate and re-audit')
            with Image.open(local_path(root, record[key])) as image:
                image.load()
        record['review_fingerprint'] = digest({'job': digest(job), 'generator': generator_hash(), 'pdf': manifest.get('pdf_sha256'), 'record': {k: v for k, v in record.items() if k != 'review_fingerprint'}})
    if (root / 'notebook.html').read_text(encoding='utf-8') != render_html(job, manifest):
        raise ValueError('HTML paths, placement or text changed: rebuild')
    if digest((root / 'notebook.pdf').read_bytes()) != manifest.get('pdf_sha256'):
        raise ValueError('PDF changed: rebuild and inspect again')
    if require_review and records:
        review_path = root / 'review.json'
        if not review_path.is_file():
            raise ValueError('Pass 2 requires review.json after inspecting every decoded frame and live playback')
        review = json.loads(review_path.read_text(encoding='utf-8'))
        required_text(review, 'reviewer')
        if len(review.get('gifs', [])) != len(records):
            raise ValueError('Pass 2 review must cover every animation')
        for item, record in zip(review['gifs'], records):
            if item.get('fingerprint') != record['review_fingerprint'] or item.get('section') != record['section'] or item.get('approved') is not True:
                raise ValueError('Pass 2 review is stale, unapproved or mapped to the wrong section')
            for key in ('alignment', 'readability', 'playback'):
                if len(required_text(item, key).strip()) < 20:
                    raise ValueError('Pass 2 requires concrete alignment, readability and playback evidence')
    image_fingerprints = verify_images(job, root, manifest, require_review)
    return {'pass1': True, 'pass2': bool(require_review), 'gifs': len(records), 'images': len(image_fingerprints), 'review_fingerprints': {r['section']: r['review_fingerprint'] for r in records}, 'image_review_fingerprints': image_fingerprints}
