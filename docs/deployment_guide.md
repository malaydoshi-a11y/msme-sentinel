# Deployment Guide

You need three links for the submission: **GitHub repo**, **demo video**, **final product (deployment) link**. I can't create accounts or deploy on your behalf (sign-in/OAuth actions require you), but here's the exact path — should take under 15 minutes total.

## 1. Push to GitHub (public repo)

```bash
cd msme-sentinel
git init
git add .
git commit -m "MSME Sentinel — IDBI Innovate 2026 Track 04 prototype"
```

Then on github.com: create a new **public** repository (e.g. `msme-sentinel`), and:

```bash
git remote add origin https://github.com/<your-username>/msme-sentinel.git
git branch -M main
git push -u origin main
```

That URL is your **GitHub Public Repository** link.

## 2. Deploy the dashboard (pick one — all free, all ~5 minutes)

### Option A — GitHub Pages (simplest, same repo)
1. In your GitHub repo → Settings → Pages.
2. Source: "Deploy from a branch" → branch `main`, folder `/dashboard` (or move dashboard contents to a `docs/` folder if GitHub Pages requires that naming — check the current UI options).
3. Save. GitHub gives you a URL like `https://<username>.github.io/msme-sentinel/`.

### Option B — Netlify (drag-and-drop, no CLI needed)
1. Go to netlify.com → sign in → "Add new site" → "Deploy manually".
2. Drag the entire `dashboard/` folder into the upload zone.
3. Netlify gives you a live URL instantly (e.g. `https://random-name-123.netlify.app`).

### Option C — Vercel
1. Go to vercel.com → sign in → "Add New Project" → import your GitHub repo.
2. Set the root directory to `dashboard/`.
3. Deploy — Vercel gives you a live URL.

Any of these becomes your **Final Product Link**.

## 3. Record and host the demo video

- Record following `docs/demo_video_script.md` (screen + voiceover, ~3 minutes, 1080p).
- Upload to YouTube (as "Unlisted" is fine for most hackathon submissions — check Hack2skill's requirement, some want public/unlisted specifically) or Google Drive with link-sharing enabled.
- That URL is your **Demo Video Link**.

## Before you submit
- Double-check the deployed dashboard link actually loads `data.json`, `app.js`, `style.css`, and `vendor/chart.umd.js` correctly relative to wherever it's hosted — if you moved files into a `docs/` folder for GitHub Pages, update the relative paths in `index.html` if needed.
- Make sure the GitHub repo is **public** (private repos can't be evaluated).
