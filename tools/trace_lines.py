#!/usr/bin/env python3
"""Line Usage Analyzer & Debugger.

Traces a Python file line-by-line during REAL execution and reports:
- Which lines were EXECUTED (coverage)
- Which lines were NOT EXECUTED (candidates for deletion)
- Real-time line tracing (debug mode)

Usage:
    python tools/trace_lines.py <target.py>                         # Report
    python tools/trace_lines.py <target.py> --live                  # Live debug
    python tools/trace_lines.py <target.py> --timeout 300           # Custom timeout
    python tools/trace_lines.py <target.py> --stop-after "texto"    # Stop at text
    python tools/trace_lines.py <target.py> --live --stop-after "Reenvio concluido"
    python tools/trace_lines.py <target.py> --max-users 1              # Stop after 1 user
    python tools/trace_lines.py <target.py> --live --max-users 1       # Live debug, 1 user
"""

import sys
import os
import signal

executed_lines = set()
target_abspath = None
source_lines = []
live_mode = False
debug_only = False
stop_after = None
max_users = 0


class _StopTracing(BaseException):
    pass


class _TimeoutError(Exception):
    pass


def _timeout_handler(signum, frame):
    raise _TimeoutError("Execution timed out")


def _tracer(frame, event, arg):
    if event == 'line':
        fname = os.path.abspath(frame.f_code.co_filename)
        if fname == target_abspath:
            lineno = frame.f_lineno
            executed_lines.add(lineno)
            if live_mode and lineno <= len(source_lines):
                func = frame.f_code.co_name
                line = source_lines[lineno - 1].rstrip()
                marker = ">>" if lineno in executed_lines else " >"
                print(
                    f"  {marker} L{lineno:>4} [{func:>30}] {line}",
                    file=sys.stderr,
                )
    return _tracer


class _WriteMonitor:
    def __init__(self, original_write, pattern, max_cycles=0):
        self.original_write = original_write
        self.pattern = pattern
        self.max_cycles = max_cycles
        self.cycles_seen = 0

    def __call__(self, text):
        if text and self.pattern and self.pattern in text:
            raise _StopTracing(f"Matched '{self.pattern}'")
        if self.max_cycles:
            import re
            m = re.search(r'--- Ciclo (\d+)', text)
            if m:
                self.cycles_seen = int(m.group(1))
                if self.cycles_seen > self.max_cycles:
                    raise _StopTracing(
                        f"Processed {self.max_cycles} user(s)"
                    )
        self.original_write(text)

    def flush(self):
        try:
            self.original_write.flush()
        except AttributeError:
            pass


def _count_code_lines(lines):
    code = set()
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            code.add(i)
    return code


def _print_report(filepath):
    code_lines = _count_code_lines(source_lines)
    unused = sorted(code_lines - executed_lines)
    used = sorted(code_lines & executed_lines)

    total_code = len(code_lines)
    total_executed = len(used)
    coverage_pct = total_executed * 100 // max(total_code, 1)

    print(f"\n{'=' * 70}")
    print(f" LINE USAGE REPORT: {os.path.basename(filepath)}")
    print(f"{'=' * 70}")
    print(f" Total code lines : {total_code}")
    print(f" Lines executed   : {total_executed} ({coverage_pct}%)")
    print(f" Lines NOT used   : {len(unused)}"
          + (" (review for deletion)" if unused else ""))

    if unused:
        print(f"\n--- UNUSED LINES (review for deletion) ---")
        for ln in unused:
            print(f"  {ln:>4}: {source_lines[ln - 1].rstrip()}")
        print(f"\n Tip: {len(unused)} line(s) never executed.")
        print(" They may be dead code, error handlers for edge cases")
        print(" not triggered in this run, or conditional branches.")
        print(" Run with --live to see execution flow in real time.")

    if used:
        print(f"\n--- EXECUTED LINES ---")
        for ln in used:
            print(f"  {ln:>4}: {source_lines[ln - 1].rstrip()}")

    if not unused:
        print("\n All code lines were executed. No candidates for deletion.")


