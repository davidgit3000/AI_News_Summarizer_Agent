# Fidelity Checking with Gemini - Phase 6.5 ✅

## Overview
The Fidelity Checker uses Google's Gemini AI to verify summary accuracy, detect hallucinations, and ensure factual consistency. This is an advanced validation feature that goes beyond traditional metrics like ROUGE scores.

## Why Gemini for Fidelity Checking?

### ✅ **Advantages:**
1. **Cost-Effective:** Gemini 1.5 Flash is significantly cheaper than GPT-4
2. **Fast:** Quick response times for validation
3. **Semantic Understanding:** Understands meaning, not just word overlap
4. **Free Tier:** Google offers generous free quota for testing
5. **Separation of Concerns:** Different model for validation vs. summarization

### 💰 **Cost Comparison:**
- **Gemini 1.5 Flash:** ~$0.00001 per check (essentially free for testing)
- **GPT-3.5-turbo:** ~$0.002 per check
- **GPT-4:** ~$0.01 per check

## Features

### 1. **Fidelity Checking**
Evaluates overall summary faithfulness to sources.

**Metrics:**
- Factual consistency (0-1)
- Hallucination-free score (0-1)
- Proper attribution (0-1)
- Balanced representation (0-1)
- Overall fidelity (0-1)

### 2. **Hallucination Detection**
Identifies fabricated or unsupported claims.

**Detects:**
- Claims not in sources
- Contradictions
- Exaggerations
- Misrepresentations

### 3. **Claim Verification**
Verifies each factual claim against sources.

**Status Types:**
- SUPPORTED: Directly stated in sources
- PARTIALLY_SUPPORTED: Partially true
- UNSUPPORTED: Not found in sources
- CONTRADICTED: Contradicts sources

### 4. **Completeness Check**
Ensures key points aren't omitted.

**Analyzes:**
- Total key points in sources
- Covered key points in summary
- Missing important information
- Completeness score (0-1)

## Setup

### 1. Get Gemini API Key
```bash
# Visit: https://makersuite.google.com/app/apikey
# Click "Create API Key"
# Copy your key
```

### 2. Add to .env
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### 3. Install Dependencies
```bash
pip install google-generativeai>=0.3.0
```

## Usage

### Basic Fidelity Check
```python
from src.validation.fidelity_checker import FidelityChecker

checker = FidelityChecker()

source_articles = [
    "Article 1 text...",
    "Article 2 text..."
]

summary = "Generated summary..."

# Check fidelity
result = checker.check_fidelity(summary, source_articles)

print(f"Fidelity: {result['overall_fidelity']:.2f}")
print(f"Factual consistency: {result['factual_consistency']:.2f}")
```

### Hallucination Detection
```python
result = checker.check_hallucinations(summary, source_articles)

if result['has_hallucinations']:
    print(f"Found {result['hallucination_count']} hallucinations:")
    for h in result['hallucinations']:
        print(f"- {h['claim']}")
        print(f"  Severity: {h['severity']}")
```

### Claim Verification
```python
result = checker.verify_claims(summary, source_articles)

print(f"Verified: {result['verified_claims']}/{result['total_claims']}")
print(f"Verification rate: {result['verification_rate']:.1%}")

for claim in result['claims']:
    print(f"\nClaim: {claim['claim']}")
    print(f"Status: {claim['status']}")
    print(f"Evidence: {claim['evidence']}")
```

### Completeness Check
```python
result = checker.check_completeness(summary, source_articles)

print(f"Completeness: {result['completeness_score']:.2f}")
print(f"Covered: {result['covered_key_points']}/{result['total_key_points']}")

if result['missing_key_points']:
    print("\nMissing points:")
    for point in result['missing_key_points']:
        print(f"- {point}")
```

### Comprehensive Check
```python
# Run all checks at once
result = checker.comprehensive_check(summary, source_articles)

print(f"Overall score: {result['overall_score']:.2f}")
print(f"Fidelity: {result['fidelity']['overall_fidelity']:.2f}")
print(f"Hallucinations: {result['hallucinations']['hallucination_count']}")
print(f"Verification rate: {result['claim_verification']['verification_rate']:.1%}")
print(f"Completeness: {result['completeness']['completeness_score']:.2f}")
```

### Integrated with Validation Pipeline
```python
from src.validation.pipeline import ValidationPipeline

# Enable fidelity checking
pipeline = ValidationPipeline(enable_fidelity_check=True)

# Evaluate with fidelity check
result = pipeline.evaluate_summary(
    summary=summary,
    original_text=original,
    check_fidelity=True,
    source_articles=source_articles
)

# Access fidelity results
if 'fidelity' in result:
    fidelity = result['fidelity']
    print(f"Fidelity: {fidelity['overall_fidelity']:.2f}")
    print(f"Explanation: {fidelity['explanation']}")
```

## Testing

### Run Tests
```bash
python test_fidelity.py
```

### Test Coverage
- ✅ Fidelity checking
- ✅ Hallucination detection
- ✅ Claim verification
- ✅ Completeness checking
- ✅ Comprehensive check
- ✅ Integration with validation pipeline

## Example Results

