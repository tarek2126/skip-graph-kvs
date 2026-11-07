# Skip Graph Key-Value Store

A small Python simulator of query routing in a distributed key-value store built on a Skip Graph. Each node knows only its own label, its key range and its neighbour links at each level.

## What it does
- Builds an 8-node Skip Graph from node labels and membership vectors.
- Routes exact-match queries from node to node using only local information.
- Answers range queries by routing to the owner of the lower bound, then walking the level-0 links.

## Run
Requires Python 3.8 or newer.

    python skip_graph_kvs.py

## Example output

```
Routing table (level: left / right)
   5 [00]  L2: - / 45, L1: - / 21, L0: - / 13
  13 [10]  L2: - / 62, L1: - / 30, L0: 5 / 21
  21 [01]  L2: - / 71, L1: 5 / 45, L0: 13 / 30
  30 [11]  L2: - / 80, L1: 13 / 62, L0: 21 / 45
  45 [00]  L2: 5 / -, L1: 21 / 71, L0: 30 / 62
  62 [10]  L2: 13 / -, L1: 30 / 80, L0: 45 / 71
  71 [01]  L2: 21 / -, L1: 45 / -, L0: 62 / 80
  80 [11]  L2: 30 / -, L1: 62 / -, L0: 71 / -

Exact query: get(37) from entry node 5
start at 5 (level 2)
  level 2: cannot move, drop to level 1
  level 1: 5 -> 21
  level 1: cannot move, drop to level 0
  level 0: 21 -> 30
owner reached: 30 manages [30, 45)
  result: grape

Exact query: get(8) from entry node 80
start at 80 (level 2)
  level 2: 80 -> 30
  level 2: cannot move, drop to level 1
  level 1: 30 -> 13
  level 1: cannot move, drop to level 0
  level 0: 13 -> 5
owner reached: 5 manages [5, 13)
  result: lemon

Range query: keys 40..75 from entry node 13
start at 13 (level 2)
  level 2: cannot move, drop to level 1
  level 1: 13 -> 30
owner reached: 30 manages [30, 45)
  level-0 walk over nodes [30, 45, 62, 71]
  result: [(42, 'pear'), (50, 'mango'), (66, 'kiwi'), (73, 'plum')]
```

## Notes
Written as a course project at the University of Fukui. It is a teaching simulator, not a performance benchmark. Load balancing and node failure recovery are not handled.
