#!/usr/bin/env bash

# BIOTech Futures Hub – consolidated test runner with per-test summaries.
# -----------------------------------------------------------------------
# Requirements:
#   backend: pip install -r backend/requirements.txt
#   frontend: (cd frontend && npm install)
# Usage:
#   chmod +x tests/run-all-tests.sh
#   ./tests/run-all-tests.sh

set -u
set -o pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")"/.. && pwd)"

declare -a step_names
declare -a step_desc
declare -a step_dirs
declare -a step_cmds
declare -a step_types
declare -a step_status
declare -a step_logs

append_step() {
  step_names+=("$1")
  step_desc+=("$2")
  step_dirs+=("$3")
  step_cmds+=("$4")
  step_types+=("$5")
  step_status+=(999)
  step_logs+=("")
}

append_step "Backend unit & API tests" \
  "Django/DRF domain endpoints & permissions (tests.backend)" \
  "backend" \
  "python manage.py test tests.backend --verbosity 2" \
  "django"

append_step "Cross-service backend flows" \
  "Magic-link + admin workflows (tests.api, tests.integration)" \
  "backend" \
  "python manage.py test tests.api tests.integration --verbosity 2" \
  "django"

append_step "Frontend Vitest suite" \
  "Pinia stores, Vue components, router guards (npm run test)" \
  "frontend" \
  "npx --yes vitest run --reporter=json" \
  "vitest"

print_heading() {
  printf '\n\033[1;34m==> %s\033[0m\n' "$1"
}

print_suite_table() {
  local type="$1"
  local log_file="$2"
  local title="$3"

  case "$type" in
    django)
      python - "$log_file" "$project_root" <<'PY'
import os
import re
import sys

def humanize(name: str) -> str:
    if name.startswith('test_'):
        name = name[5:]
    parts = [p for p in re.split(r'_+', name) if p]
    return ' '.join(part.capitalize() for part in parts) or name

def status_icon(token: str):
    token = token.strip().lower()
    if token.startswith('ok'):
        return '✅'
    if token.startswith('fail') or token.startswith('error'):
        return '❌'
    if token.startswith('skip'):
        return '⚠'
    return None

log_path, project_root = sys.argv[1], sys.argv[2]
pattern = re.compile(r'^(test[\w\d_]+) \(([\w\.]+)\)\s+\.\.\.\s*(.*)$')
rows = []
pending = None
with open(log_path, 'r', encoding='utf-8', errors='ignore') as stream:
    for raw_line in stream:
        line = raw_line.rstrip()
        m = pattern.match(line.strip())
        if m:
            test_name, location, tail = m.groups()
            module, _class = location.rsplit('.', 1)
            module_path = module.replace('tests.', '', 1).replace('.', '/')
            test_id = f"{module_path}.{test_name}"
            messages = [tail] if tail else []
            icon = status_icon(tail)
            if icon:
                desc = humanize(test_name)
                if messages and not icon == '✅':
                    desc += f" ({messages[0]})"
                rows.append((icon, test_id, desc))
            else:
                pending = {
                    'id': test_id,
                    'name': humanize(test_name),
                    'messages': [tail] if tail else [],
                }
            continue

        if pending is not None:
            token_icon = status_icon(line)
            if token_icon:
                desc = pending['name']
                if pending['messages'] and not token_icon == '✅':
                    desc += f" ({pending['messages'][0]})"
                rows.append((token_icon, pending['id'], desc))
                pending = None
            else:
                if line.strip():
                    pending['messages'].append(line.strip())

if not rows:
    sys.exit(0)

headers = ('Status', 'Test', 'Description')
widths = [len(h) for h in headers]
for status, test_id, desc in rows:
    widths[0] = max(widths[0], len(status))
    widths[1] = max(widths[1], len(test_id))
    widths[2] = max(widths[2], len(desc))

