# IAM Inline Policies (AWS)

## What an inline policy is
An **inline policy** is an IAM policy document that is **embedded directly** into a single IAM identity:

- **User inline policy** → attached to **one user**
- **Role inline policy** → attached to **one role**
- **Group inline policy** → attached to **one group**

It is **not reusable** across identities like a managed policy.

---

## Why inline policies matter 
A user/role can appear to have “no permissions” if you only check **attached managed policies**, but still have full access via an inline policy.

That’s why these two are different:

- **Managed policy attached?** `list-attached-*-policies`
- **Inline policy exists?** `list-*-policies`

If you only run the first, you can miss the real permissions.

---

## How to recognize inline vs managed
### Managed policy
- Has its own ARN like:
  `arn:aws:iam::ACCOUNT_ID:policy/MyManagedPolicy`
- Can be attached to many users/roles/groups

### Inline policy
- Has **no policy ARN**
- Lives inside the identity
- Identified only by a **policy name** within that identity

---

## CLI commands (most useful)
### User inline policies
List inline policy names:
```bash
aws iam list-user-policies --user-name <USER>
```

## When inline policies are a bad idea

Inline policies make permissions harder to audit and standardize because they:
- are easy to forget
- cannot be reused
- can cause “mystery access” during debugging

Best practice: prefer managed policies for normal permission management.
Use inline policies only for edge cases where you truly want a policy to exist only on one identity and nowhere else.
