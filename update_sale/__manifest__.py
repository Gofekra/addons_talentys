{
    "name": "Update sale",
    "version": "1.0",
    "depends": ["base","sale"],
    "author": "VEONE",
    "category": "purchases",
    "description": """
   Module de gestion des achats :
   - Expression des besoins d'achat
   - Emission de demande de cotation
   - Bons de commande
   - Suivi des commandes
   - Ecart des besoins
   - Tableau de bord des alertes de produits en réparation
    """,
    "init_xml": [],
    'data': [
            "views/update_sale_view.xml",
        ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
