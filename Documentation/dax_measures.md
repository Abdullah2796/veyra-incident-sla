# DAX measure catalogue

All measures live in the `_Measures` table and are grouped into display folders. Generated from the TMDL source.

## Volume

### As Of

Latest incident timestamp in the export; anchors ageing.

```dax
CALCULATE ( MAX ( FactIncident[Opened At] ), REMOVEFILTERS () )
```

Format: `d mmm yyyy hh:nn`

### Incidents

```dax
COUNTROWS ( FactIncident )
```

Format: `#,0`

### P1 Incidents

```dax
CALCULATE ( [Incidents], FactIncident[Priority] = "P1" )
```

Format: `#,0`

### Auto-detected %

```dax
DIVIDE ( CALCULATE ( [Incidents], FactIncident[Channel] = "Auto-monitoring" ), [Incidents] )
```

Format: `0.0%`

### Incidents per 1k Devices

Incident rate normalised by installed devices.

```dax
DIVIDE ( [Incidents], SUM ( DimSite[Devices] ) ) * 1000
```

Format: `#,0.0`

### Incidents MoM %

```dax
VAR Prev = CALCULATE ( [Incidents], DATEADD ( DimDate[Date], -1, MONTH ) )
RETURN DIVIDE ( [Incidents] - Prev, Prev )
```

Format: `+0.0%;-0.0%;0.0%`

### Release-linked Incidents

```dax
CALCULATE ( [Incidents], FactIncident[Release] <> "" )
```

Format: `#,0`

## SLA

### Resolved Incidents

```dax
CALCULATE ( [Incidents], NOT ISBLANK ( FactIncident[Resolution Met] ) )
```

Format: `#,0`

### Response SLA %

```dax
DIVIDE ( CALCULATE ( [Incidents], FactIncident[Response Met] = TRUE () ), CALCULATE ( [Incidents], NOT ISBLANK ( FactIncident[Response Met] ) ) )
```

Format: `0.0%`

### Resolution SLA %

Share of resolved incidents fixed within the resolution target for their priority.

```dax
DIVIDE ( CALCULATE ( [Incidents], FactIncident[Resolution Met] = TRUE () ), [Resolved Incidents] )
```

Format: `0.0%`

### SLA Breaches

```dax
CALCULATE ( [Incidents], FactIncident[Resolution Met] = FALSE () )
```

Format: `#,0`

### Median Response (min)

```dax
MEDIAN ( FactIncident[Response Minutes] )
```

Format: `#,0.0`

### Median Resolution (hrs)

```dax
MEDIAN ( FactIncident[Resolution Hours] )
```

Format: `#,0.0`

### P90 Resolution (hrs)

90th percentile: the slowest 10% of incidents take longer than this.

```dax
PERCENTILEX.INC ( FILTER ( FactIncident, NOT ISBLANK ( FactIncident[Resolution Hours] ) ), FactIncident[Resolution Hours], 0.9 )
```

Format: `#,0.0`

### Reopen Rate %

```dax
DIVIDE ( CALCULATE ( [Incidents], FactIncident[Reopened] = TRUE () ), [Resolved Incidents] )
```

Format: `0.0%`

## Backlog

### Open Incidents

```dax
CALCULATE ( [Incidents], FactIncident[Is Open] = TRUE () )
```

Format: `#,0`

### Aged Backlog

Open incidents already older than their resolution target.

```dax
CALCULATE ( [Incidents], FactIncident[Is Aged] = TRUE () )
```

Format: `#,0`

### Aged Backlog %

```dax
DIVIDE ( [Aged Backlog], [Open Incidents] )
```

Format: `0.0%`

### Avg Age Open (days)

```dax
DIVIDE ( CALCULATE ( AVERAGE ( FactIncident[Age Hours] ), FactIncident[Is Open] = TRUE () ), 24 )
```

Format: `#,0.0`

## Customer

### Survey Responses

