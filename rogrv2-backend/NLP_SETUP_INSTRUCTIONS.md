# Level 2 Semantic NLP Setup Instructions

## Installation Steps

### 1. Install Python Dependencies

```bash
pip install -r requirements.txt
```

This will install:
- `transformers>=4.30.0` (Hugging Face models)
- `torch>=2.0.0` (PyTorch for model inference)
- `spacy>=3.5.0` (spaCy NLP library)

### 2. Download spaCy Language Model

After installing spacy, you need to download the English language model:

```bash
python -m spacy download en_core_web_sm
```

**Note:** This is a ~50MB download and is required for entity recognition and dependency parsing.

### 3. Verify Installation

Test that everything is working:

```python
python -c "
from intelligence.claims.nlp_interpret import NLP_AVAILABLE, parse_claim_nlp
print(f'NLP Available: {NLP_AVAILABLE}')
if NLP_AVAILABLE:
    result = parse_claim_nlp('Water boils at 100 degrees Celsius')
    print(f'Concept: {result[\"concept\"]}')
    print(f'Dimension: {result[\"dimension\"]}')
    print(f'Confidence: {result[\"confidence\"]}')
"
```

Expected output:
```
NLP Available: True
Concept: water 100 degrees celsius measurement
Dimension: temperature
Confidence: 0.9
```

## Models Used

### spaCy: en_core_web_sm
- **Size:** ~50MB
- **Purpose:** Entity recognition, dependency parsing, part-of-speech tagging
- **Download:** `python -m spacy download en_core_web_sm`

### BART: facebook/bart-large-mnli
- **Size:** ~1.6GB (downloaded automatically on first use)
- **Purpose:** Zero-shot classification for domain detection
- **Cache:** `~/.cache/huggingface/`

### BERT: dslim/bert-base-NER
- **Size:** ~400MB (downloaded automatically on first use)
- **Purpose:** Enhanced named entity recognition
- **Cache:** `~/.cache/huggingface/`

## Total Disk Space Required

- Python packages: ~3GB
- Models: ~2GB
- **Total:** ~5GB

## Memory Requirements

- Minimum: 2GB RAM
- Recommended: 4GB RAM
- Optimal: 8GB RAM

## Performance Expectations

### First Call (Cold Start)
- Model loading: 2-5 seconds
- Enrichment: 200-500ms

### Subsequent Calls (Warm)
- Enrichment: 50-200ms per claim

## Fallback Behavior

If NLP libraries are not available, the system automatically falls back to deterministic enrichment:

```python
from intelligence.claims.nlp_interpret import NLP_AVAILABLE

if not NLP_AVAILABLE:
    print("NLP not available, using deterministic fallback")
    # System continues to work with dictionary-based enrichment
```

## Troubleshooting

### "No module named 'transformers'"
```bash
pip install transformers torch
```

### "Can't find model 'en_core_web_sm'"
```bash
python -m spacy download en_core_web_sm
```

### Out of Memory (OOM)
- Reduce batch size (already set to 1 for single claims)
- Use smaller models (instructions below)
- Increase system RAM

### Smaller Model Options (if needed)

If you need to reduce memory usage, you can modify `nlp_interpret.py`:

**Replace BART (1.6GB) with DistilBART (500MB):**
```python
_classifier = pipeline(
    "zero-shot-classification",
    model="valhalla/distilbart-mnli-12-1",  # Smaller, faster
    device=-1
)
```

**Use tiny spaCy model (12MB instead of 50MB):**
```bash
python -m spacy download en_core_web_sm
# Replace with:
python -m spacy download en_core_web_sm  # Already smallest
```

## Replit-Specific Instructions

### On Replit Shell:

```bash
# 1. Navigate to project
cd rogrv2-backend

# 2. Install dependencies
pip install -r requirements.txt

# 3. Download spaCy model
python -m spacy download en_core_web_sm

# 4. Test
python3 tests/pipeline_diagnostic_complete.py "COVID vaccines cause autism"
```

### Replit Tier Requirements

- **Free tier (1GB RAM):** ❌ Insufficient
- **Hacker tier (4GB RAM):** ✅ Sufficient
- **Pro tier (8GB RAM):** ✅ Comfortable

## IFCN Compliance Notes

All models are version-locked in requirements.txt for reproducibility:
- `transformers>=4.30.0`
- `torch>=2.0.0`
- `spacy>=3.5.0`

Model versions are logged in enrichment output:
```python
{
    "enrichment_method": "nlp_semantic",
    "confidence": 0.85,
    "models_used": {
        "spacy": "en_core_web_sm-3.5.0",
        "classifier": "facebook/bart-large-mnli",
        "ner": "dslim/bert-base-NER"
    }
}
```

## Next Steps

After setup, the NLP enrichment is automatically used via the hybrid wrapper in `intelligence/claims/interpret.py`.

Test with:
```bash
python3 tests/pipeline_diagnostic_complete.py "COVID vaccines cause autism"
```

You should see enrichment confidence >0.7 and non-empty concept/dimension fields.
