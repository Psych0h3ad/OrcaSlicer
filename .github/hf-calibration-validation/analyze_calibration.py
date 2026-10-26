"""Measure commanded extrusion volume/time from long outer-wall G1 moves.

Does not estimate acceleration, pressure dynamics, or actual printer throughput.
Only the slicer's straight calibration segments are used, excluding purge/brim.
"""
import argparse
import csv
import hashlib
import json
import math
from pathlib import Path
import re
import statistics

parser = argparse.ArgumentParser()
parser.add_argument('gcode', type=Path)
parser.add_argument('--out', type=Path)
parser.add_argument('--start', type=float)
parser.add_argument('--step', type=float)
args = parser.parse_args()
if (args.start is None) != (args.step is None):
    parser.error('--start and --step must be supplied together')
data = args.gcode.read_text(encoding='utf-8-sig')
diam_match = re.search(r'^; filament_diameter:\s*([\d.]+)', data, re.M)
diameter = float(diam_match.group(1)) if diam_match else 1.75
area = math.pi * (diameter / 2) ** 2
position = dict(X=0., Y=0., Z=0., E=0.)
relative_e, relative_xyz = False, False
feed, feature, layer, layer_z = 0., '', 0, 0.
layers = {}
arcs = 0
for number, line in enumerate(data.splitlines(), 1):
    if line.startswith(';TYPE:'):
        feature = line[6:].strip()
    elif line == ';LAYER_CHANGE':
        layer += 1
    elif line.startswith(';Z:'):
        layer_z = float(line[3:])
    code = line.split(';', 1)[0].strip()
    if not code:
        continue
    command = code.split()[0]
    fields = {k: float(v) for k, v in re.findall(r'([XYZEF])\s*(-?(?:\d+(?:\.\d*)?|\.\d+))', code)}
    if command == 'M83':
        relative_e = True
    elif command == 'M82':
        relative_e = False
    elif command == 'G90':
        relative_xyz = False
    elif command == 'G91':
        relative_xyz = True
    elif command == 'G92':
        for key in position.keys() & fields.keys():
            position[key] = fields[key]
    elif command in ('G0', 'G1', 'G2', 'G3'):
        next_position = position.copy()
        for key in ('X', 'Y', 'Z'):
            if key in fields:
                next_position[key] = fields[key] + (position[key] if relative_xyz else 0.)
        extrusion = 0.
        if 'E' in fields:
            extrusion = fields['E'] if relative_e else fields['E'] - position['E']
            next_position['E'] = position['E'] + extrusion
        feed = fields.get('F', feed)
        length_xy = math.hypot(next_position['X'] - position['X'], next_position['Y'] - position['Y'])
        length = math.sqrt(length_xy**2 + (next_position['Z'] - position['Z'])**2)
        if command in ('G2', 'G3') and extrusion > 0 and feature == 'Outer wall':
            arcs += 1
        elif feature == 'Outer wall' and extrusion > 0 and length_xy >= 25 and feed > 0:
            time = length / (feed / 60)
            layers.setdefault(layer, []).append({'line': number, 'z': layer_z,
                                                'speed': feed / 60,
                                                'flow': extrusion * area / time,
                                                'length': length})
        position = next_position
if arcs:
    raise SystemExit(f'Unsupported {arcs} extruding arcs in measured feature')
rows = []
for layer, moves in layers.items():
    rows.append({'layer': layer, 'z_mm': moves[0]['z'], 'segments': len(moves),
                 'median_speed_mm_s': statistics.median(m['speed'] for m in moves),
                 'median_flow_mm3_s': statistics.median(m['flow'] for m in moves),
                 'max_flow_mm3_s': max(m['flow'] for m in moves),
                 'first_line': moves[0]['line']})
    if args.start is not None:
        expected = args.start + moves[0]['z'] * args.step
        rows[-1]['requested_flow_mm3_s'] = expected
        rows[-1]['median_error_mm3_s'] = rows[-1]['median_flow_mm3_s'] - expected
if not rows:
    raise SystemExit('No outer-wall calibration segments found')
config = {}
for key in ('filament_flow_ratio', 'filament_max_volumetric_speed', 'slow_down_layer_time',
            'filament_grouping_mode', 'filament_volume_type', 'nozzle_volume_type'):
    match = re.search(r'^; ' + key + r' = (.*)$', data, re.M)
    if match:
        config[key] = match.group(1)
samples = [min(rows, key=lambda r: abs(r['z_mm'] - z)) for z in (10., 30., 50., 70.)]
result = {'file': args.gcode.name, 'sha256': hashlib.sha256(args.gcode.read_bytes()).hexdigest(),
          'method': 'E * pi * (diameter/2)^2 / (3D straight-line distance / (F/60)); median of outer-wall G1 segments >=25 mm per layer',
          'filament_diameter_mm': diameter, 'measured_layers': len(rows),
          'max_long_wall_flow_mm3_s': max(r['max_flow_mm3_s'] for r in rows),
          'config': config, 'sample_layers': samples,
          'limitations': 'Commanded steady-feed flow; excludes acceleration and physical extrusion behavior.'}
if args.start is not None:
    # The first layer has its own speed. The second is SpiralVase's
    # transition_in, which ramps E from spiral_starting_flow_ratio to 1.
    # Finishing adds another block at the final Z, tapering E back down.
    # Keep all three in the CSV, but compare only the steady ramp here.
    excluded = [r['layer'] for r in rows[:2]] + [rows[-1]['layer']]
    eligible = [r for r in rows if r['layer'] not in excluded]
    result['requested_ramp'] = {'start_mm3_s': args.start, 'step_mm3_s_per_mm': args.step,
                                'excluded_transition_layer_groups': excluded,
                                'max_abs_median_error_mm3_s': max((abs(r['median_error_mm3_s']) for r in eligible), default=None)}
if args.out:
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.with_suffix('.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    with args.out.with_suffix('.csv').open('w', newline='', encoding='utf-8') as output:
        writer = csv.DictWriter(output, fieldnames=rows[0])
        writer.writeheader()
        writer.writerows(rows)
print(json.dumps(result, indent=2))
