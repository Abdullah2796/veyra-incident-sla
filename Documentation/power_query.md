# Power Query (M) catalogue

Every table is loaded from the files in `Data/` through the `DataFolder` parameter. `RawIncidents` is a staging query (not loaded) shared by the fact table and the data-quality log.

## RawIncidents (staging, not loaded)

```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "itsm_incident_export.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true])
in
    Promoted
```

## Data Quality Log

```powerquery
let
    Raw = RawIncidents,
    Duplicates = Table.RowCount(Raw) - Table.RowCount(Table.Distinct(Raw, {"number"})),
    PriorityVariants = Table.RowCount(Table.SelectRows(Raw, each not Text.Contains([priority], " - "))),
    MunicipalityCase = Table.RowCount(Table.SelectRows(Raw, each [municipality] = Text.Upper([municipality]))),
    BadTimes = Table.RowCount(Table.SelectRows(FactIncident, each [State] <> "Open" and [Resolution Hours] = null)),
    NoGroup = Table.RowCount(Table.SelectRows(FactIncident, each [Group Code] = "UNASSIGNED")),
    Orphans = Table.RowCount(Table.SelectRows(FactCSAT, each [Has Incident] = false)),
    Result = #table(
        type table [Check = text, Source = text, Records Affected = Int64.Type, Action Taken = text, Sort = Int64.Type],
        {
            {"Duplicate incident rows", "ITSM export (CSV)", Duplicates, "Removed – one row per incident number", 1},
            {"Priority written in non-standard formats", "ITSM export (CSV)", PriorityVariants, "Mapped P1 / High / low etc. to P1–P4", 2},
            {"Resolved before opened (clock errors)", "ITSM export (CSV)", BadTimes, "Excluded from resolution time and SLA", 3},
            {"Open incidents with no resolver group", "ITSM export (CSV)", NoGroup, "Shown as 'Unassigned' so they are not lost", 4},
            {"Municipality in capitals", "ITSM export (CSV)", MunicipalityCase, "Ignored – municipality taken from the site master", 5},
            {"Survey responses for unknown incidents", "CSAT survey (CSV)", Orphans, "Flagged and excluded from CSAT", 6}
        })
in
    Result
```

## DimDate

```powerquery
let
    Dates = List.Dates(#date(2026, 1, 1), 365, #duration(1, 0, 0, 0)),
    AsTable = Table.FromList(Dates, Splitter.SplitByNothing(), type table [Date = date]),
    AddYear = Table.AddColumn(AsTable, "Year", each Date.Year([Date]), Int64.Type),
    AddMonthNo = Table.AddColumn(AddYear, "Month No", each Date.Month([Date]), Int64.Type),
    AddMonth = Table.AddColumn(AddMonthNo, "Month", each Date.ToText([Date], "MMM", "en-US"), type text),
    AddMonthStart = Table.AddColumn(AddMonth, "Month Start", each Date.StartOfMonth([Date]), type date),
    AddWeek = Table.AddColumn(AddMonthStart, "Week Start", each Date.StartOfWeek([Date], Day.Monday), type date),
    AddWdNo = Table.AddColumn(AddWeek, "Weekday No", each Date.DayOfWeek([Date], Day.Monday) + 1, Int64.Type),
    AddWd = Table.AddColumn(AddWdNo, "Weekday", each Date.ToText([Date], "ddd", "en-US"), type text)
in
    AddWd
```

## DimGroup

```powerquery
let
    Source = Json.Document(File.Contents(DataFolder & "resolver_groups_api.json")),
    Groups = Table.FromRecords(Source[groups]),
    Renamed = Table.RenameColumns(Groups, {{"code", "Group Code"}, {"name", "Group"}, {"type", "Group Type"}, {"vendor", "Vendor"}}),
    WithUnassigned = Table.InsertRows(Renamed, Table.RowCount(Renamed), {[Group Code = "UNASSIGNED", Group = "Unassigned", Group Type = "Unassigned", Vendor = null]}),
    Filled = Table.ReplaceValue(WithUnassigned, null, "In-house", Replacer.ReplaceValue, {"Vendor"}),
    Typed = Table.TransformColumnTypes(Filled, {{"Group Code", type text}, {"Group", type text}, {"Group Type", type text}, {"Vendor", type text}})
in
    Typed
```

## DimPriority

