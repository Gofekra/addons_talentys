##############################################################################
#
# Copyright (c) 2012 Veone - jonathan.arra@gmail.com
# Author: Jean Jonathan ARRA
#
# Fichier du module hr_synthese
# ##############################################################################
{
    "name" : "Mise à jour TALENTYS",
    "version" : "1.0",
    "author" : "Jean Jonathan ARRA(VEONE)",
    'category': 'report',
    "website" : "http://www.veone.net",
    "depends" : ["base", "sale",],
    "description": """
    """,
    "init_xml" : [],
    "demo_xml" : [],
    "data":[
        "wizard/wizard_sale_update_view.xml",
        "views/sale_order_lview.xml"
        ],
    "installable": True
}
