# Quick Setup: Gemini Fidelity Checking

## Get Your Free Gemini API Key

### Step 1: Visit Google AI Studio
Go to: **https://makersuite.google.com/app/apikey**

### Step 2: Create API Key
1. Click **"Create API Key"**
2. Select a Google Cloud project (or create new one)
3. Copy your API key

### Step 3: Add to .env
Open your `.env` file and add:
```bash
GEMINI_API_KEY=your_gemini_api_key_here
```

### Step 4: Install Package
```bash
pip install google-generativeai>=0.3.0
```

### Step 5: Test It
```bash
python test_fidelity.py
```

## Free Tier Limits

Gemini 1.5 Flash (default):
- **15 requests per minute**
- **1 million tokens per day**
- **1,500 requests per day**

This is more than enough for testing and development!

## Quick Test

```python
from src.validation.fidelity_checker import FidelityChecker

checker = FidelityChecker()

source = "AI is transforming technology through machine learning."
summary = "AI transforms tech via ML."

result = checker.check_fidelity(summary, [source])
print(f"Fidelity: {result['overall_fidelity']:.2f}")
```

## Troubleshooting

**Error: "Gemini API key not provided"**
- Make sure you added `GEMINI_API_KEY` to `.env`
- Restart your terminal/IDE after adding it

**Error: "API key not valid"**
- Check you copied the full key
- Make sure there are no extra spaces
- Verify the key is active in Google AI Studio

**Rate limit errors:**
- You're making too many requests
- Wait a minute and try again
- Free tier: 15 requests/minute

## Why Use Gemini?

✅ **Free:** Generous free tier  
✅ **Fast:** Quick responses  
✅ **Accurate:** Good at fact-checking  
✅ **Separate:** Different model from OpenAI (better validation)  
✅ **Cost-effective:** ~100x cheaper than GPT-4  

## Next Steps

Once setup:
1. Run `python test_fidelity.py` to verify
2. Use in validation pipeline (see `docs/FIDELITY_CHECKING.md`)
3. Integrate with your summarization workflow

---

**Need help?** Check `docs/FIDELITY_CHECKING.md` for detailed documentation.
