# -*- coding: utf-8 -*-
from odoo import tools
from odoo import fields, models, api
from odoo.addons.decimal_precision.models.decimal_precision import DecimalPrecision as dp
from odoo.tools.translate import _
from odoo import registry
from odoo import SUPERUSER_ID
from odoo import service
class report_achat_analysis(models.Model):
    _name = "report.achat.analysis"
    _description = "Analyse des ordres d'achat"
    _auto = False

    name = fields.Char('Désignation', size=256, readonly=True)

    product_qty = fields.Float('Qté dmdée', readonly=True)

    date_planned = fields.Datetime('Date', select=True, readonly=True)
    product_uom = fields.Many2one('product.uom', 'Product UOM', help='Unité de mesure du produit', readonly=True)
    product_id =  fields.Many2one('product.product', 'Produit', domain=[('purchase_ok','=',True)], change_default=True, readonly=True)
    price_unit = fields.Float('Unit Price', readonly=True)
    partner_id = fields.Many2one('res.partner', 'Fournisseur potentiel', domain=[('supplier','=',True)], help='Fournisseur potentiel de la demande', readonly=True)
    notes = fields.Text('Notes')
    demande_id = fields.Many2one('purchase.exp.achat', 'Demande', readonly=True)

    # Classe purchase_exp_achat_detail inexistante
    # def init(self):
    #     tools.drop_view_if_exists(self._cr, 'report_achat_analysis')
    #     self._cr.execute(""" CREATE OR REPLACE VIEW report_achat_analysis AS (
    #                     SELECT
    #                            min(d.id) as id,
    #                            d.product_id as product_id,d.product_qty as product_qty, d.date_planned as date_planned, d.product_uom as product_uom,
    #                            d.price_unit * d.product_qty as price_unit, d.partner_id as partner_id, d.demande_id as demande_id
    #                     FROM
    #                            purchase_exp_achat_detail d
    #                     LEFT JOIN
    #                            product_product p ON (d.product_id=p.id)
    #                     GROUP BY
    #                            d.product_id, d.product_qty, d.date_planned, d.product_uom,
    #                            d.price_unit, d.partner_id, d.demande_id
    #                     );
    #     """)