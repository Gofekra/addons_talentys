# -*- coding:utf-8 -*-

from itertools import groupby
from odoo import models, fields, api
from odoo.tools.safe_eval import safe_eval as eval

from odoo.tools import Number_To_Word


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.onchange('prix_gpl', 'remise_fournisseur', 'marge',
                  'frais_approche', 'methode_calcul', 'discount')
    def _get_price_unit(self):
        if self.methode_calcul:
            tva_percent = 0.0
            if self.tax_id:
                for tax in self.tax_id:
                    if tax.type == 'tva':
                        tva_percent = tax.amount/100
            print tva_percent
            prix_gpl = self.prix_gpl
            remise_fournisseur = self.remise_fournisseur/100
            marge = self.marge/100
            discount= self.discount/100
            frais_approche= self.frais_approche /100
            value_got_from_methode_calcul = self.methode_calcul._compute_price_unit(
                prix_gpl, remise_fournisseur, marge, frais_approche, discount, tva_percent)
            self.price_unit = value_got_from_methode_calcul[0]['price_unit']



    prix_gpl = fields.Float(string='Prix GPL', required=False)
    remise_fournisseur = fields.Float(
        string="Remise Fournisseur (%)", required=False, default=0.0)
    marge = fields.Float(string="Marge (%)", required=False, default=0.0)
    frais_approche = fields.Float(
        string="Frais d'approche (%)", required=False, default=0.0)
    methode_calcul = fields.Many2one(
        'sale.order.methode_calcul', required=False, string="Méthode de Calcul")
    product_uom_qty = fields.Float(string='Quantity', digits=(12,2), required=True, default=1.0)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.depends('amount_total')
    def get_amount_letter(self):
        if self.amount_total :
            amount_letter = Number_To_Word.Number_To_Word(self.amount_total, 'fr', self.currency_id.symbol, '')
            self.amount_total_letter = amount_letter

    amount_total_letter= fields.Char('Montant total en lettre', required=False, compute='get_amount_letter')
    # method_payment= fields.Selection([('espece', 'Espèces'),('cheque', 'Chèques')], '')


    @api.multi
    def _get_tax_amount_by_type(self, type):
        self.ensure_one()
        result = self._get_tax_amount_by_group()
        if type :
            for res in result :
                if res[0] == type :
                    return res[1]
        else :
            return 0



class SaleLayoutCategory(models.Model):
    _inherit = 'sale.layout_category'

    account_other_charge_id= fields.Many2one('account.other.charge', 'Autres charges')

class MethodeCalcul(models.Model):
    _name = 'sale.order.methode_calcul'
    _rec_name = 'libelle'

    @api.one
    def _compute_price_unit(self, prix_gpl=0.0, remise_fournisseur=0.0,
                            marge=0.0, frais_approche=0.0, discount=0.0, tva=0.0):
        data = {}
        if self.type_methode == 'pourcentage':
            print self.type_methode
            data['price_unit'] = 0
        elif self.type_methode == 'fixed':
            data['price_unit'] = 0
            print self.type_methode
        elif self.type_methode == 'code_python':
            localdict = {
                'prix_gpl': prix_gpl,
                'remise_fournisseur': remise_fournisseur,
                'marge': marge,
                'frais_approche': frais_approche,
                'discount': discount,
                'tva': tva
            }
            # print "[!] Displaying dictionary we got as parameter: {}".format(
            #     encapsulated_dictionary)
            eval(self.code_python, localdict, mode="exec", nocopy=True)
            print "[! ] Before returning, got data_to_return: {}".format(localdict)
            data['price_unit'] = localdict['result']
        return data

    libelle = fields.Char(string='Methode Calcul', required=True)
    type_methode = fields.Selection(
        [('pourcentage', 'Pourcentage'), ('fixed', 'Fixé'),
         ('code_python', 'Code Python')], string='Type Méthode',
        default='code_python')
    code_python = fields.Text(string="Code Python", required=True,
                              default="""# prix_gpl: prix GPL
#remise_fournisseur: remise fournisseur
#marge : Marge
#frais_approche: Frais d'approche
#discount: discount
#tva: TVA
#result = 0.0""")