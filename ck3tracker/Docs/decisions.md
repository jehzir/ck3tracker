# Crusader Kings III – Formation Decisions Summary

> **Gameplay reference only:** This is not an architecture decision log or implementation manifest. Use `Docs/architecture.md` for durable system boundaries and `Docs/current_build.md` for the sole current execution path.

| Title / Decision              | Type        | Requirements (Simplified)                                                                 | Region / Notes |
|------------------------------|-------------|---------------------------------------------------------------------------------------------|----------------|
| **Create Kingdom (Generic)** | Kingdom     | 51% de jure counties; 2 duchies; 500 gold; 1000 prestige                                   | Standard creation |
| **Create Empire (Generic)**  | Empire      | 80% de jure counties; 2 kingdoms; 1000 gold; 2000–4000 prestige                             | Standard creation |
| **Restore the Roman Empire** | Empire      | Control Italy, Balkans, Anatolia, Levant, North Africa; hold multiple empires; high prestige | Grants Augustus |
| **Control the Mediterranean**| Empire/Feat | Control all Mediterranean coastal counties                                                   | Achievement-style |
| **Restore Carthage**         | Kingdom     | Control Carthage/Tunis duchies; high prestige; North African/Punic culture preferred         | Special decision |
| **Form the Holy Roman Empire**| Empire     | Control core German duchies; Christian faith; high prestige                                  | Creates HRE |
| **Form the Empire of Francia**| Empire     | Control West Francia, Lotharingia, Burgundy; high prestige                                   | Creates Francia |
| **Form the Empire of Britannia**| Empire   | Control England, Scotland, Wales, Ireland; high prestige                                     | Creates Britannia |
| **Form the Empire of Russia**| Empire      | Control East Slavic kingdoms; East Slavic culture                                            | Creates Russia |
| **Unify the Slavs**          | Cultural    | Control Slavic homelands; Slavic culture                                                     | Creates Slavic Empire |
| **Unify the German Peoples** | Cultural    | Control German duchies; German culture                                                       | Creates German Empire |
| **Unify India**              | Cultural    | Control Deccan, Bengal, Rajasthan kingdoms; Indian culture                                   | Creates Indian Empire |
| **Unify the Maghreb**        | Cultural    | Control Berber homelands; Berber culture                                                     | North Africa |
| **Unify the Horn of Africa** | Cultural    | Control Somali/Ethiopian homelands; Horn cultures                                            | East Africa |
| **Unify the Steppe**         | Cultural    | Control major steppe duchies; Steppe cultures                                                | Eurasian Steppe |
| **Unify the Sahel**          | Cultural    | Control Sahelian kingdoms; Sahelian cultures                                                 | West Africa |
| **Kingdom of Israel**        | Religious   | Jewish faith; control Jerusalem + surrounding duchies; high piety                            | Creates Israel |
| **Restore the Caliphate**    | Religious   | Islamic faith; control Baghdad or Damascus; high piety                                       | Creates Caliphate |
| **Restore Papacy (Christian)**| Religious  | Control Rome; Catholic faith; install Pope                                                   | Restores Papal State |
| **Restore Zoroastrian High Priesthood** | Religious | Zoroastrian faith; control Persian duchies; high piety                                       | Restores priesthood |
| **Kingdom of Portugal**      | Kingdom     | Control Porto, Coimbra; Christian faith; high prestige                                       | Creates Portugal |
| **Kingdom of Asturias → Spain**| Kingdom   | Control Asturias, Galicia, León; Christian faith; high prestige                              | Creates Spain |
| **Kingdom of Mann & the Isles**| Kingdom   | Control Mann + Isles duchies; Norse culture; high prestige                                   | Special kingdom |
| **Kingdom of Bavaria (Restore)**| Kingdom  | Control Bavarian duchies; high prestige                                                      | Restored title |
| **Kingdom of Aksum/Ethiopia**| Kingdom     | Control Aksum, Semien; East African faith/culture; high piety                                | Creates Ethiopia |
| **Unify Ireland**            | Kingdom     | Control all Irish duchies; high prestige                                                     | Creates Ireland |
| **Unify Wales**              | Kingdom     | Control all Welsh duchies; high prestige                                                     | Creates Wales |
| **Unify Alba (Scotland)**    | Kingdom     | Control all Scottish duchies; high prestige                                                  | Creates Scotland |

Restore Roman Empire – Starting Requirements

• Must be an Emperor
• Must be independent
• Must have Exalted Among Men prestige
• Must be Roman culture OR Byzantine Emperor OR hold Empire of Italia
• Must control key duchies across Italy, Balkans, North Africa, Iberia, Gaul, Britannia, Anatolia, and the Levant
• Must be Feudal/Clan (not Tribal)
• Must not be at war

To restore the Roman Empire, you must personally control the following duchies:

Italy: Latium, Campania, Spoleto, Tuscany, Lombardy, Verona, Friuli  
Balkans: Dalmatia, Croatia, Bosnia, Rashka, Bulgaria, Thrace  
North Africa: Carthage, Tripolitania  
Iberia: Baetica, Tarraconensis  
Gaul: Provence, Toulouse, Poitou  
Britannia: Wessex  
Anatolia: Opsikion, Thrakesion, Cibyrrhaeot  
Levant: Palestine, Galilee


