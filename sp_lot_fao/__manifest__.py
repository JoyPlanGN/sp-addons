{
    "name": "Salerno Pesca - Tracciabilità FAO su Lotti",
    "version": "19.0.1.1.0",
    "category": "Inventory",
    "summary": "Gestione FAO, metodo di produzione e tracciabilità su lotti ittici",
    "author": "Salerno Pesca / JoyPlan",
    "license": "LGPL-3",
    "depends": [
        "stock",
        "purchase",
        "product",
    ],

   "data": [
    "security/ir.model.access.csv",
    "views/stock_lot_views.xml",
    "views/product_template_views.xml",
],
    "installable": True,
    "application": True,
}
