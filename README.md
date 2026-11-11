# pyWR WCPS Game server

## Client versions

`main` targets **Code Name Legacy**, a WarRock Chapter 1 mod built on the
international **PF23** client (December 2008): client tables generated from the
Legacy data files and PF23 packet IDs (migration in progress).

**PF20** (October 2008) is frozen as a reference:

- Tag `pf20-reference`: the exact state when PF20 support was frozen. It never moves.
- Branch `pf20`: starts at that tag and only receives **backports** of bug fixes
  in logic shared by both versions (rooms, damage, inventory...), cherry-picked
  from `main`. PF23-specific changes (tables, renumbered packets) are not backported.

To run the PF20 reference, check out `pf20` in `wcps_auth` and `wcps_game`.
`wcps_core` has no version-specific code and stays on `main` for both.

## Dependencies
- aiomysql 0.2.0 
- pandas 2.2.2
- pydantic 2.8.2
- pydantic-core 2.20.1
- pydantic-settings 2.4.0
