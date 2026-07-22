#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd -P)
CRON_SOURCE_DIR=${CRON_SOURCE_DIR:-"$REPO_ROOT/hermes-cron"}
MODE=${1:-add}
PROFILE_NAME=${HERMES_PROFILE_NAME:-${2:-}}
CRON_SELECTION=${CRON_SELECTION:-${3:-}}
HERMES_BIN=${HERMES_BIN:-hermes}
HERMES_HOME_DIR=${HERMES_HOME:-"$HOME/.hermes"}
PROFILES_DIR=${HERMES_PROFILES_DIR:-"$HERMES_HOME_DIR/profiles"}
GLOBAL_SCRIPTS_DIR=${HERMES_SCRIPTS_DIR:-"$HERMES_HOME_DIR/scripts"}

usage() {
  cat <<'EOF'
Usage:
  scripts/add-hermes-cron.sh [add|list] [profile_name] [cron_name|all]

Env overrides:
  HERMES_PROFILE_NAME   Target Hermes profile name. Optional.
  CRON_SELECTION       Cron config basename to use, without .json. Optional.
  CRON_SOURCE_DIR      Source cron JSON dir. Default: <repo>/hermes-cron
  HERMES_BIN           Hermes CLI binary. Default: hermes
  HERMES_HOME          Hermes home dir. Default: ~/.hermes
  HERMES_PROFILES_DIR  Hermes profiles dir. Default: $HERMES_HOME/profiles
  HERMES_SCRIPTS_DIR   Hermes scripts dir. Default: $HERMES_HOME/scripts

Behavior:
  - reads JSON files under CRON_SOURCE_DIR
  - converts supported JSON fields into `hermes cron create ...` arguments
  - if profile name is empty, prompts user to select profile first
  - if cron selection is empty, prompts user to select one config or `all`
  - if JSON script points to repo/local file, script copies basename under $HERMES_HOME/profiles/<profile>/scripts/
  - cron config keeps basename-only `--script <name>`
  - list mode prints generated CLI commands and planned script installs
  - add mode installs needed scripts, then runs generated CLI commands

Supported JSON keys:
  - schedule_display | schedule.display | schedule.expr | schedule
  - prompt
  - name
  - deliver
  - repeat.times | repeat
  - skills | skill
  - script
  - no_agent
  - workdir

Notes:
  - runtime fields like id, next_run_at, last_run_at, state are ignored
  - if profile name is set, script adds `--profile <name>` to each command
EOF
}

if [[ ${MODE} == "-h" || ${MODE} == "--help" ]]; then
  usage
  exit 0
fi

if [[ ! -d "$CRON_SOURCE_DIR" ]]; then
  printf 'Missing cron source dir: %s\n' "$CRON_SOURCE_DIR" >&2
  exit 1
fi

if [[ "$MODE" != "list" && "$MODE" != "add" ]]; then
  usage >&2
  exit 1
fi

