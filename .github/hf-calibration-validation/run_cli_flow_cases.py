"""Exercise normal CLI slicing and check active variant and MVS limits."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('--exe', type=Path, required=True)
parser.add_argument('--label', required=True)
args = parser.parse_args()
folder = Path(__file__).resolve().parent
root = folder / 'cli-flow-cases'
cases = json.loads((root / 'cases.json').read_text())
results = []
for case in cases:
    output = folder / ('cli-' + args.label) / case['name']
    output.mkdir(parents=True, exist_ok=True)
    log = output / 'slice.log'
    command = [sys.executable, str(folder / 'run_slicer_cli.py'), '--exe', str(args.exe.resolve()),
               '--log', str(log), '--', '--allow-newer-file', '--slice', '1',
               '--outputdir', str(output), str(root / case['input'])]
    process = subprocess.run(command, capture_output=True, text=True)
    status = {'name': case['name'], 'expected_mm3_s': case['expected_long_wall_flow_mm3_s'],
              'cli_process_exit_code': process.returncode, 'status': 'FAIL'}
    record_file = log.with_suffix('.result.json')
    if record_file.exists():
        status['slicer_exit_code'] = json.loads(record_file.read_text())['exit_code']
    gcodes = list(output.glob('*.gcode'))
    if process.returncode == 0 and len(gcodes) == 1:
        prefix = output / 'flow'
        analysis = subprocess.run([sys.executable, str(folder / 'analyze_calibration.py'),
                                   str(gcodes[0]), '--out', str(prefix)],
                                  capture_output=True, text=True)
        if analysis.returncode == 0:
            flow = json.loads(prefix.with_suffix('.json').read_text())
            status.update({'observed_max_mm3_s': flow['max_long_wall_flow_mm3_s'],
                           'gcode_sha256': flow['sha256'], 'config': flow['config']})
            error = abs(status['observed_max_mm3_s'] - status['expected_mm3_s'])
            status['abs_error_mm3_s'] = error
            status['status'] = 'PASS' if error <= 0.01 else 'FAIL'
        else:
            status['error'] = analysis.stderr[-1500:]
    else:
        status['error'] = log.read_text(errors='replace')[-1500:]
    results.append(status)
    print(json.dumps(status), flush=True)
result = {'label': args.label,
          'scope': 'Engine-only: preconfigured normal CLI slices. GUI calibration generation and preservation are not exercised.',
          'exe_sha256': hashlib.sha256(args.exe.read_bytes()).hexdigest(),
          'all_pass': all(r['status'] == 'PASS' for r in results), 'cases': results}
dll = args.exe.parent / 'Snapmaker_Orca.dll'
if dll.exists():
    result['dll_sha256'] = hashlib.sha256(dll.read_bytes()).hexdigest()
report = folder.parent / 'outputs' / ('cli-' + args.label + '-results.json')
report.parent.mkdir(parents=True, exist_ok=True)
report.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
print(report)
raise SystemExit(0 if result['all_pass'] else 1)