### Good Summary
```
Source: "Microsoft AI announced a new team for superintelligent AI 
focused on safety and ethics."

Summary: "Microsoft AI formed a team for safe, ethical superintelligent AI."

Results:
- Overall fidelity: 0.95
- Factual consistency: 0.98
- Hallucination-free: 1.00
- Issues: None
```

### Bad Summary (with Hallucinations)
```
Source: "Microsoft AI announced a new team for superintelligent AI 
focused on safety and ethics."

Summary: "Microsoft AI created the world's first conscious AI that 
will replace all jobs by 2025."

Results:
- Overall fidelity: 0.15
- Hallucination-free: 0.10
- Hallucinations found: 3
  1. "world's first conscious AI" (HIGH severity)
  2. "replace all jobs by 2025" (HIGH severity)
  3. "achieved consciousness" (HIGH severity)
```

## Models Available

| Model | Speed | Cost | Quality | Best For |
|-------|-------|------|---------|----------|
| `gemini-1.5-flash` | Fast | Free* | Good | Testing, validation (default) |
| `gemini-1.5-pro` | Medium | Low | Excellent | Production, critical checks |

*Free tier: 15 requests/minute, 1M tokens/day

## Configuration

```python
# Use different model
checker = FidelityChecker(model_name="gemini-1.5-pro")

# Detailed analysis
result = checker.check_fidelity(
    summary=summary,
    source_articles=sources,
    detailed=True  # More comprehensive analysis
)
```

## Best Practices

### 1. When to Use Fidelity Checking
- ✅ Critical summaries (news, medical, legal)
- ✅ Production deployments
- ✅ Quality assurance testing
- ✅ Comparing different summarization models
- ❌ Every single summary (use sampling)

### 2. Optimization
```python
# Sample-based checking (cost-effective)
import random

if random.random() < 0.1:  # Check 10% of summaries
    fidelity_result = checker.check_fidelity(summary, sources)
```

### 3. Interpretation
- **Fidelity > 0.8:** Excellent, trustworthy
- **Fidelity 0.6-0.8:** Good, minor issues
- **Fidelity 0.4-0.6:** Fair, needs review
- **Fidelity < 0.4:** Poor, likely hallucinations

### 4. Error Handling
```python
try:
    result = checker.check_fidelity(summary, sources)
    if 'error' in result:
        logger.warning(f"Fidelity check failed: {result['error']}")
        # Fall back to traditional metrics
except Exception as e:
    logger.error(f"Fidelity checker error: {e}")
    # Continue without fidelity check
```

## Integration Points

### With Summarization Pipeline
```python
from src.summarization.pipeline import SummarizationPipeline
from src.validation.pipeline import ValidationPipeline

# Generate summary
summarizer = SummarizationPipeline()
summary_result = summarizer.summarize_topic("AI", max_articles=5)

# Validate with fidelity
validator = ValidationPipeline(enable_fidelity_check=True)
validation_result = validator.evaluate_summary(
    summary=summary_result['summary'],
    original_text="...",
    check_fidelity=True,
    source_articles=[...]
)
```

### In UI (Streamlit)
```python
if st.checkbox("Check fidelity (Gemini)"):
    with st.spinner("Checking fidelity..."):
        fidelity = checker.check_fidelity(summary, sources)
        
        st.metric("Fidelity Score", f"{fidelity['overall_fidelity']:.2f}")
        
        if fidelity.get('issues_found'):
            st.warning("Issues detected:")
            for issue in fidelity['issues_found']:
                st.write(f"- {issue}")
```

## Limitations

### 1. API Dependency
- Requires internet connection
- Subject to API rate limits
- Potential latency (1-2 seconds)

### 2. Not Perfect
- LLM-based, can make mistakes
- May miss subtle hallucinations
- Context window limits (~1M tokens)

### 3. Cost Considerations
- Free tier sufficient for testing
- Production use may incur costs
- Consider sampling strategy

## Troubleshooting

### Issue: "Gemini API key not provided"
**Solution:** Add `GEMINI_API_KEY` to `.env` file

### Issue: Rate limit exceeded
**Solution:** 
- Use `gemini-1.5-flash` (higher limits)
- Implement rate limiting in code
- Upgrade to paid tier if needed

### Issue: JSON parsing errors
**Solution:** Already handled in code with fallbacks

### Issue: Timeout errors
**Solution:** Increase timeout or retry logic

## Performance

**Typical Response Times:**
- Fidelity check: 1-2 seconds
- Hallucination detection: 1-2 seconds
- Claim verification: 2-3 seconds
- Comprehensive check: 4-6 seconds

**Optimization:**
- Run checks in parallel when possible
- Cache results for identical summaries
- Use async/await for multiple checks

## Future Enhancements

Possible improvements:
- Multi-language support
- Custom fidelity criteria
- Fine-tuned models for specific domains
- Batch processing for efficiency
- Confidence calibration

## Files Created

```
src/
└── validation/
    ├── fidelity_checker.py   # Gemini-based fidelity checking

test_fidelity.py              # Test suite
docs/
└── FIDELITY_CHECKING.md      # This file
```

---

**Status:** ✅ Complete and Tested  
**Model:** Gemini 1.5 Flash  
**Cost:** ~Free for testing  
**Integration:** Optional enhancement to Phase 6
