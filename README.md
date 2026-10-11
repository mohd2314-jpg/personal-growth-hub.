# Personal Growth Hub

A lightweight installable web app (PWA) for daily reading. A scheduled GitHub Actions workflow calls Hugging Face Inference Providers and writes a daily JSON digest to `docs/daily.json`. The phone opens the static page; it does not need Termux running in the background.

## Included
- Minimal dark PWA reading interface
- Psychology / charisma lesson
- Daily quote (model-generated; verify attribution before sharing)
- Evergreen engineering/decision-making briefing (not live news)
- One GATE ECE PYQ explanation **only when you add a verified question with an official source URL**
- Weekly review on Sundays
- Manual workflow run button

## Honest limitations
- GitHub Actions schedules can be delayed or disabled after long periods of repository inactivity. This is not a guaranteed alarm clock.
- Hugging Face inference is metered. Free credits/availability vary by account, model and provider; check the current pricing page.
- The model is not a source of truth. The included starter does not invent official GATE PYQs. Add questions from official papers and answer keys to `data/pyqs.json`.
- The daily briefing is evergreen, not live news. Adding a trustworthy RSS/news source is a separate enhancement.
- The current version does not send push notifications. Install the PWA and use its single home-screen icon. Android notifications require a separate push service or Android-side automation.

## 1. Create the GitHub repository
1. Create a new repository on GitHub, e.g. `personal-growth-hub`.
2. Upload all files in this folder to the repository root.
3. In repository **Settings → Secrets and variables → Actions → New repository secret**, add:
   - Name: `HF_TOKEN`
   - Value: your Hugging Face token with inference permissions.
4. In **Settings → Pages**, choose **Deploy from a branch**, select your default branch and `/docs` folder, then save.
5. Wait for GitHub Pages to publish. Open the Pages URL once on your phone.
6. In Chrome on Android, use **⋮ → Add to Home screen** (or **Install app**, if shown).

## 2. Configure the Hugging Face model
The workflow uses `Qwen/Qwen3.5-9B` as a starting default, but model/provider availability can change. Check https://huggingface.co/inference/models and change `HF_MODEL` in `.github/workflows/daily.yml` to a currently supported chat-completion model if needed.

Create a token at https://huggingface.co/settings/tokens. Never put the token in `docs/`, HTML, JavaScript, or any public file.

## 3. Add verified GATE PYQs
Edit `data/pyqs.json`. Each record must include the exact question, answer, year/paper, official source URL, and a short verified solution or answer key. Keep source links to official GATE/IIT organizing-institute material where possible.

Example schema (replace placeholders with a real verified question; this example is deliberately not a real question):
```json
[
  {
    "id": "gate-ec-2024-example",
    "year": 2024,
    "paper": "EC",
    "topic": "Signals and Systems",
    "question": "REPLACE WITH EXACT QUESTION FROM OFFICIAL PAPER",
    "options": {"A": "option A", "B": "option B", "C": "option C", "D": "option D"},
    "answer": "B",
    "official_source_url": "https://REPLACE-WITH-OFFICIAL-PDF-OR-ANSWER-KEY-URL",
    "verified_solution": "REPLACE WITH SOLUTION CHECKED AGAINST THE OFFICIAL ANSWER KEY"
  }
]
```
The generator refuses to label a question as a verified PYQ if the source URL is missing or still a placeholder.

## 4. Run it
- GitHub → **Actions** → **Daily Growth Digest** → **Run workflow**.
- Check the run log. On success, it commits `docs/daily.json`.
- Open the app icon and tap **Refresh digest** to fetch the latest version.

## 5. Schedule
The included cron is `17 1 * * *` (01:17 UTC = 06:47 IST). GitHub may delay scheduled jobs; choose an off-the-hour minute to reduce congestion. Sundays include a weekly review section.

## 6. Cost control
- One generation request per day; no continuous calls.
- Use a smaller, low-cost model that is currently available to your account.
- Check current per-token rates and free credits before relying on a provider.
- Add a spending limit where supported; never commit tokens.
- If inference fails, the previous digest remains available.

## 7. Termux is optional
Termux is useful for editing files or manually testing Python. It is not required for daily operation. Do not keep wake locks or an always-running loop just to refresh this page.
