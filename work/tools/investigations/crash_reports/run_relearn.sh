#!/bin/zsh
# usage: run_relearn.sh ROM OUTNAME CASES [pre-menu] [extra]
S=/private/tmp/claude-501/-Users-simonvergauwen-Developer-poke/c8491cb6-81cf-412e-b864-3295209437a7/scratchpad
cd /Users/simonvergauwen/Developer/poke-inv-crash-reports
export EMU_HARNESS_DATA=/Users/simonvergauwen/Developer/poke/work EMU_TOOLS_DIR=/Users/simonvergauwen/Developer/poke/work/tools
/Users/simonvergauwen/Developer/poke/.venv/bin/python work/tools/investigations/crash_reports/emu_saffron_retry.py --rom $1 --save /Users/simonvergauwen/Developer/poke/work/build/origin_hg_v4.0.3_en_wip.sav --cases $3 --no-reset --fill-party --pre-menu ${4:-bag} --out $S/inv/crash-reports-relearner-wallpaper/$2 $5 > $S/inv/crash-reports-relearner-wallpaper/$2.log 2>&1
python3 - <<P
import json
r=json.load(open("$S/inv/crash-reports-relearner-wallpaper/$2/report.json"))
for c in r['cases']: print(c['case'],c.get('outcome'),c.get('error'),len(c.get('eligible') or []))
print(r.get('heap_checks'),r.get('heap_table_errors'),r['rom_unchanged'],r['save_unchanged'])
P
