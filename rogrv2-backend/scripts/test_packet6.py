import sys, pathlib, json
# Ensure imports regardless of CWD
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1]))

from intelligence.claims.extract import extract_claims
from intelligence.strategy.plan import build_search_plans
from intelligence.gather.pipeline import build_evidence_for_claim
from intelligence.consensus.aggregate import consensus_metrics
from intelligence.score.scoring import claim_score, overall_score

SAMPLE = (
    "The mayor says the new bridge will cost $250 million and open in 2027. "
    "Officials indicate prior estimates were lower because steel prices rose. "
    "Residents claim traffic has doubled since 2020. "
    "This announcement follows a year of public hearings."
)

def synth_candidates(claim_text, arm):
    base_kw = " ".join(claim_text.split()[:6])
    if arm == "A":
        return [
            {"url":"https://city.gov/reports/bridge-2027-plan","title":"City issues 2027 bridge plan","snippet":f"{base_kw} official report outlines costs and timeline 2027 with financial details."},
            {"url":"https://localnews.example/bridge-costs","title":"Bridge costs rise due to steel","snippet":"Steel prices increased; estimates adjusted; timeline remains on track for 2027 according to officials."},
            {"url":"https://opinion.example/blog-bridge","title":"Opinion: concerns remain","snippet":"Some residents are worried; details unclear; no figures given."},
        ]
    else:
        return [
            {"url":"https://watchgroup.example/bridge-oversight","title":"Watch group flags issues","snippet":"Report suggests the 2027 claim may be optimistic; not confirmed by independent audit."},
            {"url":"https://transport.db/stats","title":"Traffic statistics 2020-2024","snippet":f"Data shows traffic doubled since 2020 in corridor; numbers compiled annually 2021 2022 2023."},
            {"url":"https://forum.example/thread","title":"Community thread","snippet":"People discuss the bridge; mixed views; uncertain details."},
        ]

def main():
    claims = extract_claims(SAMPLE)
    assert any(c.tier.value=="primary" for c in claims)
    assert any(c.tier.value=="secondary" for c in claims)
    assert any(c.tier.value=="tertiary" for c in claims)

    plans = build_search_plans(claims)
    results = []
    for c in claims[:3]:
        armA = build_evidence_for_claim(c.text, synth_candidates(c.text, "A"))
        armB = build_evidence_for_claim(c.text, synth_candidates(c.text, "B"))
        cons = consensus_metrics(armA, armB)
        ev = armA + armB
        score, label, expl = claim_score(ev)
        results.append({"tier": c.tier.value, "score": score, "label": label, "explanation": expl, "consensus": cons})

    overall, overall_label = overall_score(results)

    assert all(0 <= r["score"] <= 100 for r in results), "scores must be 0..100"
    assert all(r["label"] in {"True","Mostly True","Mixed","Mostly False","False"} for r in results)
    assert 0 <= overall <= 100 and overall_label in {"True","Mostly True","Mixed","Mostly False","False"}

    print("PASS")
    print(json.dumps({
        "claims_preview":[{"tier":r["tier"],"score":r["score"],"label":r["label"]} for r in results],
        "overall":{"score":overall,"label":overall_label},
        "example_consensus":results[0]["consensus"]
    }, ensure_ascii=False))

if __name__ == "__main__":
    main()