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
from odoo.tools import Number_To_Word, format_amount

class account_invoice(models.Model):
    _inherit='account.invoice'

    @api.one
    def _get_dg(self):
        hr_obj = self.env['hr.department']
        hr = hr_obj.search([('code','=','DG')])
        if hr:
            self.dg_name = hr.manager_id.name


    @api.one
    def _get_total_discount(self):
        disc = 0
        for line in self.invoice_line_ids :
            disc += line.price_subtotal * line.discount/100
        self.total_discount = disc

    @api.one
    def _get_order_origin(self):
        order_id = False
        order_ids = self.env['sale.order'].search([('name','=',self.origin)])
        if order_ids:
            order_id = order_ids[0]
        else :
            order_id = 10
        self.order_id = order_id

    @api.one
    def _get_advance_amount(self):
        acompte = 0
        for line in self.invoice_line_ids :
            if line.price_unit < 0 :
                acompte += -line.price_unit
        self.acompte = acompte

    @api.multi
    @api.depends('order_id')
    def _get_taux(self):
        for inv in self :
            taux = 0.0
            if inv.amount_total!=0 and inv.order_id :
                taux = (inv.amount_total / inv.order_id.amount_total)* 100
            inv.taux_acompte = taux

    @api.multi
    @api.depends('order_id')
    def get_total_acompte_paye(self):
        total_acompte = 0
        for inv in self:
            if inv.order_id :
                invs= self.search([('id', '!=',inv.id), ('id', 'in', inv.order_id.invoice_ids.ids),('date_invoice', '<', inv.date_invoice)])
                if invs :
                    total_acompte = sum([i.amount_total for i in invs])
            inv.total_acompte = total_acompte

    @api.multi
    def _get_net_paye(self):
        for inv in self:
            net = 0
            if inv.order_id :
                total_acompte = inv.total_acompte+ inv.amount_total
                print total_acompte
                net = inv.order_id.amount_total - total_acompte
                print net
            inv.net_paie = net

    @api.one
    @api.depends('net_paie')
    def _get_amount_total_letter(self):
        if self.net_paie:
            self.amount_total_letter = Number_To_Word.Number_To_Word(self.net_paie, 'fr', self.currency_id.symbol, '')
            print self.amount_total_letter

    @api.one
    @api.depends('amount_total')
    def _get_amount_to_letter(self):
        if self.amount_total:
            self.amount_letter = Number_To_Word.Number_To_Word(self.amount_total, 'fr', self.currency_id.symbol, '')
            print self.amount_total_letter





    type_facture = fields.Selection([
                          ('acompte','Acompte'),
                          ('acompte_exo','Acompte exonéré'),
                          ('solde','Solde 1'),
                          ('solde2','Solde 2'),
                          ('solde_exo','Solde exonéré'),
                          ('exoneration','Exonération de taxe'),
                          ('avoir','Avoir'),('normal', 'Normal')
                           ],    'Type', select=True, readonly=False, default='normal')

    taux_acompte = fields.Float(compute='_get_taux', string='Taux accompte',  digits=(10,2))
    taux_solde = fields.Float('Taux solde')
    total_acompte= fields.Float(compute='get_total_acompte_paye', string='Total acompte', )
    acompte = fields.Float(compute='_get_advance_amount', string='Montant acompte')
    net_paie= fields.Float('Net à payer', compute='_get_net_paye')
    amount_total_letter = fields.Char(compute='_get_amount_total_letter')
    amount_letter = fields.Char(compute='_get_amount_to_letter')
    montant_solde = fields.Float('Montant solde')
    mode_paiement =  fields.Selection([
                          ('cheque','Chèque'),
                          ('espece','Espèce'),
                          ('virement','Virement'),
                           ],    'Mode de paiement', select=True, readonly=False)
    total_discount =  fields.Float(compute='_get_total_discount', string='Remise totale')
    order_id =  fields.Many2one('sale.order',compute='_get_order_origin',string='Bon de commande')
    dg_name = fields.Char('DG',compute='_get_dg')

    def convert_amount(self, amount):
        if amount :
            f_amount = format_amount.manageSeparator(amount, digits=0, separator=' ')
            print f_amount
            return f_amount


class AccountAnalyticAccount(models.Model):
    _inherit= "account.analytic.account"

    parent_id= fields.Many2one('account.analytic.account', "Parent", required=False, domain="[('type', '=', 'view')]")
    type= fields.Selection([('view', 'Vue'),('normal', 'Normal')], 'Type de compte')
