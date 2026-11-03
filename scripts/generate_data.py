"""Synthetic data generator for the Veyra Safety Services incident & SLA portfolio project.
All companies, places, people and identifiers are fictional. Seeded for reproducibility."""
import numpy as np, pandas as pd, json, os, datetime as dt
rng = np.random.default_rng(2611)
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'Data')
os.makedirs(OUT, exist_ok=True)
START, ASOF = pd.Timestamp('2026-01-01'), pd.Timestamp('2026-10-31 18:00')

# ---- sites (Excel) ----
MUNI = ['Ravenstad', 'Lindholm', 'Westerburg', 'Ekeren', 'Sloterveen', 'Hoogmade']
SEG = ['Residential', 'Commercial', 'Public building']
sites = pd.DataFrame({'Site ID': [f"S{i:05d}" for i in range(1, 2401)],
                      'Municipality': rng.choice(MUNI, 2400, p=[.24, .2, .18, .14, .13, .11]),
                      'Segment': rng.choice(SEG, 2400, p=[.7, .2, .1])})
sites['Devices'] = np.where(sites.Segment == 'Residential', rng.integers(2, 8, 2400), rng.integers(10, 60, 2400))
sites['Contract Start'] = [dt.date(2024, 1, 1) + dt.timedelta(days=int(d)) for d in rng.integers(0, 600, 2400)]

# ---- resolver groups (JSON API) ----
GROUPS = [('NOC-L1', 'NOC Level 1', 'Internal', None, 0.8), ('NOC-L2', 'NOC Level 2', 'Internal', None, 1.0),
          ('PLAT', 'Platform Engineering', 'Internal', None, 1.1),
          ('FV-ARD', 'Field – Ardent Service', 'Vendor', 'Ardent Service BV', 1.0),
          ('FV-OST', 'Field – Ostra Field Services', 'Vendor', 'Ostra Field Services', 1.7),
          ('FV-PEL', 'Field – Pelikan Techniek', 'Vendor', 'Pelikan Techniek', 1.15)]
VENDOR_MUNI = {'Ravenstad': 'FV-ARD', 'Lindholm': 'FV-ARD', 'Westerburg': 'FV-OST', 'Ekeren': 'FV-OST', 'Sloterveen': 'FV-PEL', 'Hoogmade': 'FV-PEL'}

# ---- release calendar (CSV) ----
rel = pd.DataFrame([('2.2.0', '2026-02-10', 'Minor'), ('2.3.0', '2026-05-05', 'Minor'), ('2.3.1', '2026-06-16', 'Patch'),
                    ('2.4.0', '2026-09-08', 'Major'), ('2.4.1', '2026-10-13', 'Patch')], columns=['Release', 'Release Date', 'Type'])

# ---- incidents ----
CATS = {  # weight, priority probs P1..P4, field visit prob, base resolution hrs, channel probs [Auto, Phone, Portal, Email]
 'Device offline':       (.26, [.02, .18, .55, .25], .35, 6,  [.9, .04, .04, .02]),
 'False alarm':          (.18, [.10, .40, .40, .10], .10, 2,  [.6, .3, .07, .03]),
 'Low battery':          (.16, [0, .05, .45, .50], .80, 20, [.95, .02, .02, .01]),
 'Connectivity':         (.12, [.03, .25, .52, .20], .25, 8,  [.8, .1, .07, .03]),
 'Panel fault':          (.12, [.08, .42, .40, .10], .60, 10, [.7, .2, .07, .03]),
 'Installation defect':  (.06, [.02, .20, .48, .30], .90, 30, [.1, .4, .3, .2]),
 'Customer request':     (.10, [0, .02, .38, .60], .05, 30, [0, .45, .35, .20])}