# Best Hybrid Path for Sicilian → Roman Heritage

1. Raise acceptance with Greek culture.
   • Marry Greeks
   • Use Greek vassals
   • Promote Cultural Acceptance
   • Convert a few counties (optional)

2. Hybrid Sicilian + Greek.
   • Select "Roman Heritage"
   • Language: Latin
   • Aesthetics: Roman (optional)
   • Keep Sicilian traditions

3. Convert your ruler and capital to the new hybrid.

4. Restore the Roman Empire.
   • Roman heritage is the only requirement.


# 867 Sicilian Start → Roman Heritage Hybrid Plan

## Overview
This document outlines the optimal strategy for starting as **Sicilian** in 867, leveraging early traditions like **Sword for Hire**, exploiting the chaos of Sicily and southern Italy, and transitioning into a **true Roman-heritage culture** through hybridization with Greek. This path avoids Sardinian entirely and focuses on Sicilian as the base culture.

---

## Why Sicilian (867) Is the Best Start
- **Mediterranean Martial** — excellent for early warfare and naval mobility.
- **Sword for Hire** — powerful early-game gold engine via mercenaries.
- **Latin Group** — easy acceptance with Greek, Italian, and future Sicilian pops.
- **Proximity to Greek counties** — essential for hybridization.
- **Sicily’s natural chaos** — ideal for opportunistic expansion.

---

## Strategic Goals
1. **Use Sicilian traditions early** to stabilize and expand.
2. **Exploit southern Italy’s instability** to grab key counties.
3. **Raise acceptance with Greek** for hybridization.
4. **Hybrid Sicilian + Greek → Roman Heritage**.
5. **Convert ruler + capital** to the new hybrid culture.
6. **Expand up the Italian boot**.
7. **Restore the Roman Empire** using true Roman heritage.

---

## Phase 1 — Early Game (867–900)
### Objectives
- Consolidate power in Sicily.
- Build economy using Sword for Hire.
- Capture Greek-majority counties.

### Key Targets
- **Palermo**
- **Messina**
- **Agrigento**
- **Calabria (Reggio, Catanzaro)**

### Actions
- Hire mercenaries early to win decisive wars.
- Focus on duchy control and coastal holdings.
- Begin integrating Greek courtiers and vassals.

---

## Phase 2 — Acceptance Building (900–950)
### Goal: Reach ~40–50 Greek Acceptance

### Methods
- Marry Greek courtiers.
- Appoint Greek vassals in Calabria/Sicily.
- Convert a few counties to Greek (optional).
- Use Steward → **Promote Cultural Acceptance**.

### Why Greek?
Hybridizing with Greek unlocks the **Roman Heritage** selector — the only way to become true Roman.

---

## Phase 3 — The Hybrid Moment (950–1000)
### Hybrid Sicilian + Greek

In the hybrid culture creation menu:

- **Heritage: Roman** ← critical
- Language: Latin
- Aesthetics: Roman (optional)
- Traditions:
  - Keep Sicilian strengths (Mediterranean Martial, Sword for Hire)
  - Add Roman Legacy later if desired

### Suggested Culture Names
- **Siculo-Roman**
- **Romano-Sicilian**
- **Neo-Roman**

### Immediate Actions
- Convert your ruler to the new hybrid.
- Move capital to a hybrid county and convert it.

You are now **true Roman heritage**, fully valid for Restore Roman Empire.

---

## Phase 4 — Midgame Expansion (1000–1100)
### Goals
- Consolidate southern Italy.
- Push north into Lombard and Italian lands.
- Form the **Empire of Italia** (optional but useful).

### Benefits of Forming Italia
- Prestige
- De jure claims
- Roman culture recognition (even if heritage is Italic)
- Flavor alignment with your Roman restoration

---

## Phase 5 — Restore the Roman Empire (1100+)
### Requirements
You already meet the cultural requirement:

- **Heritage: Roman**

Now it’s purely territorial:

- Italy
- Sicily
- Sardinia (optional)
- North Africa (partial)
- Balkans (partial)
- Rome itself

Once complete, you can enact **Restore the Roman Empire**.

---

## Culture Logic Summary

### Why Sicilian Works
- Latin group → easy Greek acceptance
- Strong traditions → excellent early game
- Perfect hybrid candidate → Roman heritage selectable

### Why Hybridization Is Required
- **Heritage cannot be changed through divergence.**
- **Heritage cannot be changed through decisions.**
- **Heritage can ONLY be changed during hybridization.**

### Why Greek Is the Key
- Hybridization with Greek unlocks the **Roman Heritage** option.
- No natural Roman-heritage cultures exist in CK3.

---

## Final Summary

**Start Sicilian → Expand into Sicily/Calabria → Raise Greek acceptance → Hybrid Sicilian + Greek → Select Roman Heritage → Convert → Expand Italy → Restore Rome.**

This is the cleanest, strongest, and most lore-friendly path to a true Roman Empire restoration from a Sicilian 867 start.