```powerquery
let
    Source = Excel.Workbook(File.Contents(DataFolder & "sla_policy_and_targets.xlsx"), null, true),
    Sheet = Source{[Item = "SLA Policy", Kind = "Sheet"]}[Data],
    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Priority", type text}, {"Priority Name", type text}, {"Response Target (min)", Int64.Type}, {"Resolution Target (hrs)", Int64.Type}})
in
    Typed
```

## DimRelease

```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "release_calendar.csv"), [Delimiter = ",", Encoding = 65001]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Release", type text}, {"Release Date", type date}, {"Type", type text}}, "en-US")
in
    Typed
```

## DimSite

```powerquery
let
    Source = Excel.Workbook(File.Contents(DataFolder & "customer_sites.xlsx"), null, true),
    Sheet = Source{[Item = "Sites", Kind = "Sheet"]}[Data],
    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Site ID", type text}, {"Municipality", type text}, {"Segment", type text}, {"Devices", Int64.Type}, {"Contract Start", type date}})
in
    Typed
```

## FactCSAT

```powerquery
let
    Source = Csv.Document(File.Contents(DataFolder & "csat_survey_responses.csv"), [Delimiter = ",", Encoding = 65001, QuoteStyle = QuoteStyle.Csv]),
    Promoted = Table.PromoteHeaders(Source, [PromoteAllScalars = true]),
    Renamed = Table.RenameColumns(Promoted, {{"incident_number", "Incident Number"}, {"response_date", "Response Date"}, {"score", "Score"}, {"comment_theme", "Comment Theme"}}),
    Typed = Table.TransformColumnTypes(Renamed, {{"Response Date", type date}, {"Score", Int64.Type}}, "en-US"),
    // flag survey rows whose incident number is not in the incident export
    Known = Table.Buffer(Table.AddColumn(Table.RenameColumns(Table.SelectColumns(FactIncident, {"Number"}), {{"Number", "Known Number"}}), "Has Incident", each true, type logical)),
    Joined = Table.Join(Typed, "Incident Number", Known, "Known Number", JoinKind.LeftOuter, JoinAlgorithm.RightHash),
    Flagged = Table.ReplaceValue(Table.RemoveColumns(Joined, {"Known Number"}), null, false, Replacer.ReplaceValue, {"Has Incident"}),
    Result = Table.TransformColumnTypes(Flagged, {{"Has Incident", type logical}})
in
    Result
```

## FactIncident

