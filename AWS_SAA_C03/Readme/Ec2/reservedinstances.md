# EC2 Reserved Instances and Capacity Reservations

## EC2 pricing baseline

EC2 by default uses on demand pricing.

On demand pricing means:
- You pay by the second or hour
- Minimum charge is usually 60 seconds
- No long term commitment
- Full flexibility to start and stop instances

On demand pricing is the most expensive EC2 pricing model and acts as the baseline for all cost comparisons.

---

## Reserved Instances overview

Reserved Instances are a pricing option that allows you to save money by committing to EC2 usage for a fixed period.

Key characteristics:
- Commitment period of one year or three years
- Discounts of up to 72 percent compared to on demand pricing
- Best suited for long running and predictable workloads

You are trading flexibility for cost savings.

---

## Reserved Instance payment options

There are three payment models:

No Upfront:
- No initial payment
- Billed monthly
- Least discount

Partial Upfront:
- Some payment at purchase time
- Remaining cost billed monthly
- Medium discount

All Upfront:
- Full payment at purchase time
- No monthly payments
- Highest discount

The more you pay upfront, the higher the discount.

---

## Zonal and Regional Reserved Instances

Zonal Reserved Instances:
- Locked to a specific availability zone
- Provide capacity reservation
- Slightly higher discount
- Less flexible

Regional Reserved Instances:
- Apply across the entire region
- No capacity guarantee
- More flexible
- Slightly lower discount

More specificity results in better pricing.

---

## Convertible Reserved Instances

Convertible Reserved Instances provide flexibility.

They allow changes to:
- Instance family
- Instance type
- Operating system

Key tradeoff:
- More flexibility
- Lower discount than standard Reserved Instances

Best used when future requirements are uncertain.

---

## Reserved Instances marketplace

Reserved Instances can be:
- Bought from the AWS Marketplace
- Sold on the AWS Marketplace

This allows you to:
- Exit unused commitments
- Buy short term commitments from other customers

---

## When to use Reserved Instances

Reserved Instances are ideal for:
- Long running workloads
- Always on production systems
- Predictable usage patterns

They are not suitable for:
- Short lived workloads
- Unpredictable usage
- Experimental environments

---

## Capacity Reservations overview

Capacity Reservations guarantee that EC2 capacity is available for you in a specific availability zone.

Key characteristics:
- You reserve capacity, not a discount
- Charged at on demand pricing
- Charged even if instances are not running
- Can be created for any duration

Capacity Reservations are about availability, not cost savings.

---

## Important Capacity Reservation rule

You are billed for a Capacity Reservation whether you use it or not.

Unused reservations still incur full on demand charges.

---

## When to use Capacity Reservations

Capacity Reservations are suitable for:
- Business critical workloads
- Applications that must always be able to scale
- Short or custom duration capacity needs
- Scenarios where capacity availability matters more than cost

They are not cost optimization tools.

---

## Key differences summary

Reserved Instances:
- Provide cost savings
- Require long term commitment
- Best for predictable workloads

Capacity Reservations:
- Provide guaranteed capacity
- No cost savings
- Charged even when unused

---

## Exam takeaway

If the question focuses on reducing cost for long running workloads, choose Reserved Instances.

If the question focuses on guaranteeing capacity in a specific availability zone, choose Capacity Reservations.

If unused capacity still costs money, the answer is Capacity Reservations.
