# EC2 Placement Groups

## What problem do placement groups solve

Placement groups control how EC2 instances are physically placed on AWS hardware inside a single availability zone.

They are used when you need one of the following:
- Extremely low latency and high network throughput
- Strong fault isolation between instances
- Predictable failure domains for large distributed systems

Placement groups do not span regions or availability zones and they do not improve internet latency.

---

## Types of placement groups

## Cluster placement group

Cluster placement groups place instances physically close together on the same underlying hardware.

They are optimized for:
- Very low network latency
- Very high bandwidth
- High packets per second

Typical use cases:
- High performance computing
- Machine learning training on EC2
- Distributed simulations
- Real time analytics engines

Important constraints:
- All instances must be in the same availability zone
- Only certain instance types are supported
- You can get capacity errors when launching or scaling
- Scaling later may fail even if it worked initially

Key exam points:
- Does not provide fault tolerance
- A single hardware failure can affect multiple instances
- Used for performance, not availability

---

## Spread placement group

Spread placement groups place each instance on separate underlying hardware.

They are optimized for:
- Maximum fault isolation
- Protection against hardware failure

Typical use cases:
- Critical application nodes
- Master or controller nodes
- Small but highly important workloads

Limits:
- Maximum of 7 instances per availability zone
- Not designed for large scale systems

Key exam points:
- Best choice when instance isolation is required
- Not suitable for performance optimization
- Not suitable for large fleets

### Physical placement detail:
- Each instance in a spread placement group is placed on distinct underlying hardware.
- This typically means different physical racks with separate power and networking.
- AWS guarantees hardware isolation but abstracts the exact physical layout.


---

## Partition placement group

Partition placement groups divide instances into logical partitions.

Each partition runs on separate hardware, but instances within the same partition may share hardware.

They are optimized for:
- Large scale distributed systems
- Controlled failure domains

Typical use cases:
- Cassandra
- Kafka
- HDFS
- Distributed databases

Important concept:
- AWS provides partition boundaries
- The application is responsible for handling failures

Key exam points:
- Supports hundreds of instances
- Limited to a single availability zone
- Used when the application understands fault domains

Physical placement detail:
- Each partition is placed on a separate set of underlying hardware.
- This usually maps to different physical racks, power sources, and network paths.
- Instances within the same partition may share hardware and can fail together.


---

## When to use placement groups

Use placement groups only when:
- You have a clear performance or fault isolation requirement
- You understand the scaling and capacity risks
- The workload explicitly benefits from physical placement control

> Do not use placement groups for general purpose workloads.

---

## Common misconceptions

- Placement groups do not span availability zones
- Placement groups do not replace load balancers
- Placement groups do not improve internet traffic
- Placement groups affect physical placement, not security or routing

---

## Exam strategy summary

- If the question mentions low latency or high throughput, choose cluster placement group.
- If the question mentions critical instances and fault isolation, choose spread placement group.
- If the question mentions large distributed systems with controlled failure domains, choose partition placement group.
- If the question mentions multiple availability zones, placement groups are not the answer.
