# Results

## Summary with Cost Metrics

| Run | Mode | Dev Accuracy | Test Accuracy | Avg Tokens | Tokens/Correct | Cost/100 Correct |
|-----|------|--------------|---------------|------------|----------------|------------------|
| 20250812-135910_self_refine | self_refine | 1.0 | 1.0 | 19.2 | 19.2 | $0.0038 |
| 20250812-104350_gepa | gepa | nan | 1.0 | nan | 92.0 | $0.0184 |
| 20250812-131955_baseline | baseline | 1.0 | 1.0 | 96.4 | 96.4 | $0.0193 |
| 20250812-135618_baseline | baseline | 0.4 | 0.2 | 99.0 | 247.5 | $0.0495 |
| 20250812-101433_self_refine | self_refine | 1.0 | 1.0 | 15.8 | 15.8 | $0.0032 |
| 20250812-143528_distill_from_self_refine | distill_from_self_refine | 1.0 | 1.0 | 606.8 | 606.8 | $0.1214 |
| 20250812-092419_baseline | baseline | 0.6 | 0.4 | 7.0 | 11.666666666666668 | $0.0023 |
| 20250812-135811_baseline | baseline | 0.4 | 0.2 | 105.4 | 263.5 | $0.0527 |
| 20250812-092140_baseline | baseline | 0.6 | 0.4 | 7.0 | 11.666666666666668 | $0.0023 |
| 20250812-135735_baseline | baseline | 0.2 | 0.2 | 94.6 | 472.99999999999994 | $0.0946 |
| 20250812-100502_baseline | baseline | 0.6 | 0.4 | 7.0 | 11.666666666666668 | $0.0023 |
| 20250812-143436_baseline | baseline | 0.0 | 0.2 | 86.2 | ∞ | ∞ |
| 20250812-131851_baseline | baseline | 1.0 | 1.0 | 98.4 | 98.4 | $0.0197 |
| 20250812-101351_baseline | baseline | 1.0 | 1.0 | 94.0 | 94.0 | $0.0188 |
| 20250812-092857_self_refine | self_refine | 0.0 | 0.0 | 7.0 | ∞ | ∞ |
| 20250812-104258_self_refine | self_refine | 1.0 | 1.0 | 16.2 | 16.2 | $0.0032 |
| 20250812-100505_self_refine | self_refine | 0.0 | 0.0 | 7.0 | ∞ | ∞ |
| 20250812-132311_baseline | baseline | 1.0 | 1.0 | 95.6 | 95.6 | $0.0191 |
| 20250812-095043_self_refine | self_refine | 0.0 | 0.0 | 7.0 | ∞ | ∞ |
| 20250812-135704_baseline | baseline | 0.4 | 0.0 | 95.8 | 239.49999999999997 | $0.0479 |
| 20250812-141852_self_refine | self_refine | 1.0 | 1.0 | 519.4 | 519.4 | $0.1039 |
| 20250812-133616_baseline | baseline | 0.2 | 0.2 | 2.0 | 10.0 | $0.0020 |
| 20250812-135937_gepa | gepa | nan | 0.4 | nan | 253.99999999999997 | $0.0508 |
| 20250812-131744_baseline | baseline | 1.0 | 1.0 | 97.8 | 97.8 | $0.0196 |
| 20250812-134330_baseline | baseline | 1.0 | 1.0 | 91.0 | 91.0 | $0.0182 |
| 20250812-092150_self_refine | self_refine | 0.0 | 0.0 | 7.0 | ∞ | ∞ |
| 20250812-141954_gepa | gepa | nan | 0.0 | nan | ∞ | ∞ |
| 20250812-134418_baseline | baseline | 1.0 | 1.0 | 92.2 | 92.2 | $0.0184 |
| 20250812-135851_baseline | baseline | 0.2 | 0.2 | 97.2 | 486.0 | $0.0972 |
| 20250812-141930_baseline | baseline | 0.2 | 0.0 | 96.8 | 483.99999999999994 | $0.0968 |
| 20250812-104226_baseline | baseline | 1.0 | 1.0 | 98.4 | 98.4 | $0.0197 |
| 20250812-133537_baseline | baseline | 1.0 | 1.0 | 102.2 | 102.2 | $0.0204 |

## Key Insights

- **Tokens per Correct**: Lower is better - combines cost and accuracy
- **Cost per 100 Correct**: Dollar cost for 100 correct answers
- **Self-Refine vs GEPA**: Compare efficiency at similar accuracy levels

## GEPA Variant Pareto

See `pareto.png` for the scatter plot.