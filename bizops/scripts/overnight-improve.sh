#!/bin/bash
# overnight-improve.sh — Nightly skill optimization
# Schedule via cron: 0 2 * * * cd /path/to/repo && ./bizops/scripts/overnight-improve.sh
# Run from monorepo root (needs access to .claude/skills and bizops/)

set -e

REPO_ROOT=$(git rev-parse --show-toplevel)
SKILLS_DIR="$REPO_ROOT/.claude/skills"
GLOBAL_LOG="$REPO_ROOT/bizops/global/memory/skill-improvement-log.md"
THRESHOLD=75

echo "🌙 Starting overnight improvement cycle..."
skills_checked=0
skills_improved=0

for skill_dir in $SKILLS_DIR/*/; do
  [ -d "$skill_dir" ] || continue
  skill_name=$(basename $skill_dir)
  eval_file="$skill_dir/eval.json"

  if [ -f "$eval_file" ]; then
    skills_checked=$((skills_checked + 1))
    pass_rate=$(jq '.history[-1].pass_rate // 0' $eval_file)

    if (( $(echo "$pass_rate < $THRESHOLD" | bc -l) )); then
      echo "[$skill_name] Below threshold ($pass_rate% < $THRESHOLD%). Improving..."

      for i in {1..5}; do
        claude -p \
          --system-prompt "You are a skill optimizer. Make ONE specific improvement based on failure patterns. Output ONLY the full updated SKILL.md content." \
          "Current skill: $(cat $skill_dir/SKILL.md)
           Recent failures: $(jq '.history[-1].failures // []' $eval_file)
           Make exactly ONE change." \
          > /tmp/improved_skill.md

        cp /tmp/improved_skill.md $skill_dir/SKILL.md

        total=0
        for run in {1..3}; do
          score=$(claude -p \
            --system-prompt "$(cat $skill_dir/SKILL.md)" \
            "$(jq -r '.test_prompt' $eval_file)" | \
            claude -p --tools '[]' \
            --system-prompt "Score this output against these assertions. Return ONLY a number (count of passed assertions)." \
            "Output: $(cat /dev/stdin) Assertions: $(jq '.assertions' $eval_file)")
          total=$((total + score))
        done
        median_score=$((total / 3))

        baseline=$(jq '.history[-1].score // 0' $eval_file)
        if [ $median_score -gt $baseline ]; then
          git add $skill_dir/SKILL.md
          git commit -m "skill-improve: $skill_name iteration $i — $baseline% → $median_score%"
          echo "  ✅ Iteration $i: Improved $baseline% → $median_score%"
          skills_improved=$((skills_improved + 1))
          break
        else
          git checkout -- $skill_dir/SKILL.md
          echo "  ↩️  Iteration $i: Regressed. Reverted."
        fi
      done
    fi
  fi
done

echo "" >> $GLOBAL_LOG
echo "## [$(date +%Y-%m-%d)] Overnight Improvement Cycle" >> $GLOBAL_LOG
echo "- Skills checked: $skills_checked" >> $GLOBAL_LOG
echo "- Skills improved: $skills_improved" >> $GLOBAL_LOG
echo "---" >> $GLOBAL_LOG

echo "🌅 Overnight cycle complete. Checked: $skills_checked, Improved: $skills_improved"