border = ' '.join('-' * w for w in widths)
print('\n\033[1;36mPer-test summary\033[0m')
print(' '.join(h.ljust(w) for h, w in zip(headers, widths)))
print(border)
for status, test_id, desc in rows:
    print(' '.join(value.ljust(width) for value, width in zip((status, test_id, desc), widths)))
PY
      ;;
    vitest)
      python - "$log_file" "$project_root" <<'PY'
import json
import os
import sys

def relative(path: str, root: str) -> str:
    try:
        return os.path.relpath(path, root)
    except ValueError:
        return path

log_path, project_root = sys.argv[1], sys.argv[2]
content = open(log_path, 'r', encoding='utf-8', errors='ignore').read().strip()
if not content:
    sys.exit(0)
try:
    data = json.loads(content)
except json.JSONDecodeError:
    sys.exit(0)

def icon_for(status: str) -> str:
    status = status.lower()
    if status == 'passed' or status == 'success':
        return '✅'
    if status in {'failed', 'fail'}:
        return '❌'
    if status in {'skipped', 'pending', 'todo'}:
        return '⚠'
    return '•'

rows = []
for result in data.get('testResults', []):
    file_path = relative(result.get('name', ''), project_root)
    assertions = result.get('assertionResults', [])
    if assertions:
        for case in assertions:
            status = icon_for(case.get('status', ''))
            title = case.get('title') or 'Unnamed'
            rows.append((status, f"{file_path}::{title}", ' '.join(case.get('ancestorTitles', [])) or title))
    else:
        status = icon_for(result.get('status', 'failed'))
        message = result.get('message', '').split('\n')[0]
        description = message if message else 'No assertions run'
        rows.append((status, file_path or 'unknown', description))

if not rows:
    sys.exit(0)

headers = ('Status', 'Test', 'Details')
widths = [len(h) for h in headers]
for status, test_id, desc in rows:
    widths[0] = max(widths[0], len(status))
    widths[1] = max(widths[1], len(test_id))
    widths[2] = max(widths[2], len(desc))

border = ' '.join('-' * w for w in widths)
print('\n\033[1;36mPer-test summary\033[0m')
print(' '.join(h.ljust(w) for h, w in zip(headers, widths)))
print(border)
for status, test_id, desc in rows:
    print(' '.join(value.ljust(width) for value, width in zip((status, test_id, desc), widths)))
PY
      ;;
  esac
}

for idx in "${!step_names[@]}"; do
  print_heading "${step_names[$idx]}"
  log_file="$(mktemp)"
  (
    cd "${project_root}/${step_dirs[$idx]}" || exit 1
    set -o pipefail
    eval "${step_cmds[$idx]}" 2>&1 | tee "$log_file"
    echo "${PIPESTATUS[0]}" >"$log_file.exit"
  )
  exit_code=$(<"$log_file.exit")
  rm -f "$log_file.exit"
  step_status[$idx]=$exit_code
  step_logs[$idx]=$log_file

  print_suite_table "${step_types[$idx]}" "$log_file" "${step_names[$idx]}"
  rm -f "$log_file"

  if [[ $exit_code -ne 0 ]]; then
    printf '\033[1;31mStep failed with exit code %d\033[0m\n' "$exit_code"
  else
    printf '\033[1;32mStep completed successfully\033[0m\n'
  fi

done

printf '\n\033[1;37m%-6s | %-34s | %-60s\033[0m\n' "Status" "Suite" "Coverage"
printf '\033[1;37m%s\033[0m\n' "---------------------------------------------------------------------------------------------"
for idx in "${!step_names[@]}"; do
  code=${step_status[$idx]}
  icon='❌'
  [[ $code -eq 0 ]] && icon='✅'
  printf '%-6s | %-34s | %-60s\n' "$icon" "${step_names[$idx]}" "${step_desc[$idx]}"
done

overall_exit=0
for code in "${step_status[@]}"; do
  if [[ $code -ne 0 ]]; then
    overall_exit=1
    break
  fi
done

exit $overall_exit
