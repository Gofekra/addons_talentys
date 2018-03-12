# -*- encoding: utf-8 -*-

from odoo import fields, models, api

class product_product(models.Model):
    _name = 'product.product'
    _inherit = 'product.product'

    famille = fields.Char('famille', size=64, required=False, readonly=False)
    depot = fields.Char('Dépôt', size=64, required=False, readonly=False)
    prix = fields.Char('prix', size=64, required=False, readonly=False)
    methode_valorisation = fields.Char('Méthode de valorisation', size=64, required=False, readonly=False)
    commentaire  =fields.Text('Commentaire')
    # achat_id = fields.Many2one('purchase.exp.achat', "Demande d'achat", required=False)