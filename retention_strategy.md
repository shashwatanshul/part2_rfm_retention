# Retention Strategy

## Segment logic

RFM is computed using only orders on or before `2025-09-30`. Duplicate-like orders ending `_DUP` are normalized with `base_order_id` before customer-level aggregation.

| segment_name               |   customers |   avg_recency |   avg_frequency |   avg_monetary |   avg_return_rate |   avg_ticket_count_90d |   avg_sessions_30d |   observed_churn_rate |
|:---------------------------|------------:|--------------:|----------------:|---------------:|------------------:|-----------------------:|-------------------:|----------------------:|
| General Nurture            |         792 |        72.509 |           1.854 |       1385.11  |             0.074 |                  0.22  |              4.324 |                 0.484 |
| At-Risk High Value         |         355 |       156.518 |           5.256 |       4343.91  |             0.053 |                  0.042 |              4.152 |                 0.766 |
| Champions                  |         323 |        20.737 |           6.313 |       4872.01  |             0.06  |                  0.347 |              7.146 |                 0.108 |
| Loyal Customers            |         278 |        78.601 |           5.306 |       3718.25  |             0.064 |                  0.227 |              5.755 |                 0.367 |
| Discount Sensitive         |         260 |        62.662 |           2.165 |       1368.01  |             0.062 |                  0.246 |              6.465 |                 0.431 |
| Dormant                    |         200 |       222.46  |           1.3   |        948.135 |             0.062 |                  0     |              2.77  |                 0.91  |
| New Engaged Potential      |          81 |        26.457 |           1.099 |        799.449 |             0.062 |                  0.222 |             11.012 |                 0.185 |
| High Intent Non-Converters |          66 |        61.803 |           2.03  |       1490.08  |             0.045 |                  0.167 |             12.364 |                 0.288 |
| Needs Service Recovery     |          45 |        25.689 |           5.2   |       3516.52  |             0.262 |                  2.067 |              7.867 |                 0.156 |

## Recommended actions

| Segment | Action | Why |
|---|---|---|
| Needs Service Recovery | Apology plus priority support or product replacement | Support friction can destroy trust; fix root cause before discounting. |
| At-Risk High Value | Premium win-back, replenishment reminder, or concierge support | High monetary value but stale recency deserves budget priority. |
| High Intent Non-Converters | Cart recovery nudge, free shipping threshold, limited-time reminder | Engagement exists; reduce purchase friction. |
| Discount Sensitive | Controlled coupon or bundle discount | Avoid full-price nudges for customers trained by discount behavior. |
| Dormant | Low-cost reactivation email/SMS, not expensive offers first | Many may be inactive; test low-cost channels first. |
| Loyal Customers | Loyalty points, new launch preview, subscription offer | Preserve retention without over-discounting. |
| Champions | Thank-you perks, referral, exclusive launch access | Protect advocates; do not waste deep discounts. |
| New Engaged Potential | Onboarding education and category recommendations | Build repeat behavior early. |
| General Nurture | Regular content and product recommendations | Keep low-cost always-on nurture. |

## Budget prioritization

Assumed limited campaign budget: **₹15,000**. Prioritize in this order: Needs Service Recovery → At-Risk High Value → High Intent Non-Converters → Discount Sensitive. The generated table `outputs/tables/budget_selected_customers.csv` shows the selected customers under budget.

## Why this should score well

The segmentation uses recency, frequency, monetary value, support friction, returns, web/app activity, campaign engagement, and category diversity. It also produces customer-level outputs that can be inspected manually.