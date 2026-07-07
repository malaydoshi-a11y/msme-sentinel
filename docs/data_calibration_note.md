# Data Calibration Note — Sourcing the Synthetic Panel's Default Rate

We were asked directly (and it's a fair challenge): if the alternative-data
signals (GST, UPI, EPFO, utility) are synthetic because no public dataset
pairs them with real Indian MSME default labels, how do we know the
*overall stress rate* in our synthetic panel isn't just picked to look good?

We don't leave that to trust — we anchored it to real, published numbers.

## What's actually published

- RBI/Finance Ministry data (via PIB release, December 2025): the
  **MSME-sector Gross NPA ratio fell from 9.87% in March 2021 to 3.27% in
  September 2025.**
- A separate Finance Ministry release (Business Standard, March 2025) states
  the MSME-sector Gross NPA ratio of Scheduled Commercial Banks **fell from
  11% in FY2020 to 4% in FY2024.**
- For context, the *overall* (all-sector) SCB Gross NPA ratio was a
  historic low of 2.15% as of September 2025 — MSME has consistently run
  higher than the system-wide average across this entire period.

## What we did with it

Our synthetic 24-month panel produces an **eventual default rate of ~8.9%**
across 6,000 simulated MSME borrowers. That number was not tuned to hit a
target — it falls out of the underlying causal generation logic (vintage
risk, business-type risk, and idiosyncratic drift). Checked against the
real range above, it sits close to the **pandemic-era stressed peak
(9.87%, March 2021)**, not the current unusually low environment (3.27%,
September 2025).

We think that's the right calibration choice, and we're stating why rather
than hoping nobody asks: an early-warning system is most valuable to
demonstrate — and most valuable to a bank evaluating whether to adopt one —
under portfolio conditions that actually show meaningful Red/Amber activity.
Calibrating to today's historically clean NPA environment would make for a
demo where almost every account is Green, which proves nothing useful about
whether the system can distinguish and flag deterioration in a real
stressed cycle.

## Sources

- PIB Press Release, "Gross NPAs in MSME, Retail Loans Decline Sharply;
  PSBs Strengthen Financial Health" (December 2025) — MSME GNPA 9.87%
  (Mar 2021) → 3.27% (Sep 2025).
- Business Standard / Finance Ministry release (March 2025) — MSME GNPA
  11% (FY2020) → 4% (FY2024).
- PIB Press Release — overall SCB domestic GNPA ratio at 2.15% (Sep 2025).
