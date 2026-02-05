# sp-addons (Salerno Pesca)

Repo privato che contiene i moduli extra di Odoo, separati per tipologia.

## Struttura
- `sp_custom/`    → moduli sviluppati per Salerno Pesca (modificabili)
- `sp_purchased/` → moduli acquistati (non modificare: estendere con moduli in sp_custom)
- `sp_oca/`       → moduli OCA (opzionale)
- `docs/`         → note tecniche (installazione, convenzioni, checklist upgrade)

## Regole
1) Non inserire moduli dentro `odoo/addons`.
2) Non modificare i moduli in `sp_purchased/`.
3) Per estensioni usare un modulo nuovo in `sp_custom/`.
