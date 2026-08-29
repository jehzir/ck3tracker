# Logrono Holder Adjudication

- Baseline: `ck3_1_19_0_6_867` (`0867-01-01`)
- Evidence save: `Sheikh_Lubb_of_Najera_867_01_01.ck3`
- SHA-256: `b7ec35196c8577957adbbd71323a7925b37652ebf26f5cff735f9376a91ad48f`
- Game version: `1.19.0.6`
- Review date: 2026-08-29

## Finding

Installed title history declares dead character `73812` as holder of `b_logrono`. Installed character history records his death on `0862-09-26`.

The immediate unmodded 867 start save records Sheikh Lubb as save-local character `12876`, with `c_najera` as his primary title and `b_logrono` in his domain. The installed baseline already identifies the holder of `c_najera` as historical character `73813`, Lubb, born `0831-01-01`, Basque, Muwalladi, and a member of House Musa.

The title hierarchy remains:

- `c_najera`: county, held by `73813`
- `b_logrono`: city barony under `c_najera`

The reviewed adjudication therefore records `73813` as the runtime-resolved holder of `b_logrono` at the 867 baseline. The original `b_logrono -> 73812` title-history declaration remains unchanged and auditable.

## Validation Contract

- The save date and game version must exactly match the baseline and snapshot.
- The observed title must appear in the saved player's domain.
- The saved primary title's installed holder must resolve the save-local player to the adjudicated stable character ID.
- The adjudicated character must be unique and alive at the baseline.
- A reviewed adjudication applies only while its recorded declared holder still matches current installed title history.