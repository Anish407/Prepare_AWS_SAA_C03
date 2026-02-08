## What is Amazon S3 Select?
Amazon S3 Select allows you to retrieve **a subset of data** from an object stored in Amazon S3 using **SQL expressions**, without downloading the entire object.

Filtering happens **at the storage layer**, which reduces:
- Data transfer
- Latency
- Cost

This is especially useful for data engineering, analytics, and ML preprocessing workloads.

---

## Why S3 Select Exists (The Problem)
In many real-world systems:
- Objects in S3 can be large (hundreds of MBs or GBs)
- Applications often need only:
  - A few columns
  - A small subset of rows

Downloading the entire object and filtering locally is inefficient and expensive.

---

## Dataset Used
**File:** [events.csv](./events.csv)
**Location:** `s3://<bucket-name>/data/events.csv`

Columns:
- `user_id`
- `country`
- `event_type`
- `event_time`
- `session_duration`
- `device`
- `value`

---

## Baseline Approach (Without S3 Select)
1. Upload the file to s3
2. Download the full object from S3
3. Parse the CSV locally
4. Filter rows in application code

### Downsides
- Entire object transferred over the network
- Higher latency
- Higher data transfer cost
- Poor scalability

---

## S3 Select Approach
Instead of downloading the full object:
- Create an s3 bucket and upload the CSV file
- Run a SQL query directly on the S3 object
- Stream back only the matching rows and columns

---

## Running the Lab (AWS Console)

1. Open the S3 object (`events.csv`)
2. Choose **Query with S3 Select**
   <img width="1878" height="708" alt="1 select" src="https://github.com/user-attachments/assets/e698d9e2-831d-414b-b944-d055b7093a4b" />

4. Input format:
   - Format: **CSV**
   - **Enable:** *Exclude the first line of CSV data*  
     (Use this if the file contains a header row)
     <img width="1362" height="787" alt="2 selectoptions" src="https://github.com/user-attachments/assets/bfd7b447-ac89-47e9-b35d-56a278e154b5" />

5. Output format:
   - CSV

If this header option is not enabled:
- `SELECT *` will work
- Column-based filters (e.g. `s.user_id`) will fail

---

## Sample Queries

### 1. Return first few rows
```sql
SELECT * FROM S3Object s LIMIT 5
```

### 2. Filter by user ID
```sql
SELECT * FROM S3Object s WHERE s.user_id = '1001'
```
<img width="1792" height="716" alt="4 result1" src="https://github.com/user-attachments/assets/eb6158df-4816-4db9-b083-70c41e1fdc39" />

### 3. Filter by country
```sql
SELECT * FROM S3Object s WHERE s.country = 'SE'
```
<img width="958" height="725" alt="5 result" src="https://github.com/user-attachments/assets/1ac5911b-1b1c-42b8-a685-2f11d4b2843a" />

### 4. Column projection (cost-efficient)
```sql
SELECT s.user_id, s.event_type, s.value FROM S3Object s WHERE s.country = 'SE'
```

### 5. Click events with value
```sql
SELECT s.user_id, s.event_time, s.value FROM S3Object s WHERE s.event_type = 'click'   AND s.value > 0
```
<img width="958" height="725" alt="5 result" src="https://github.com/user-attachments/assets/97f16d33-a85f-4583-b322-b097baa014d7" />

### 6. Purchase events only
```sql
SELECT s.user_id, s.country, s.value FROM S3Object s WHERE s.event_type = 'purchase'
```

### 7. High-value purchases from Sweden
```sql
SELECT * FROM S3Object s WHERE s.country = 'SE'AND s.event_type = 'purchase' AND CAST(s."value" AS float) > 100
```
<img width="1822" height="663" alt="6 result" src="https://github.com/user-attachments/assets/5cbefbcf-885b-4398-b3fc-7890ca47a7af" />

> I struggled here since s.value always failed, it was because value is a keyword and we need to wrap in it ""

### 8. Count events in the file
```sql
SELECT COUNT(*) AS total_events FROM S3Object s
```
### 9 Sum of total sales
```sql 
SELECT SUM(CAST(s."value" as float)) AS total_revenue FROM S3Object s WHERE s.event_type = 'purchase'
```
<img width="1765" height="622" alt="7" src="https://github.com/user-attachments/assets/7ce8075d-c138-4219-a61d-891903b272aa" />

---

## Key Learnings
- S3 Select performs **push-down filtering**
- Only required data is transferred
- Column projection provides the biggest cost savings
- Schema is applied **at read time** (schema-on-read)

---

## Supported Formats
- CSV
- JSON
- Parquet

---

## Limitations (Important)
- Queries apply to **a single object only**
- No joins
- Limited SQL dialect
- Not suitable for real-time APIs or transactional workloads

---

## When to Use S3 Select
- Large CSV / JSON / Parquet objects
- Partial data access
- Read-heavy workloads
- Cost-sensitive architectures

---

## When NOT to Use S3 Select
- Queries across many files
- Complex analytics
- Joins or multi-dataset queries
- Frequent low-latency requests

---

## Common Pitfalls
- Forgetting to enable header row handling
- Using column names when headers are ignored
- Hidden BOM characters in CSV headers
- Leading whitespace or newlines in SQL strings (API usage)

---
