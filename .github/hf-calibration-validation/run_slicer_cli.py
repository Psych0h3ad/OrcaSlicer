"""Run the slicer's documented CLI with no foreground window."""
from pathlib import Path
import argparse
import json
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--exe', type=Path, required=True)
parser.add_argument('--log', type=Path, required=True)
parser.add_argument('--timeout', type=int, default=180)
parser.add_argument('arguments', nargs=argparse.REMAINDER)
args = parser.parse_args()
arguments = args.arguments[1:] if args.arguments[:1] == ['--'] else args.arguments
args.log.parent.mkdir(parents=True, exist_ok=True)
startup = subprocess.STARTUPINFO()
startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow = subprocess.SW_HIDE
command = [str(args.exe.resolve()), *arguments]
start = time.perf_counter()
with args.log.open('wb') as output:
    result = subprocess.run(command, cwd=args.exe.resolve().parent,
                            stdout=output, stderr=subprocess.STDOUT,
                            timeout=args.timeout, startupinfo=startup,
                            creationflags=subprocess.CREATE_NO_WINDOW)
record = {'command': command, 'exit_code': result.returncode,
          'elapsed_seconds': round(time.perf_counter() - start, 3),
          'log': str(args.log.resolve())}
args.log.with_suffix('.result.json').write_text(json.dumps(record, indent=2), encoding='utf-8')
print(json.dumps(record))
raise SystemExit(result.returncode)
