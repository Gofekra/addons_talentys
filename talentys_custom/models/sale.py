# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (http://tiny.be). All Rights Reserved
#    
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see http://www.gnu.org/licenses/.
#
##############################################################################

from odoo import fields, models, api
from odoo.tools.safe_eval import safe_eval
from odoo.tools import Number_To_Word, format_amount

from itertools import groupby

class sale_order(models.Model):
    _inherit='sale.order'
    _order='id desc'

    @api.depends('order_line.price_total')
    def _amount_all(self):
        """
        Compute the total amounts of the SO.
        """
        for order in self:
            amount_untaxed = amount_tax = 0.0
            for line in order.order_line.filtered(lambda l: l.type_line == 'product'):
                amount_untaxed += line.price_subtotal
                # FORWARDPORT UP TO 10.0
                if order.company_id.tax_calculation_rounding_method == 'round_globally':
                    price = line.price_unit * (1 - (line.discount or 0.0) / 100.0)
                    taxes = line.tax_id.compute_all(price, line.order_id.currency_id, line.product_uom_qty, product=line.product_id, partner=order.partner_shipping_id)
                    amount_tax += sum(t.get('amount', 0.0) for t in taxes.get('taxes', []))
                else:
                    amount_tax += line.price_tax
            order.update({
                'amount_untaxed': order.pricelist_id.currency_id.round(amount_untaxed),
                'amount_tax': order.pricelist_id.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })


    picking_delay = fields.Text('Delai de livraison')
    delai_livraison = fields.Date('Delai de livraison')
    duree_validite= fields.Integer('Durée de validité', required=True, default=30)
    da_ids = fields.One2many('purchase.exp.achat', 'sale_id', "Demande d'achat")
    number_of_day = fields.Integer('Delai de livraison')

    @api.multi
    def order_lines_layouted(self):
        """
        Returns this order lines classified by sale_layout_category and separated in
        pages according to the category pagebreaks. Used to render the report.
        """
        self.ensure_one()
        report_pages = [[]]
        for category, lines in groupby(self.order_line, lambda l: l.layout_category_id):
            # If last added category induced a pagebreak, this one will be on a new page
            if report_pages[-1] and report_pages[-1][-1]['pagebreak']:
                report_pages.append([])
            # Append category to current report page
            report_pages[-1].append({
                'name': category and category.name or 'Uncategorized',
                'subtotal': category and category.subtotal,
                'pagebreak': category and category.pagebreak,
                'lines': list(lines)
            })

        return report_pages

    @api.multi
    def getSubtotal(self, line):
        self.ensure_one()
        lines = []
        sequence = line.sequence
        subtotal= self.env['sale.order.line'].search([('order_id', '=', self.id), ('type_line', '=', 'soubtotal')])
        print subtotal
        products = self.env['sale.order.line'].search([('sequence', '<', sequence), ('order_id', '=', self.id)], order='sequence desc')
        print products
        soustotal = 0
        for product in products :
            if product.type_line == 'product':
                soustotal += product.price_subtotal
            elif product.type_line == 'soubtotal':
                return soustotal
            else :
                continue
        return soustotal

    @api.multi
    @api.depends('project_id.project_ids')
    def _compute_project_project_id(self):
         print 'bjr'
    #     for order in self:
    #         order.project_project_id = self.env['project.project'].search([('analytic_account_id', '=', order.project_id.id)])

    def get_amountRemise(self):
        total_amount = 0
        if self.order_line :
            for line in self.order_line :
                if line.discount != 0.0 :
                    tmp = line.price_unit*(line.discount/100)
                    amount = tmp * line.product_uom_qty
                    total_amount += amount
            print total_amount
        return total_amount

    def computeAmount(self, amount):
        amount = format_amount.manageSeparator(amount, digits=0, separator=' ')
        return amount

    def getAmountWithouDiscount(self):
        amount = 0
        if self.order_line :
            for line in self.order_line :
                tmp = line.price_unit * line.product_uom_qty
                amount += tmp
        montant = format_amount.manageSeparator(amount, digits=0, separator=' ')
        return montant

    def amount_to_letter(self, amount):
        letter = ''
        if amount :
            letter = Number_To_Word.Number_To_Word(amount, 'fr', self.currency_id.symbol, '')
        return letter

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'
    _order = 'order_id, sequence, id'

    @api.onchange('prix_gpl', 'remise_fournisseur', 'marge',
                  'frais_approche', 'methode_calcul')
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
            frais_approche= self.frais_approche/100
            value_got_from_methode_calcul = self.methode_calcul._compute_price_unit(
                prix_gpl, remise_fournisseur, marge, frais_approche, discount, tva_percent)
            self.price_unit = value_got_from_methode_calcul[0]['price_unit']



    prix_gpl = fields.Float(string='Prix GPL', required=False)
    remise_fournisseur = fields.Float(
        string="Remise Fournisseur (%)", required=False, default=0.0)
    marge = fields.Float(string="Marge (%)", required=False, default=0.0)
    frais_approche = fields.Float(string="Frais d'approche (%)", required=False, default=0.0)
    methode_calcul = fields.Many2one(
        'sale.order.methode_calcul', required=False, string="Méthode de Calcul")
    product_id = fields.Many2one('product.product', string='Produit', domain=[('sale_ok', '=', True)],
                                 change_default=True, ondelete='restrict', required=False)
    product_uom_qty = fields.Float(string='Quantity', digits=(12,2), required=False, default=1.0)
    product_uom = fields.Many2one('product.uom', string='Unit of Measure', required=False)
    type_line= fields.Selection([('title', 'Titre'), ('product', 'Produit'), ('remark', 'Remarque'), ('line', 'Saut de ligne'),
                ('soubtotal', 'Sous Total')], 'Type de line', default='product', required=True)

class crm_lead(models.Model):
    _inherit='crm.lead'
    _order='create_date desc'


class MethodeCalcul(models.Model):
    _name = 'sale.order.methode_calcul'
    _rec_name = 'libelle'

    @api.one
    def _compute_price_unit(self, prix_gpl=0.0, remise_fournisseur=0.0,
            marge=0.0, frais_approche=0.0, discount=0.0, tva=0.0,  line=None,):
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
                'tva': tva,
                'line': line
            }
            print localdict
            # print "[!] Displaying dictionary we got as parameter: {}".format(
            #     encapsulated_dictionary)
            safe_eval(self.code_python, localdict, mode="exec", nocopy=True)
            print localdict
            if localdict.get('result'):
                print "Erreur"
            else :
                print "ok"
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
