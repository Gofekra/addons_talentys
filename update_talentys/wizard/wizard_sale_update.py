#-*- coding:utf-8 -*-

from odoo import api, models, fields, _


class UpdateSaleOrderLine(models.TransientModel):
    _name= 'update.sale.order.line'

    @api.one
    def updateSaleOrder(self):
        sLine_obj= self.env['sale.order.line']
        lines = sLine_obj.search([])
        print len(lines)
        print lines
        for line in lines :
            prix_revient = 0
            prix_vente = 0
            if not line.methode_calcul :
                prix_revient = line.prix_gpl * (1 + line.frais_approche/100)
                prix_vente = prix_revient / (1 - line.marge_beneficiaire/100)
                price_unit = prix_vente * (1 - line.remise_fournisseur/100)

                print price_unit
                line.write({'price_unit': price_unit})