def main():
    global target_abspath, source_lines, live_mode, debug_only, stop_after, max_users

    if len(sys.argv) < 2 or sys.argv[1] in ('-h', '--help'):
        print(__doc__, file=sys.stderr)
        sys.exit(0 if len(sys.argv) > 1 else 1)

    filepath = os.path.abspath(sys.argv[1])
    timeout = 120
    cwd = None

    args = sys.argv[2:]
    i = 0
    while i < len(args):
        if args[i] == '--timeout' and i + 1 < len(args):
            timeout = int(args[i + 1])
            i += 2
        elif args[i] == '--live':
            live_mode = True
            i += 1
        elif args[i] == '--debug-only':
            live_mode = True
            debug_only = True
            i += 1
        elif args[i] == '--stop-after' and i + 1 < len(args):
            stop_after = args[i + 1]
            i += 2
        elif args[i] == '--max-users' and i + 1 < len(args):
            max_users = int(args[i + 1])
            i += 2
        elif args[i] == '--cwd' and i + 1 < len(args):
            cwd = args[i + 1]
            i += 2
        else:
            print(f"Unknown option: {args[i]}", file=sys.stderr)
            sys.exit(1)

    if not os.path.isfile(filepath):
        print(f"File not found: {filepath}", file=sys.stderr)
        sys.exit(1)

    target_abspath = filepath

    with open(filepath) as f:
        source_lines = f.readlines()

    orig_cwd = os.getcwd()
    script_dir = os.path.dirname(filepath)
    target_dir = os.path.abspath(cwd) if cwd else script_dir
    os.chdir(target_dir)

    try:
        code = compile(''.join(source_lines), filepath, 'exec')
    except SyntaxError as e:
        print(f"Syntax error: {e}", file=sys.stderr)
        os.chdir(orig_cwd)
        sys.exit(1)

    has_alarm = hasattr(signal, 'SIGALRM')
    if has_alarm:
        signal.signal(signal.SIGALRM, _timeout_handler)
        signal.alarm(timeout)

    if live_mode:
        basename = os.path.basename(filepath)
        print(f"\n{'=' * 70}", file=sys.stderr)
        print(f" LIVE DEBUG: {basename}", file=sys.stderr)
        print(f"{'=' * 70}", file=sys.stderr)
        print(f" Timeout: {timeout}s | CWD: {os.getcwd()}", file=sys.stderr)
        if stop_after:
            print(f" Stop after: '{stop_after}'", file=sys.stderr)
        if max_users:
            print(f" Max users : {max_users}", file=sys.stderr)
        print(f" Legend: >> = first hit   > = re-executed", file=sys.stderr)
        print(f"{'=' * 70}\n", file=sys.stderr)

    namespace = {'__name__': '__main__', '__file__': filepath}

    # Intercept stdout to detect stop pattern
    orig_stdout_write = sys.stdout.write
    if stop_after or max_users:
        sys.stdout.write = _WriteMonitor(orig_stdout_write, stop_after, max_users)

    error = None
    stop_reason = None
    sys.settrace(_tracer)
    try:
        exec(code, namespace)
    except _StopTracing as e:
        stop_reason = str(e)
        print(f"\n[!] {stop_reason}", file=sys.stderr)
    except _TimeoutError:
        stop_reason = f"Timeout ({timeout}s)"
        print(f"\n[!] Stopped after {timeout}s timeout.", file=sys.stderr)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        stop_reason = "KeyboardInterrupt"
        print(f"\n[!] Interrupted by user.", file=sys.stderr)
    except BaseException as e:
        error = e
        print(f"\n[!] Error: {e}", file=sys.stderr)
    finally:
        sys.settrace(None)
        if has_alarm:
            signal.alarm(0)
        # Restore original stdout write
        if stop_after or max_users:
            sys.stdout.write = orig_stdout_write
        os.chdir(orig_cwd)

    if not debug_only:
        _print_report(filepath)


if __name__ == '__main__':
    main()
