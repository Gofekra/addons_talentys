{
    "name": "Talentys Customisations",
    "version": "1.0",
    "depends": ["base","product","hr","purchase","purchase_requisition","sale","stock","project"],
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
    'update_xml': [
                'security/groups.xml',
                'security/ir.model.access.csv',
                #
                # "workflow/wkl_exp_besoin.xml",
                # "workflow/wkl_demande_achat.xml",
                # "workflow/wkl_cotations_groupees.xml",
                #
                # "report/demande_achat_report.xml",
                # "report/bon_sortie_report.xml",
                "reports/layout_template.xml",
		        "reports/report_demande_achat.xml",
                "reports/report_justificatif_da.xml",
                "reports/report_saleorder_talentys.xml",
                "reports/report_view.xml",
                "reports/purchase_order_template.xml",
                "reports/purchase_quotation_templates.xml",
                "reports/report_saleorder_bf.xml",
                "reports/report_bon_livraison_bf.xml",
                "reports/report_account_invoice.xml",
                "wizard/affectedTechnicienView.xml",
                "wizard/paymentCashView.xml",
                # "views/meeting_view.xml",
                # "views/lead_view.xml",
                "views/sale_view.xml",
                'views/purchase_view.xml',
                "views/res_partner_view.xml",
                'views/account_view.xml',
                "views/expression_besoin_view.xml",
                "views/purchase_order_request_view.xml",
                "views/product_view.xml",
                "views/hr_department_view.xml",
                # "views/requisition_view.xml",
                # "views/report_achat_analysis_view.xml",
                # "views/requisition_sequence.xml",
                "views/users_view.xml",
                "views/account_cash_order_view.xml",
                "views/project_view.xml",
                "views/accountAccountView.xml",
                # "wizard/project_wizard_view.xml",
                ],
    'data': [
        'data/requisition_sequence.xml',
        'data/mail_templates.xml',
    ],
    'demo_xml': [],
    'installable': True,
    'active': False,
#    'certificate': 'certificate',
}
