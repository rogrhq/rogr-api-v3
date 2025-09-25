from typing import Dict, List, Set

def _dedupe_keys(evs: List[Dict]) -> Set[str]:
    return {e["source"]["dedupe_key"] for e in evs}

def consensus_metrics(arm_a: List[Dict], arm_b: List[Dict]) -> Dict:
    set_a = _dedupe_keys(arm_a)
    set_b = _dedupe_keys(arm_b)
    overlap = len(set_a & set_b)
    union = len(set_a | set_b) or 1
    overlap_ratio = overlap / union

    def stance_totals(evs: List[Dict]) -> Dict[str, int]:
        t = {"support":0,"refute":0,"neutral":0}
        for e in evs:
            t[e["stance"]] += 1
        return t

    ta, tb = stance_totals(arm_a), stance_totals(arm_b)
    support = ta["support"] + tb["support"]
    refute  = ta["refute"]  + tb["refute"]
    total   = max(1, support + refute)
    conflict_score = min(1.0, abs(support - refute) / total)  # 0 (balanced) .. 1 (one-sided)

    # Stability: proportion of overlapping items that also agree in stance when present in both
    stance_agree = 0
    for e in arm_a:
        dk = e["source"]["dedupe_key"]
        if dk in set_b:
            for eb in arm_b:
                if eb["source"]["dedupe_key"] == dk and eb["stance"] == e["stance"]:
                    stance_agree += 1
                    break
    stability = stance_agree / (overlap or 1)

    return {
        "overlap_ratio": round(overlap_ratio,3),
        "conflict_score": round(conflict_score,3),
        "stability": round(stability,3),
        "totals": {"support": support, "refute": refute}
    }