RESP = {1: 15, 2: 30, 3: 120, 4: 480}; RES = {1: 4, 2: 8, 3: 24, 4: 72}
days = pd.date_range(START, ASOF.normalize())
rows = []
iid = 100000
for d in days:
    base = 40 * (1.12 if d.month in (1, 2, 12) else 1.0) * (0.85 if d.weekday() >= 5 else 1.0)
    surge = 1.0
    if pd.Timestamp('2026-09-08') <= d <= pd.Timestamp('2026-10-14'): surge = 1.35
    n = rng.poisson(base * surge)
    for _ in range(n):
        cw = np.array([v[0] for v in CATS.values()])
        if surge > 1: cw = cw * np.array([1, 1, 1, 1, 3.2, 1, 1])
        cat = list(CATS)[rng.choice(7, p=cw / cw.sum())]
        w, pp, fprob, rbase, ch = CATS[cat]
        pr = int(rng.choice(4, p=pp)) + 1
        site = sites.iloc[int(rng.integers(len(sites)))]
        opened = d + pd.Timedelta(minutes=int(rng.integers(0, 1440)))
        weekend = opened.weekday() >= 5 or opened.hour < 7 or opened.hour >= 20
        resp = rng.lognormal(np.log(RESP[pr] * 0.45), 0.7) * (1.4 if weekend else 1)
        field = rng.random() < fprob
        grp = VENDOR_MUNI[site.Municipality] if field else rng.choice(['NOC-L1', 'NOC-L2', 'PLAT'], p=[.62, .3, .08])
        mult = dict((g[0], g[4]) for g in GROUPS)[grp]
        prf = {1: .25, 2: .45, 3: 1, 4: 1.6}[pr]
        resol = rng.lognormal(np.log(0.55 * rbase * prf * mult * (1.25 if weekend else 1) * (1.7 if surge > 1 else 1)), 0.7)
        resolved = opened + pd.Timedelta(minutes=resp) + pd.Timedelta(hours=resol)
        reopened = rng.random() < (0.11 if cat == 'False alarm' else 0.035)
        if reopened: resolved += pd.Timedelta(hours=rng.lognormal(np.log(12), .6))
        stuck = (ASOF - opened).days < 45 and rng.random() < (0.06 if field else 0.015)
        state = 'Open' if stuck else 'Closed' if resolved <= ASOF - pd.Timedelta(hours=72) else ('Resolved' if resolved <= ASOF else 'Open')
        iid += 1
        rows.append({'number': f"INC{iid}", 'opened_at': opened, 'acknowledged_at': opened + pd.Timedelta(minutes=resp),
                     'resolved_at': resolved if state != 'Open' else pd.NaT, 'state': state,
                     'priority': {1: '1 - Critical', 2: '2 - High', 3: '3 - Moderate', 4: '4 - Low'}[pr],
                     'category': cat, 'contact_type': ['Auto-monitoring', 'Phone', 'Portal', 'Email'][rng.choice(4, p=ch)],
                     'assignment_group': grp, 'site_id': site['Site ID'], 'municipality': site.Municipality,
                     'reopen_count': int(reopened), 'caused_by_release': '2.4.0' if (surge > 1 and cat == 'Panel fault' and rng.random() < .55) else ''})
inc = pd.DataFrame(rows)
# --- deliberate data-quality issues ---
dup = inc.sample(frac=0.01, random_state=1); inc = pd.concat([inc, dup])
i = inc.sample(frac=0.03, random_state=2).index.unique(); inc.loc[i, 'priority'] = inc.loc[i, 'priority'].map({'1 - Critical': 'P1', '2 - High': 'High', '3 - Moderate': 'P3', '4 - Low': 'low'})
i = inc[inc.state != 'Open'].sample(n=60, random_state=3).index.unique(); inc.loc[i, 'resolved_at'] = inc.loc[i, 'opened_at'] - pd.Timedelta(hours=2)
i = inc.sample(frac=0.04, random_state=4).index.unique(); inc.loc[i, 'municipality'] = inc.loc[i, 'municipality'].str.upper()
i = inc[inc.state == 'Open'].sample(frac=0.08, random_state=5).index.unique(); inc.loc[i, 'assignment_group'] = ''
inc = inc.sort_values('opened_at')
fmt = lambda s: s.dt.strftime('%d/%m/%Y %H:%M').fillna('')
for c in ['opened_at', 'acknowledged_at', 'resolved_at']: inc[c] = fmt(inc[c])
inc.to_csv(f"{OUT}/itsm_incident_export.csv", index=False)

