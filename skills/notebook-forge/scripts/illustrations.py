"""Original static teaching images, explicit media consent and topic coverage."""
import json
from pathlib import Path
import re

from PIL import Image


def image_entries(job):
    for pi, page in enumerate(job['pages']):
        for bi, block in enumerate(page['blocks']):
            if 'illustration' in block:
                yield f'page-{pi}-block-{bi}', page, block, block['illustration']


def validate_media(job):
    from animations import entries, required_text
    pictures, gifs = list(image_entries(job)), list(entries(job))
    consent = job.get('media')
    if consent is None and not pictures and not gifs:
        return  # Historical text-only jobs remain renderable.
    if not isinstance(consent, dict) or consent.get('confirmed') is not True or any(type(consent.get(k)) is not bool for k in ('images', 'gifs')):
        raise ValueError('Ask for explicit media permission: confirmed, images and gifs choices')
    if pictures and not consent['images'] or gifs and not consent['gifs']:
        raise ValueError('Media generation denied: obtain user permission for each media kind')
    covered, seen = set(), {k: set() for k in ('id', 'concept', 'layout')}
    topics = {topic['id'] for topic in job['topics']}
    for section, page, block, picture in pictures:
        if block['type'] != 'paragraph' or not isinstance(picture, dict):
            raise ValueError('Place each illustration on its exact core explanation paragraph')
        for key in ('id', 'topic', 'concept', 'layout', 'caption', 'alt'):
            value = required_text(picture, key)
            if key == 'id' and not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', value):
                raise ValueError('Image id must be a lowercase filename slug')
            if key in seen:
                canonical = ' '.join(value.casefold().split())
                if canonical in seen[key]:
                    raise ValueError(f'duplicate illustration {key}')
                seen[key].add(canonical)
        if picture['topic'] not in topics or picture['topic'] not in page['covers']:
            raise ValueError('Image topic must be an exact topic covered by its host page')
        covered.add(picture['topic'])
        scene = picture.get('scene')
        if not isinstance(scene, dict):
            raise ValueError('Image requires an original locally drawn scene')
        required_text(scene, 'title')
        required_text(scene, 'label')
        if not isinstance(scene.get('objects'), list) or not 1 <= len(scene['objects']) <= 80:
            raise ValueError('Image scene requires 1-80 original drawing objects')
    if consent['images'] and topics - covered:
        raise ValueError(f'Image coverage missing for topics: {sorted(topics-covered)}')
    # Different formats may teach the same concept within one host section;
    # they must not recycle a concept/layout in another section.
    for field in ('concept', 'layout'):
        locations = {}
        for section, _, _, item in pictures + gifs:
            key = ' '.join(required_text(item, field).casefold().split())
            if key in locations and locations[key] != section:
                raise ValueError(f'duplicate cross-section media {field}')
            locations[key] = section


def inspect_image(path):
    from animations import SIZE, digest
    try:
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError('Missing or empty image file')
        with Image.open(path) as image:
            image.load()
            if image.format != 'PNG' or image.size != SIZE or getattr(image, 'n_frames', 1) != 1:
                raise ValueError('Expected a static 960x540 PNG teaching image')
            pixels = image.convert('RGB')
            if all(lo == hi for lo, hi in pixels.getextrema()):
                raise ValueError('Blank image cannot teach a topic')
            return {'sha256': digest(path.read_bytes()), 'visual_sha256': digest(pixels.tobytes()), 'dimensions': list(image.size)}
    except (OSError, EOFError) as error:
        raise ValueError(f'Invalid image: {error}') from error


def geometry(scene):
    return [{k: v for k, v in obj.items() if k in ('type', 'xy', 'box')} for obj in scene['objects']]


def build_images(job, root):
    from animations import digest, draw_frames, local_path
    records = []
    for section, page, block, picture in image_entries(job):
        relative = f'assets/images/{picture["id"]}.png'
        path = local_path(root, relative)
        path.parent.mkdir(parents=True, exist_ok=True)
        scene = picture['scene']
        canvas = draw_frames({'storyboard': {'title': scene['title'], 'frames': [scene]}}, static=True)[0]
        for attempt in range(2):
            canvas.save(path, format='PNG')
            try:
                info = inspect_image(path)
                break
            except ValueError:
                if attempt:
                    raise
        records.append(dict(section=section, heading=page['title'], label=block['label'],
                            path=relative, **{k: picture[k] for k in ('topic', 'concept', 'layout', 'caption', 'alt')},
                            scene_sha256=digest(scene), geometry_sha256=digest(geometry(scene)), **info))
    return records


def verify_images(job, root, manifest, require_review):
    from animations import digest, generator_hash, local_path, required_text
    expected = list(image_entries(job))
    records = manifest.get('images', [])
    if len(expected) != len(records):
        raise ValueError('Image manifest coverage does not match notes')
    seen = {k: set() for k in ('path', 'section', 'sha256', 'visual_sha256', 'geometry_sha256')}
    fingerprints = {}
    for record, (section, page, block, picture) in zip(records, expected):
        if record['section'] != section or record['heading'] != page['title'] or record['label'] != block['label']:
            raise ValueError('Wrong image target section mapping')
        if record['path'] != f'assets/images/{picture["id"]}.png':
            raise ValueError('Wrong image relative path')
        for key in ('topic', 'concept', 'layout', 'caption', 'alt'):
            if record[key] != picture[key]:
                raise ValueError('Image topic metadata changed')
        for key, value in inspect_image(local_path(root, record['path'])).items():
            if record[key] != value:
                raise ValueError('Image changed; regenerate and re-review')
        if record['scene_sha256'] != digest(picture['scene']) or record['geometry_sha256'] != digest(geometry(picture['scene'])):
            raise ValueError('Image source scene changed')
        for key in seen:
            if record[key] in seen[key]:
                raise ValueError(f'duplicate or repeated image {key}')
            seen[key].add(record[key])
        fingerprints[section] = digest({'job': digest(job), 'generator': generator_hash(), 'pdf': manifest['pdf_sha256'], 'image': record})
    if require_review and records:
        path = Path(root) / 'review.json'
        if not path.is_file():
            raise ValueError('Pass 2 image review is required before delivery')
        review = json.loads(path.read_text(encoding='utf-8'))
        required_text(review, 'reviewer')
        audited = review.get('images', [])
        if len(audited) != len(records):
            raise ValueError('Pass 2 image review must cover every image')
        for item, record in zip(audited, records):
            if item.get('section') != record['section'] or item.get('fingerprint') != fingerprints[record['section']] or item.get('approved') is not True:
                raise ValueError('Image review is stale, unapproved or mapped to the wrong topic')
            for key in ('alignment', 'readability'):
                if len(required_text(item, key).strip()) < 20:
                    raise ValueError('Record concrete image topic alignment and readability evidence')
    return fingerprints
