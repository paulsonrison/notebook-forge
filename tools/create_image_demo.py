"""Author three complete static teaching diagrams, with explicit demo consent."""
import copy
import json
from pathlib import Path
from create_animation_demo import demo_job, text, shape, arrow

ROOT = Path(__file__).resolve().parents[1]


def image_demo():
    job = demo_job()
    job['title'] = 'Visual study notebook: three illustrated topics'
    job['media'] = {'confirmed': True, 'images': True, 'gifs': False}
    for page in job['pages']:
        block = page['blocks'][0]
        animation = block.pop('animation')
        picture = {k: copy.deepcopy(animation[k]) for k in ('id', 'concept', 'layout', 'caption', 'alt')}
        picture['id'] += '-diagram'
        picture['topic'] = page['covers'][0]
        picture['scene'] = {
            'title': animation['storyboard']['title'],
            'label': 'Read the complete sequence in one diagram',
            'objects': copy.deepcopy(animation['storyboard']['frames'][-1]['objects'])}
        block['illustration'] = picture
    binary = job['pages'][1]['blocks'][0]['illustration']
    binary.update(caption='Compare midpoint 12, discard the left four values, then find 23 at index 5.',
                  alt='A sorted array shows 12 as the first comparison and 23 as the match; indices 0 to 3 are discarded.',
                  layout='annotated array with comparison and match pointers')
    binary['scene']['label'] = 'Two comparisons: 12 is too small; 23 matches'
    binary['scene']['objects'] = [text(30, 150, 'Target: 23. Grey cells are discarded after comparing 12.', 24)]
    for i, value in enumerate([2, 5, 8, 12, 16, 23, 38]):
        x = 40+i*125
        binary['scene']['objects'] += [shape('rect', [x, 260, x+100, 345], '#FFF068' if i == 5 else '#E5E7EB' if i <= 3 else '#C9F5DE'), text(x+30, 282, str(value), 30), text(x+30, 365, str(i), 24)]
    binary['scene']['objects'] += [text(250, 190, '1: compare 12', 24), arrow(450, 224, 465, 254),
                                   text(640, 430, '2: find 23 at index 5', 24), arrow(730, 420, 715, 350)]
    water = job['pages'][2]['blocks'][0]['illustration']
    water.update(layout='labelled three-reservoir cycle with state-change annotations',
                 alt='Arrows connect surface water to cloud droplets through evaporation and condensation, then to rain and collection.',
                 caption='Liquid evaporates into vapour, condensation forms cloud droplets, and precipitation returns water to the surface.')
    water['scene']['label'] = 'A simplified cycle: surface, atmosphere, surface'
    water['scene']['objects'] = [
        shape('ellipse', [390, 155, 600, 225], '#C9F5DE'), text(400, 170, 'Cloud droplets', 24),
        shape('rect', [25, 420, 260, 490], '#C9F5DE'), text(40, 435, 'Surface water', 26),
        shape('rect', [680, 420, 930, 490], '#C9F5DE'), text(690, 435, 'Rain / collection', 24),
        arrow(190, 410, 410, 240), arrow(610, 240, 780, 410), arrow(670, 480, 280, 480),
        text(35, 265, 'Evaporation', 24), text(80, 200, 'Vapour condenses', 24),
        text(700, 245, 'Precipitation', 24), text(360, 490, 'Collection', 24)]
    return job


if __name__ == '__main__':
    target = ROOT / 'examples/illustrated-notebook.json'
    target.write_text(json.dumps(image_demo(), indent=2), encoding='utf-8')
    print(target)
