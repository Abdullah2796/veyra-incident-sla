# Data dictionary

Columns as they appear in the semantic model. Hidden columns are keys or helper columns not meant for report authors.

## Data Quality Log

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Check | string |  |  | sorted by Sort |
| Source | string |  |  |  |
| Records Affected | int64 |  |  |  |
| Action Taken | string |  |  |  |
| Sort | int64 |  | yes |  |

## DimDate

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Date | dateTime | d mmm yyyy |  |  |
| Year | int64 |  |  |  |
| Month No | int64 |  | yes |  |
| Month | string |  |  | sorted by Month No |
| Month Start | dateTime | mmm yyyy |  |  |
| Week Start | dateTime | d mmm |  |  |
| Weekday No | int64 |  | yes |  |
| Weekday | string |  |  | sorted by Weekday No |

## DimGroup

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Group Code | string |  |  |  |
| Group | string |  |  |  |
| Group Type | string |  |  |  |
| Vendor | string |  |  |  |

## DimPriority

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Priority | string |  |  |  |
| Priority Name | string |  |  |  |
| Response Target (min) | int64 |  |  |  |
| Resolution Target (hrs) | int64 |  |  |  |

## DimRelease

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Release | string |  |  |  |
| Release Date | dateTime | d mmm yyyy |  |  |
| Type | string |  |  |  |

## DimSite

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Site ID | string |  |  |  |
| Municipality | string |  |  |  |
| Segment | string |  |  |  |
| Devices | int64 |  |  |  |
| Contract Start | dateTime | d mmm yyyy |  |  |

## FactCSAT

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Incident Number | string |  | yes |  |
| Response Date | dateTime | d mmm yyyy |  |  |
| Score | int64 |  |  |  |
| Comment Theme | string |  |  |  |
| Has Incident | boolean |  | yes |  |

## FactIncident

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Number | string |  |  |  |
| Opened At | dateTime | d mmm yyyy hh:nn |  |  |
| Opened Date | dateTime | d mmm yyyy | yes |  |
| Priority | string |  | yes |  |
| Category | string |  |  |  |
| Channel | string |  |  |  |
| Group Code | string |  | yes |  |
| Site ID | string |  | yes |  |
| State | string |  |  |  |
| Shift | string |  |  |  |
| Release | string |  |  |  |
| Response Minutes | double | #,0.0 |  |  |
| Resolution Hours | double | #,0.0 |  |  |
| Age Hours | double | #,0 |  |  |
| Response Met | boolean |  |  |  |
| Resolution Met | boolean |  |  |  |
| Is Open | boolean |  |  |  |
| Is Aged | boolean |  |  |  |
| Reopened | boolean |  |  |  |
| Age Bucket | string |  |  | sorted by Age Bucket Sort |
| Age Bucket Sort | int64 |  | yes |  |
| Resolution Band | string |  |  | sorted by Resolution Band Sort |
| Resolution Band Sort | int64 |  | yes |  |

## KPI Targets

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| KPI | string |  |  | sorted by Sort |
| Target | double |  |  |  |
| Direction | string |  |  |  |
| Weight | double | 0% |  |  |
| KPI Key | string |  | yes |  |
| Sort | int64 |  | yes |  |

## _Measures

| Column | Type | Format | Hidden | Notes |
|---|---|---|---|---|
| Dummy | string |  | yes |  |