# ---- CSAT survey (CSV) ----
res = inc[inc.state != 'Open'].drop_duplicates('number')
s = res.sample(frac=0.22, random_state=6).copy()
o = pd.to_datetime(s.opened_at, format='%d/%m/%Y %H:%M'); r = pd.to_datetime(s.resolved_at, format='%d/%m/%Y %H:%M')
hrs = ((r - o).dt.total_seconds() / 3600).clip(lower=0)
score = 4.7 - 0.9 * np.log1p(hrs / 24) - 0.6 * s.reopen_count + rng.normal(0, .6, len(s))
s['score'] = np.clip(np.round(score), 1, 5).astype(int)
csat = s[['number']].rename(columns={'number': 'incident_number'})
csat['response_date'] = (r + pd.to_timedelta(rng.integers(1, 72, len(s)), 'h')).dt.strftime('%Y-%m-%d').values
csat['score'] = s.score.values
csat['comment_theme'] = np.where(csat.score >= 4, rng.choice(['Fast response', 'Friendly engineer', 'Clear updates'], len(s)),
                                 rng.choice(['Took too long', 'Had to chase', 'Issue came back', 'Engineer no-show'], len(s)))
orph = csat.sample(n=40, random_state=7).copy(); orph['incident_number'] = [f"INC9{i:05d}" for i in range(40)]
pd.concat([csat, orph]).to_csv(f"{OUT}/csat_survey_responses.csv", index=False)

# ---- write remaining sources ----
with pd.ExcelWriter(f"{OUT}/customer_sites.xlsx") as xw: sites.to_excel(xw, sheet_name='Sites', index=False)
with open(f"{OUT}/resolver_groups_api.json", 'w') as f:
    json.dump({'source': 'Veyra workforce API (synthetic)', 'groups': [{'code': g[0], 'name': g[1], 'type': g[2], 'vendor': g[3]} for g in GROUPS]}, f, indent=1)
sla = pd.DataFrame({'Priority': ['P1', 'P2', 'P3', 'P4'], 'Priority Name': ['Critical', 'High', 'Moderate', 'Low'],
                    'Response Target (min)': [15, 30, 120, 480], 'Resolution Target (hrs)': [4, 8, 24, 72]})
kpi = pd.DataFrame([['Resolution SLA met', .90, 'Higher is better', .30, 'RES_SLA'], ['Response SLA met', .95, 'Higher is better', .20, 'RESP_SLA'],
                    ['Reopen rate', .04, 'Lower is better', .15, 'REOPEN'], ['CSAT (avg score)', 4.2, 'Higher is better', .20, 'CSAT'],
                    ['Backlog older than SLA', .10, 'Lower is better', .15, 'AGED']], columns=['KPI', 'Target', 'Direction', 'Weight', 'KPI Key'])
kpi['Sort'] = range(1, 6)
with pd.ExcelWriter(f"{OUT}/sla_policy_and_targets.xlsx") as xw:
    sla.to_excel(xw, sheet_name='SLA Policy', index=False); kpi.to_excel(xw, sheet_name='KPI Targets', index=False)
rel.to_csv(f"{OUT}/release_calendar.csv", index=False)

# ---- quick truth check ----
c = inc.drop_duplicates('number').copy()
c['p'] = c.priority.str.extract(r'(\d)')[0].fillna(c.priority.map({'High': '2', 'low': '4'})).astype(int)
o = pd.to_datetime(c.opened_at, format='%d/%m/%Y %H:%M'); r = pd.to_datetime(c.resolved_at, format='%d/%m/%Y %H:%M', errors='coerce')
a = pd.to_datetime(c.acknowledged_at, format='%d/%m/%Y %H:%M')
c['rh'] = (r - o).dt.total_seconds() / 3600; ok = c.rh >= 0
c['met'] = c.rh <= c.p.map(RES)
print('incidents', len(c), 'open', (c.state == 'Open').sum())
print('res SLA', round(c[ok].met.mean(), 3), 'resp SLA', round((((a - o).dt.total_seconds() / 60) <= c.p.map(RESP)).mean(), 3), 'reopen', round(c.reopen_count.mean(), 3), 'csat', round(csat.score.mean(), 2))
print(c[ok].groupby('assignment_group').met.mean().round(3).to_dict())
print(c[ok].assign(m=o.dt.month).groupby('m').met.mean().round(3).to_dict())
