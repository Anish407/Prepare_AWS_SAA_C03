# S3 Versioning & Delete Marker – Hands-on Behavior Lab

## Objective
Understand the **exact behavior** of Amazon S3 when:
- Versioning is enabled *after* objects already exist
- Objects are overwritten multiple times
- Objects are deleted in a versioned bucket
- Delete markers are removed
- Objects are permanently deleted

This lab focuses on **what actually happens**, not assumptions.

---

## Lab Setup

- S3 bucket created
- Versioning initially **disabled**
- Same object key (file name) reused multiple times

---

## Step-by-Step Observations

### Step 1: Upload object before enabling versioning
- Bucket versioning was **disabled**
- Uploaded a file (e.g. `test.txt`)

**Observation:**
- Object exists as a **single version**
- When versioning is later enabled, this object appears with:
  - `VersionId = null`

**Important Insight:**
- Objects uploaded *before* versioning do **not** get retroactive version IDs
- They become the **base version** once versioning is enabled

---

### Step 2: Enable versioning
- Versioning enabled on the bucket

**Observation:**
- Existing object remains
- Its version is shown as `null`

---

### Step 3: Upload the same file again (same key)
- Uploaded another file with the same name (`test.txt`)

**Observation:**
- A **new version** is created
- The previous `null` version becomes a **noncurrent version**
- New upload becomes the **current version**

**Key Rule:**
- Overwriting an object in a versioned bucket always creates a new version

---

### Step 4: Upload multiple versions
- Uploaded the same file name multiple times

**Observation:**
- Each upload creates a **new version**
- All previous versions are retained
- Storage cost increases with every version

---

### Step 5: Delete the object
- Deleted the object using the console

**Observation:**
- A **delete marker** is created
- The object disappears from the default view
- Older versions still exist and still incur cost

**Key Rule:**
- Delete ≠ permanent delete in a versioned bucket
- Delete only adds a delete marker

---

### Step 6: Remove the delete marker
- Enabled **Show versions**
- Deleted only the **delete marker**

**Observation:**
- Object is restored automatically
- The latest real version becomes visible again

**Key Insight:**
- Delete markers only hide data
- Removing them restores access

---

### Step 7: Upload again after restore
- Uploaded another file with the same name

**Observation:**
- A new version is created
- Previous versions remain untouched

---

### Step 8: Permanently delete the object
- Selected:
  - All object versions
  - All delete markers
- Deleted them together

**Final Observation:**
- Object is permanently removed
- No versions remain
- Storage cost stops

**Key Rule:**
- Permanent deletion requires deleting:
  - Every version
  - Every delete marker

---

## Key Takeaways

- Objects uploaded **before** versioning get `VersionId = null`
- Versioning does **not** retroactively version old objects
- Overwrites always create new versions
- Deletes create delete markers, not actual deletions
- Removing a delete marker restores the object
- Permanent deletion requires deleting **all versions and delete markers**
- Versioning increases durability, **not cost efficiency**
- Lifecycle policies are mandatory for cost control

---

## Mental Model (Critical)

> In a versioned S3 bucket, an object key is just a label.  
> Each version is a real, billable object.  
> Delete markers are also real objects.

---

## Why This Matters
- Prevents silent storage cost growth
- Avoids incorrect assumptions in production
- Essential for backup, compliance, and ML data pipelines
- Common source of AWS exam trick questions

---
# Lifecyclepolicies

## Lifecycle Execution Timeline Example



T equals 0 hours (Jan 1, 10:00)

- Object is uploaded
- Object is the current version
- No lifecycle clocks are running yet

T equals 24 hours (Jan 2, 10:00), 1 day elapsed

- The rule "Expire current version after 1 day" triggers
- A delete marker is created
- The data version becomes noncurrent
- The noncurrent lifecycle timer starts at this point
- This is the first lifecycle action that occurs

T equals 48 hours (Jan 3, 10:00), 2 days elapsed

- The rule "Delete noncurrent versions after 1 day" triggers
- The noncurrent data version is permanently deleted
- The delete marker is expired and removed
