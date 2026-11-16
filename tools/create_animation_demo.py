"""Author three original educational storyboards; the renderer draws all pixels."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def text(x, y, value, size=26):
    return {'type': 'text', 'xy': [x, y], 'text': value, 'size': size}


def shape(kind, box, fill):
    return {'type': kind, 'box': box, 'fill': fill}


def arrow(x0, y0, x1, y1):
    return {'type': 'arrow', 'xy': [x0, y0, x1, y1]}


def animation(key, concept, layout, pattern, reason, alt, caption, frames):
    return dict(id=key, concept=concept, layout=layout, pattern=pattern,
                motion_reason=reason, alt=alt, caption=caption,
                storyboard={'title': concept, 'frames': frames})


def demo_job():
    tcp = []
    messages = [(220, 710, 250, 'SYN: client sequence 100'),
                (710, 220, 340, 'SYN + ACK: acknowledges 101'),
                (220, 710, 430, 'ACK: acknowledges server SYN')]
    for step, label in enumerate(('Step 1: Client initiates', 'Step 2: Server responds', 'Step 3: Client confirms')):
        objects = [text(120, 155, 'CLIENT'), text(700, 155, 'SERVER'),
                   {'type': 'line', 'xy': [190, 205, 190, 490]},
                   {'type': 'line', 'xy': [770, 205, 770, 490]}]
        for x0, x1, y, message in messages[:step+1]:
            objects += [arrow(x0, y, x1, y), text(270, y-42, message, 24)]
        tcp.append({'label': label, 'duration_ms': 1000 if step < 2 else 2200, 'objects': objects})
    binary = []
    values = [2, 5, 8, 12, 16, 23, 38]
    for step, (label, active, selected) in enumerate([
        ('Step 1: Middle is 12; target is larger', range(7), 3),
        ('Step 2: Keep only the right half', range(4, 7), None),
        ('Step 3: Middle is 23; target found', range(4, 7), 5)]):
        objects = [text(40, 165, 'Sorted values; search for 23', 28)]
        for index, value in enumerate(values):
            x = 40+index*125
            fill = '#FFF068' if index == selected else '#C9F5DE' if index in active else '#E5E7EB'
            objects += [shape('rect', [x, 260, x+100, 345], fill), text(x+30, 282, str(value), 30), text(x+30, 365, str(index), 24)]
        objects += [text(40, 450, 'Discarded values stay grey; indices begin at 0.', 24)]
        binary.append({'label': label, 'duration_ms': 1000 if step < 2 else 2200, 'objects': objects})
    water = []
    positions = [(190, 400), (470, 210), (770, 400)]
    for step, label in enumerate(('Step 1: Liquid evaporates as vapour', 'Step 2: Vapour cools and condenses', 'Step 3: Droplets fall as precipitation')):
        objects = [text(35, 465, 'Surface water', 26), text(350, 150, 'Cloud droplets', 26), text(670, 465, 'Rain / collection', 26),
                   arrow(235, 375, 420, 245), arrow(530, 245, 730, 375), arrow(690, 425, 280, 425)]
        x, y = positions[step]
        objects += [shape('ellipse', [x-25, y-25, x+25, y+25], '#145F9B')]
        water.append({'label': label, 'duration_ms': 1100 if step < 2 else 2400, 'objects': objects})
    specs = [
        ('tcp', 'TCP three-way handshake',
         'A client sends SYN. The server replies with SYN and ACK, acknowledging the client sequence plus one. The client acknowledges the server SYN. This exchange establishes a TCP connection; it does not encrypt it.',
         animation('tcp-handshake', 'TCP three-way handshake', 'two vertical endpoint lifelines', 'three cumulative alternating message arrows', 'Order and direction show who confirms each SYN.', 'Three messages appear between client and server: SYN, SYN plus ACK, then ACK.', 'Each endpoint sends a SYN and receives an acknowledgement before the connection is established.', tcp)),
        ('search', 'Binary search',
         'Binary search requires sorted data. For target 23 in [2, 5, 8, 12, 16, 23, 38], the first midpoint is 12. Discard it and all smaller values. The next midpoint is 23 at index 5, so the search succeeds.',
         animation('binary-search', 'Binary search for 23', 'horizontal indexed array cells', 'interval elimination followed by midpoint match', 'Successive states make the shrinking search interval visible.', 'Seven sorted values are shown; the left four turn grey, then 23 is highlighted at index 5.', 'Only the right half remains after comparing 12; the next comparison finds 23.', binary)),
        ('water', 'The water cycle',
         'In this simplified cycle, liquid surface water evaporates into water vapour. Vapour cools and condenses into liquid droplets that form clouds. Water can return as precipitation and collect at the surface. Many real pathways, such as transpiration and groundwater flow, are omitted here.',
         animation('water-cycle', 'A simplified water cycle', 'triangular environmental reservoirs', 'water parcel traces evaporation condensation and rain', 'Moving through the three stages connects the changes of state.', 'A blue marker moves from surface water to cloud droplets to rain and collection along a triangular cycle.', 'Evaporation produces vapour; condensation makes liquid droplets; precipitation returns water to the surface.', water))]
    return {'title': 'Motion that teaches: three topics', 'theme': {'name': 'notebook', 'confirmed': True},
            'layout': {'mode': 'subtopic-pages', 'confirmed': True},
            'sources': [
                {'kind': 'topic', 'value': 'Original demonstrations; source concepts verified 2026-11-16'},
                {'kind': 'url', 'title': 'IETF RFC 9293: TCP connection establishment', 'value': 'https://www.rfc-editor.org/rfc/rfc9293.html#section-3.5'},
                {'kind': 'url', 'title': 'Python documentation: array bisection', 'value': 'https://docs.python.org/3/library/bisect.html'},
                {'kind': 'url', 'title': 'USGS Water Science School: water cycle', 'value': 'https://www.usgs.gov/water-science-school/water-cycle'}],
            'topics': [{'id': key, 'title': title} for key, title, _, _ in specs],
            'pages': [{'title': title, 'covers': [key], 'blocks': [
                {'type': 'paragraph', 'label': 'Understand', 'text': explanation, 'animation': anim},
                {'type': 'practice', 'label': 'Recall', 'text': prompt}]} for (key, title, explanation, anim), prompt in zip(specs, [
                    'Which message acknowledges the server SYN? The final client ACK.',
                    'Why must the values be sorted? A midpoint comparison must identify which half can contain the target.',
                    'Does evaporation produce cloud droplets directly? No. Condensation of vapour forms liquid droplets.'])]}


if __name__ == '__main__':
    path = ROOT / 'examples/animated-notebook.json'
    path.write_text(json.dumps(demo_job(), indent=2), encoding='utf-8')
    print(path)
