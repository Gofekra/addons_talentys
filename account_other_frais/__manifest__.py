##############################################################################
#
# Copyright (c) 2012 Veone - support.veone.net
# Author: Veone
#
# Fichier du module hr_synthese
# ##############################################################################
{
    "name" : "Frais de timbres",
    "version" : "1.0",
    "author" : "Jean Jonathan ARRA",
    'category': 'Account',
    "website" : "www.arradev.ci",
    "depends" : ["base","account"],
    "description": """ 
    """,
    "init_xml" : [],
    "demo_xml" : [],
    "update_xml" : [
                    'security/ir.model.access.csv',
                    'views/account_other_charges_view.xml',
                    # 'views/AccountInvoiceView.xml',
                    ],
    "data":[
            ],
    "installable": True
}
