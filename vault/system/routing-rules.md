# Routing rules

Human-readable summary of how captures are routed. The machine-readable source
of truth lives in `app/config.py` (a future iteration can move it here as YAML).

## Destinations

| Key | Note folder | What goes here |
|-----|-------------|----------------|
| family | notes/family | Facts about children/family members |
| podcasts | notes/podcasts | Podcast/episode notes, timestamped |
| work | notes/work | Work ideas, project updates |
| learning | notes/learning | AI/developer learning |
| projects | notes/projects | Personal projects |
| health | notes/health | Health/sports log |
| shopping | notes/shopping | Errands, shopping |
| references | notes/references | General reference |
| unknown | (inbox) | Needs review |

## Matchers (each contributes a scored, explained vote)

- **entity** — a known person/project/podcast is named -> route to its note (strongest).
- **keyword** — destination keyword hits.
- **example** — similarity to a saved correction.
- **podcast** — timestamps / "podcast"/"episode" -> podcast note (+ session grouping).

## Ask the user when

- confidence is below the auto-sort threshold,
- two+ destinations score nearly equally,
- the note is a task/reminder rather than knowledge,
- it contains sensitive info with no clear destination,
- it would create a new long-lived note and confidence is only moderate.

## Do NOT ask when

- a known entity makes the destination obvious,
- a similar saved correction already exists,
- the action is reversible and confidence is high.
