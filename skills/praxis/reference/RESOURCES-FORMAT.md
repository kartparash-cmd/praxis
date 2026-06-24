# Resources format

`RESOURCES.md` is the list of **high-trust sources** the skill grounds teaching
in. The rule is: **never trust parametric knowledge.** Lessons cite from here.

A public seed ships in the repo so the skill honors its own rule out of the box.
Kay's private overlay *adds* his stacks; it never *enables* correctness.

```
# Resources

## <topic or stack>
- [Title](https://canonical-url) — one line on why it's trustworthy (official
  docs, the paper, a maintainer's write-up). Tier: primary | secondary.
```

## Tiers

- **primary** — official docs, source code, the original paper, the maintainer.
  Lessons should cite these for any load-bearing claim.
- **secondary** — strong community write-ups, well-known talks. Fine for
  intuition; not for a claim you'd bet the lesson on.

When a lesson makes a claim with no resource to back it, flag it inline as
low-confidence rather than stating it as fact.