```powerquery
let
    Raw = RawIncidents,
    // 1. remove duplicated export rows
    Dedup = Table.Distinct(Raw, {"number"}),
    // 2. parse dd/MM/yyyy timestamps; blank resolved = still open
    Parse = (t as text) as nullable datetime => if t = "" then null else DateTime.FromText(t, [Format = "dd/MM/yyyy HH:mm", Culture = "en-GB"]),
    Typed = Table.TransformColumns(Dedup, {{"opened_at", Parse, type datetime}, {"acknowledged_at", Parse, type datetime}, {"resolved_at", Parse, type datetime}}),
    // 3. normalise priority variants (P1, High, 2 - High, low) to P1-P4
    PriorityMap = [#"1" = "P1", #"2" = "P2", #"3" = "P3", #"4" = "P4", critical = "P1", high = "P2", moderate = "P3", low = "P4"],
    NormPriority = Table.AddColumn(Typed, "Priority", each
        let t = Text.Lower(Text.Trim([priority])),
            digit = Text.Select(t, {"1".."4"})
        in if digit <> "" then Record.Field(PriorityMap, Text.Start(digit, 1)) else Record.FieldOrDefault(PriorityMap, t, null), type text),
    Targets = Table.Buffer(DimPriority),
    Joined = Table.Join(NormPriority, "Priority", Table.RenameColumns(Table.SelectColumns(Targets, {"Priority", "Response Target (min)", "Resolution Target (hrs)"}), {{"Priority", "Target Priority"}}), "Target Priority", JoinKind.LeftOuter),
    AsOf = List.Max(Joined[opened_at]),
    // 4. durations; resolved-before-opened timestamps are treated as invalid
    AddResp = Table.AddColumn(Joined, "Response Minutes", each Duration.TotalMinutes([acknowledged_at] - [opened_at]), type number),
    AddRes = Table.AddColumn(AddResp, "Resolution Hours", each
        if [resolved_at] = null then null
        else let h = Duration.TotalHours([resolved_at] - [opened_at]) in if h < 0 then null else h, type number),
    AddOpen = Table.AddColumn(AddRes, "Is Open", each [state] = "Open", type logical),
    AddAge = Table.AddColumn(AddOpen, "Age Hours", each if [Is Open] then Duration.TotalHours(AsOf - [opened_at]) else null, type number),
    AddRespMet = Table.AddColumn(AddAge, "Response Met", each [Response Minutes] <= [#"Response Target (min)"], type logical),
    AddResMet = Table.AddColumn(AddRespMet, "Resolution Met", each if [Resolution Hours] = null then null else [Resolution Hours] <= [#"Resolution Target (hrs)"], type logical),
    AddAged = Table.AddColumn(AddResMet, "Is Aged", each [Is Open] and [Age Hours] > [#"Resolution Target (hrs)"], type logical),
    AddReopen = Table.AddColumn(AddAged, "Reopened", each Number.From([reopen_count]) > 0, type logical),
    AddShift = Table.AddColumn(AddReopen, "Shift", each
        let h = Time.Hour([opened_at]), wd = Date.DayOfWeek([opened_at], Day.Monday)
        in if wd < 5 and h >= 7 and h < 20 then "Business hours" else "Evenings & weekends", type text),
    AddBucket = Table.AddColumn(AddShift, "Age Bucket", each
        if [Age Hours] = null then null else if [Age Hours] < 24 then "< 1 day" else if [Age Hours] < 72 then "1–3 days"
        else if [Age Hours] < 168 then "3–7 days" else if [Age Hours] < 720 then "1–4 weeks" else "> 4 weeks", type text),
    AddBucketSort = Table.AddColumn(AddBucket, "Age Bucket Sort", each List.PositionOf({"< 1 day", "1–3 days", "3–7 days", "1–4 weeks", "> 4 weeks"}, [Age Bucket]) + 1, Int64.Type),
    AddBand = Table.AddColumn(AddBucketSort, "Resolution Band", each
        if [Resolution Hours] = null then null else if [Resolution Hours] < 4 then "< 4 hrs" else if [Resolution Hours] < 24 then "4–24 hrs"
        else if [Resolution Hours] < 72 then "1–3 days" else "> 3 days", type text),
    AddBandSort = Table.AddColumn(AddBand, "Resolution Band Sort", each List.PositionOf({"< 4 hrs", "4–24 hrs", "1–3 days", "> 3 days"}, [Resolution Band]) + 1, Int64.Type),
    // 5. missing resolver group -> UNASSIGNED
    AddGroup = Table.AddColumn(AddBandSort, "Group Code", each if [assignment_group] = "" then "UNASSIGNED" else [assignment_group], type text),
    AddDate = Table.AddColumn(AddGroup, "Opened Date", each DateTime.Date([opened_at]), type date),
    Renamed = Table.RenameColumns(AddDate, {{"number", "Number"}, {"opened_at", "Opened At"}, {"category", "Category"}, {"contact_type", "Channel"},
        {"site_id", "Site ID"}, {"state", "State"}, {"caused_by_release", "Release"}}),
    Result = Table.SelectColumns(Renamed, {"Number", "Opened At", "Opened Date", "Priority", "Category", "Channel", "Group Code", "Site ID", "State", "Shift", "Release",
        "Response Minutes", "Resolution Hours", "Age Hours", "Response Met", "Resolution Met", "Is Open", "Is Aged", "Reopened",
        "Age Bucket", "Age Bucket Sort", "Resolution Band", "Resolution Band Sort"})
in
    Result
```

## KPI Targets

```powerquery
let
    Source = Excel.Workbook(File.Contents(DataFolder & "sla_policy_and_targets.xlsx"), null, true),
    Sheet = Source{[Item = "KPI Targets", Kind = "Sheet"]}[Data],
    Promoted = Table.PromoteHeaders(Sheet, [PromoteAllScalars = true]),
    Typed = Table.TransformColumnTypes(Promoted, {{"Target", type number}, {"Weight", type number}, {"Sort", Int64.Type}, {"KPI", type text}, {"Direction", type text}, {"KPI Key", type text}})
in
    Typed
```

## _Measures

```powerquery
let
    Source = #table(type table [Dummy = text], {})
in
    Source
```
