#!/bin/zsh
# usage: run_relearn.sh ROM OUTNAME CASES [pre-menu] [extra]
# SCRATCH: output directory (set in the environment)
S=${SCRATCH:?set SCRATCH}
ROOT=$(cd "$(dirname "$0")/../../../.." && pwd)
cd "$ROOT"
export EMU_HARNESS_DATA=$ROOT/work EMU_TOOLS_DIR=$ROOT/work/tools
"$ROOT/.venv/bin/python" work/tools/investigations/crash_reports/emu_saffron_retry.py --rom $1 --save $ROOT/work/build/origin_hg_v4.0.3_en_wip.sav --cases $3 --no-reset --fill-party --pre-menu ${4:-bag} --out $S/inv/crash-reports-relearner-wallpaper/$2 $5 > $S/inv/crash-reports-relearner-wallpaper/$2.log 2>&1
python3 - <<P
import json
r=json.load(open("$S/inv/crash-reports-relearner-wallpaper/$2/report.json"))
for c in r['cases']: print(c['case'],c.get('outcome'),c.get('error'),len(c.get('eligible') or []))
print(r.get('heap_checks'),r.get('heap_table_errors'),r['rom_unchanged'],r['save_unchanged'])
P
