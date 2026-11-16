#!/bin/bash
# Renders every pose the studio uses into out/poses/<who>_<expr>.png (900 x 1170, 48 samples), skipping ones already there.
cd "$(dirname "$0")"
PY=${BPY:-/home/claude/bpyenv/bin/python}
for spec in sam:happy,surprised,thinking penny:happy,surprised,thinking zara:happy,surprised,thinking grace:happy,surprised,thinking \
            dev:happy,surprised,thinking maya:happy,surprised,thinking rex:sly,surprised,happy,wink dot:happy,surprised,wink; do
  who=${spec%%:*}
  for expr in $(echo ${spec#*:} | tr ',' ' '); do
    out=out/poses/${who}_${expr}.png
    [ -f "$out" ] && continue
    "$PY" cast3d.py "$who" "$expr" "$out" 900 1170 48 > /dev/null 2>&1 && echo "$(date +%H:%M:%S) $out" || echo "$(date +%H:%M:%S) FAILED $out"
  done
done
echo "$(date +%H:%M:%S) all done"