select_profile_if_needed() {
  [[ -n "$PROFILE_NAME" ]] && return 0
  [[ -t 0 ]] || {
    printf 'Missing profile name. Pass arg, set HERMES_PROFILE_NAME, or run interactively.\n' >&2
    exit 1
  }
  [[ -d "$PROFILES_DIR" ]] || {
    printf 'Missing Hermes profiles dir: %s\n' "$PROFILES_DIR" >&2
    exit 1
  }

  local profiles=()
  while IFS= read -r name; do
    [[ -n "$name" ]] && profiles+=("$name")
  done < <(find "$PROFILES_DIR" -mindepth 1 -maxdepth 1 -type d -exec basename {} \; | sort)

  [[ ${#profiles[@]} -gt 0 ]] || {
    printf 'No Hermes profiles found under: %s\n' "$PROFILES_DIR" >&2
    exit 1
  }

  printf 'Select Hermes profile:\n' >&2
  local i=1
  for name in "${profiles[@]}"; do
    printf '  %d) %s\n' "$i" "$name" >&2
    ((i += 1))
  done

  local pick
  while true; do
    read -r -p 'Profile number: ' pick
    [[ "$pick" =~ ^[0-9]+$ ]] || {
      printf 'Enter number 1-%d.\n' "${#profiles[@]}" >&2
      continue
    }
    if (( pick >= 1 && pick <= ${#profiles[@]} )); then
      PROFILE_NAME=${profiles[$((pick - 1))]}
      return 0
    fi
    printf 'Enter number 1-%d.\n' "${#profiles[@]}" >&2
  done
}

CRON_FILES=()
while IFS= read -r src; do
  CRON_FILES+=("$src")
done < <(find "$CRON_SOURCE_DIR" -mindepth 1 -maxdepth 1 -type f -name '*.json' | sort)

if [[ ${#CRON_FILES[@]} -eq 0 ]]; then
  printf 'No cron JSON files found under: %s\n' "$CRON_SOURCE_DIR" >&2
  exit 1
fi

select_cron_if_needed() {
  [[ -n "$CRON_SELECTION" ]] && return 0
  [[ -t 0 ]] || {
    printf 'Missing cron selection. Pass arg, set CRON_SELECTION, or run interactively.\n' >&2
    exit 1
  }

  printf 'Select cron config:\n' >&2
  local i=1
  for src in "${CRON_FILES[@]}"; do
    printf '  %d) %s\n' "$i" "$(basename "$src" .json)" >&2
    ((i += 1))
  done
  printf '  %d) all\n' "$i" >&2

  local pick
  while true; do
    read -r -p 'Cron number: ' pick
    [[ "$pick" =~ ^[0-9]+$ ]] || {
      printf 'Enter number 1-%d.\n' "$i" >&2
      continue
    }
    if (( pick >= 1 && pick < i )); then
      CRON_SELECTION=$(basename "${CRON_FILES[$((pick - 1))]}" .json)
      return 0
    fi
    if (( pick == i )); then
      CRON_SELECTION=all
      return 0
    fi
    printf 'Enter number 1-%d.\n' "$i" >&2
  done
}

select_profile_if_needed
select_cron_if_needed

FILTERED_CRON_FILES=()
if [[ "$CRON_SELECTION" == "all" ]]; then
  FILTERED_CRON_FILES=("${CRON_FILES[@]}")
else
  selected_path="$CRON_SOURCE_DIR/$CRON_SELECTION.json"
  [[ -f "$selected_path" ]] || {
    printf 'Cron config not found: %s\n' "$selected_path" >&2
    exit 1
  }
  FILTERED_CRON_FILES=("$selected_path")
fi

python3 - "$MODE" "$HERMES_BIN" "$PROFILE_NAME" "$REPO_ROOT" "$CRON_SOURCE_DIR" "$GLOBAL_SCRIPTS_DIR" "$HERMES_HOME_DIR" "${FILTERED_CRON_FILES[@]}" <<'PY'
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Optional


def load_json(path: Path):
    with path.open() as f:
        return json.load(f)


def schedule_text(job: dict) -> str:
    if isinstance(job.get("schedule_display"), str) and job["schedule_display"]:
        return job["schedule_display"]
    schedule = job.get("schedule")
    if isinstance(schedule, dict):
        for key in ("display", "expr"):
            value = schedule.get(key)
            if isinstance(value, str) and value:
                return value
    if isinstance(schedule, str) and schedule:
        return schedule
    raise SystemExit(f"Missing schedule display/expr in job: {job.get('name') or '<unnamed>'}")


def resolve_repo_script(script_value: str, repo_root: Path, cron_source_dir: Path, src_path: Path):
    candidates = []
    script_path = Path(script_value)
    if script_path.is_absolute():
        candidates.append(script_path)
    else:
        candidates.extend([
            src_path.parent / script_path,
            cron_source_dir / script_path,
            repo_root / script_path,
            repo_root / "scripts" / script_path.name,
        ])
    for candidate in candidates:
        if candidate.exists() and candidate.is_file():
            return candidate.resolve()
    return None


def prepare_script(job: dict, profile_name: str, repo_root: Path, cron_source_dir: Path, global_scripts_dir: Path, hermes_home_dir: Path, src_path: Path):
    script = job.get("script")
    if not isinstance(script, str) or not script:
        return None, None

    script_path = Path(script)
    if not script_path.is_absolute() and script_path.name == script:
        existing_global = global_scripts_dir / script
        if existing_global.exists() and existing_global.is_file():
            return script, None

    resolved_source = resolve_repo_script(script, repo_root, cron_source_dir, src_path)
    if resolved_source is None:
        return script_path.name, None

    profile_dir = hermes_home_dir / "profiles" / profile_name
    profile_script_target = profile_dir / "scripts" / resolved_source.name

    install_plan = {
        "source": resolved_source,
        "profile_script_target": profile_script_target,
    }
    return resolved_source.name, install_plan


def build_command(hermes_bin: str, profile_name: str, job: dict, script_arg: Optional[str]):
    schedule = schedule_text(job)
    prompt = job.get("prompt")
    if not isinstance(prompt, str) or not prompt.strip():
        raise SystemExit(f"Missing prompt in job: {job.get('name') or '<unnamed>'}")

    cmd = [hermes_bin]
    if profile_name:
        cmd.extend(["--profile", profile_name])
    cmd.extend(["cron", "create", schedule, prompt])

    name = job.get("name")
    if isinstance(name, str) and name:
        cmd.extend(["--name", name])

    deliver = job.get("deliver")
    if isinstance(deliver, str) and deliver:
        cmd.extend(["--deliver", deliver])

    repeat = job.get("repeat")
    repeat_times = None
    if isinstance(repeat, dict):
        repeat_times = repeat.get("times")
    elif isinstance(repeat, int):
        repeat_times = repeat
    if isinstance(repeat_times, int):
        cmd.extend(["--repeat", str(repeat_times)])

    skills = []
    if isinstance(job.get("skills"), list):
        skills.extend(s for s in job["skills"] if isinstance(s, str) and s)
    skill = job.get("skill")
    if isinstance(skill, str) and skill:
        skills.append(skill)
    for skill_name in dict.fromkeys(skills):
        cmd.extend(["--skill", skill_name])

    if isinstance(script_arg, str) and script_arg:
        cmd.extend(["--script", script_arg])

    if job.get("no_agent") is True:
        cmd.append("--no-agent")

    workdir = job.get("workdir")
    if isinstance(workdir, str) and workdir:
        cmd.extend(["--workdir", workdir])

    return cmd


mode = sys.argv[1]
hermes_bin = sys.argv[2]
profile_name = sys.argv[3]
repo_root = Path(sys.argv[4])
cron_source_dir = Path(sys.argv[5])
global_scripts_dir = Path(sys.argv[6])
hermes_home_dir = Path(sys.argv[7])
source_paths = [Path(p) for p in sys.argv[8:]]
plans = []
for src_path in source_paths:
    job = load_json(src_path)
    script_arg, install_plan = prepare_script(job, profile_name, repo_root, cron_source_dir, global_scripts_dir, hermes_home_dir, src_path)
    plans.append((src_path, install_plan, build_command(hermes_bin, profile_name, job, script_arg)))

if mode == "list":
    for src_path, install_plan, cmd in plans:
        print(f"{src_path}:")
        if install_plan is not None:
            print(f"  install-script {install_plan['source']} -> {install_plan['profile_script_target']}")
        print("  " + shlex.join(cmd))
    raise SystemExit(0)

for src_path, install_plan, cmd in plans:
    if install_plan is not None:
        install_plan["profile_script_target"].parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(install_plan["source"], install_plan["profile_script_target"])
        print(f"installed script {install_plan['source']} -> {install_plan['profile_script_target']}")
    print(f"running {src_path}: {shlex.join(cmd)}")
    subprocess.run(cmd, check=True)
PY