```dax
CALCULATE ( COUNTROWS ( FactCSAT ), FactCSAT[Has Incident] = TRUE () )
```

Format: `#,0`

### CSAT

Average survey score, 1–5.

```dax
CALCULATE ( AVERAGE ( FactCSAT[Score] ), FactCSAT[Has Incident] = TRUE () )
```

Format: `0.00`

### Satisfied %

```dax
DIVIDE ( CALCULATE ( [Survey Responses], FactCSAT[Score] >= 4 ), [Survey Responses] )
```

Format: `0.0%`

### Survey Response Rate

```dax
DIVIDE ( [Survey Responses], [Resolved Incidents] )
```

Format: `0.0%`

## Scorecard

### KPI Actual

```dax
SWITCH (
    SELECTEDVALUE ( 'KPI Targets'[KPI Key] ),
    "RES_SLA", [Resolution SLA %],
    "RESP_SLA", [Response SLA %],
    "REOPEN", [Reopen Rate %],
    "CSAT", [CSAT],
    "AGED", [Aged Backlog %]
)
```

Format: `0.000`

### KPI Target

```dax
SELECTEDVALUE ( 'KPI Targets'[Target] )
```

Format: `0.000`

### KPI Actual (display)

```dax
VAR v = [KPI Actual]
RETURN IF ( ISBLANK ( v ), BLANK (), IF ( SELECTEDVALUE ( 'KPI Targets'[KPI Key] ) = "CSAT", FORMAT ( v, "0.00" ), FORMAT ( v, "0.0%" ) ) )
```

Format: `General`

### KPI Target (display)

```dax
VAR v = [KPI Target]
RETURN IF ( ISBLANK ( v ), BLANK (), IF ( SELECTEDVALUE ( 'KPI Targets'[KPI Key] ) = "CSAT", FORMAT ( v, "0.00" ), FORMAT ( v, "0.0%" ) ) )
```

Format: `General`

### KPI Status

```dax
VAR Actual = [KPI Actual]
VAR Target = [KPI Target]
VAR HigherIsBetter = SELECTEDVALUE ( 'KPI Targets'[Direction] ) = "Higher is better"
VAR OnTarget = IF ( HigherIsBetter, Actual >= Target, Actual <= Target )
VAR NearTarget = IF ( HigherIsBetter, Actual >= Target * 0.95, Actual <= Target * 1.10 )
RETURN IF ( ISBLANK ( Actual ), BLANK (), IF ( OnTarget, "● On target", IF ( NearTarget, "● Watch", "● Off target" ) ) )
```

Format: `General`

### KPI Score

```dax
VAR Actual = [KPI Actual]
VAR Target = [KPI Target]
VAR Ratio = IF ( SELECTEDVALUE ( 'KPI Targets'[Direction] ) = "Higher is better", DIVIDE ( Actual, Target ), DIVIDE ( Target, Actual ) )
RETURN MIN ( 1, Ratio ) * SELECTEDVALUE ( 'KPI Targets'[Weight] )
```

Format: `0.0%`

### Overall Score

```dax
SUMX ( VALUES ( 'KPI Targets'[KPI Key] ), [KPI Score] )
```

Format: `0.0%`

## Labels

### Report Subtitle

```dax
"Synthetic data · status as of " & FORMAT ( [As Of], "d mmm yyyy" )
```

Format: `General`

### SLA Headline

```dax
VAR Weakest = TOPN ( 1, FILTER ( VALUES ( DimGroup[Group] ), NOT ISBLANK ( [Resolution SLA %] ) ), [Resolution SLA %], ASC )
VAR WName = MAXX ( Weakest, DimGroup[Group] )
VAR WRate = MAXX ( Weakest, [Resolution SLA %] )
RETURN "Resolution SLA " & FORMAT ( [Resolution SLA %], "0.0%" ) & " against a 90% target  ·  weakest resolver: " & WName & " (" & FORMAT ( WRate, "0.0%" ) & ")"
```

Format: `General`
