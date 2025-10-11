# Emergency Rollback Procedure

## Quick Rollback (< 5 minutes)

git log --oneline | head -10
git checkout [commit-before-day-12]
systemctl restart rogrv2
curl -X POST http://localhost:8000/analyses/preview -d '{"text":"Test"}' | jq

## Partial Rollback

Keep P19-P25 clean, restore P26-P29 only:
git checkout HEAD~1 -- intelligence/content/p26_dual_researchers.py
git checkout HEAD~1 -- intelligence/content/p27_consensus.py
git checkout HEAD~1 -- intelligence/content/p28_diversify.py
git checkout HEAD~1 -- intelligence/content/p29_diversify_controls.py
systemctl restart rogrv2

## When to Rollback

Immediate rollback if:
- Service will not start
- All requests failing
- Memory crashes
- Data corruption

Debug first if:
- Single request fails
- Minor errors
- Slow performance

## After Rollback

curl http://localhost:8000/health
python3 tests/test_p22_live.py
tail -f /var/log/rogrv2/error.log
