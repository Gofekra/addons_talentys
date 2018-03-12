# -*- coding:utf-8 -*-

from odoo import api, fields, _, models, exceptions


class RequestPurchase(models.Model):
    _name='purchase.purchase.request'
    _description= "Gestion des demandes d'achats"
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.depends('line_ids.price_total')
    def _amount_all(self):
        for request in self:
            amount_untaxed = amount_tax = 0.0
            for line in request.line_ids:
                pass
                amount_untaxed += line.price_subtotal
                amount_tax += line.price_tax
            request.update({
                'amount_untaxed': request.currency_id.round(amount_untaxed),
                'amount_tax': request.currency_id.round(amount_tax),
                'amount_total': amount_untaxed + amount_tax,
            })

    @api.depends('user_id')
    def _getEmployee(self):
        if self.user_id :
            employee = self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
            if employee :
                self.demandeur_id = employee

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.purchase.request')
        print vals['name']
        return super(RequestPurchase, self).create(vals)

    def _get_process_view(self):
        type = ''
        if self.type_demande == 'general' :
            type = 'Général'
        elif self.type_demande == 'achat' :
            type = 'Général Direct'
        elif self.type_demande == 'technique' :
            type = 'Technique'
        elif self.type_demande == 'divers' :
            type = 'Dépenses Diverses'

        self.process_view = type

    @api.model
    def default_get(self, fields_list):
        data = models.Model.default_get(self, fields_list)
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.uid)])

        if employee_id :
            data['department_id'] = employee_id.department_id.id

        return data


    name= fields.Char('Référence', size=15, required=True, default='/')
    notif= fields.Boolean('Notif', default=True)
    department_id = fields.Many2one('hr.department', 'Département', readonly=True)
    process_view = fields.Char(compute = _get_process_view)
    type_demande= fields.Selection([('general','Général'),('achat',"Général direct"),('technique','Technique'),
                                    ('divers','Dépenses Diverses')], 'Type de demande', required=True)
    state= fields.Selection([('draft','Brouillon'), ('draft_tech','Brouillon'), ('service','Chef de Service'),
                ('departement','Chef de Département'), ('finance','Finance'), ('ret_finance','Finance'), ('finance_cai','Finance'),
                ('direction','Direction'), ('achat','Achat'), ('caisse','Caisse'), ('commande','Commande'), ('bon','BS émis'),
                ('done','Terminé')],'Statut',required=True,states={'done':[('readonly',True)]}, default='draft', track_visibility='onchange')
    listPrice_id= fields.Many2one('product.pricelist', 'Liste de prix', required=True)
    date= fields.Date('Date', required=False)
    user_id= fields.Many2one('res.users', 'Demandeur', required=True, readonly=True, index=True,
             track_visibility='onchange', default=lambda self: self.env.user)
    demandeur_id= fields.Many2one('hr.employee', 'Demandeur', compute=_getEmployee)
    customer_id= fields.Many2one('res.partner', 'Client', required=False, domain="[('customer', '=', True)]")
    supplier_ids= fields.Many2many('res.partner', 'request_partner_real', 'request_id','supplier_id','Fournisseurs', required=False)
    sale_order_id= fields.Many2one('sale.order', 'Devis client', required=False, domain="[('partner_id', '=', customer_id)]")
    # customer_id= fields.Many2one('res.partner', 'Client', required=False, domain="[('customer', '=', True)]")
    notes= fields.Text('Notes', required=False)
    technicien_id= fields.Many2one("res.users", 'Technicien', required=False, domain="[('is_technicien', '=', True)]")
    chief_service_id= fields.Many2one('res.users', 'Chef de service', required=False)
    chief_department_id= fields.Many2one('res.users', 'Chef de departément', required=False)
    chief_finance_id= fields.Many2one('res.users', 'DAF', required=False)
    dg_id= fields.Many2one('res.users', 'DG', required=False)
    cashier_id= fields.Many2one('res.users', 'Caissier(ère)', required=False)
    achat_id=  fields.Many2one('res.users', 'Responsable Achat', required=False)
    projet = fields.Char('Projet', required=False)
    notes_finances= fields.Text('Commentaire Finance', required=False)
    besoin_id= fields.Many2one('purchase.expression.besoin', 'Expression de besoin', required=True)
    line_ids= fields.One2many("purchase.purchase.request.line", 'purchase_request_id', 'Details')
    comment_ids= fields.One2many('purchase.purchase.request.comment', 'purcahse_request_id', 'Commentaires', required=False)
    amount_untaxed = fields.Monetary(string='Total H.T.', store=False, readonly=True, track_visibility='always', compute=_amount_all)
    amount_tax = fields.Monetary(string='Taxes', store=False, readonly=True, compute=_amount_all)
    amount_total = fields.Monetary(string='Total', store=False, readonly=True, compute=_amount_all)
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  default=lambda self: self.env.user.company_id.currency_id.id)

    def getEmployeeByUser(self, user_id):
        if user_id:
            employee = self.env['hr.employee'].search([('user_id', '=', user_id.id)])
            if employee :
                return employee

    @api.one
    def send_notification(self, email_id, context=None):
        template_id = self.env['ir.model.data'].get_object_reference('talentys_custom',  email_id)
        try :
            mail_templ = self.env['mail.template'].browse(template_id[1])
            result = mail_templ.send_mail(res_id=self.id, force_send=True)
            print result
            return True
        except:
            return False

    @api.one
    def action_draft(self):
        self.state= 'draft'


    @api.one
    def action_confirmed(self):
        # service= self.env['hr.department'].search([('code', '=', 'SUPP')])[0]
        # department= self.env['hr.department'].search([('code', '=', 'INFO')])[0]
        employee= self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        if employee :
            if self.env.user == self.user_id :
                if self.user_id.is_technicien:
                    if employee.parent_id.user_id :
                        self.chief_service_id = employee.parent_id.user_id
                        self.state = 'service'
                    else :
                        raise exceptions.except_orm(_("Veuillez voir avec votre administrateur.\n Aucun utilisateur défini pour l'employé %s."%employee.parent_id.name))
                    if self.notif :
                        self.send_notification('request_service_notif', self._context)
                else:
                    self.action_service()
            else :
                raise exceptions.except_orm(_(u"Seul celui qui a initié la demande peut la soumettre."))

    @api.one
    def action_service(self):
        employee= self.env['hr.employee'].search([('user_id', '=', self.user_id.id)])
        department= self.env['hr.department'].search([('code', '=', 'SUPP')])[0]
        print department
        print employee
        if department:
            if department.manager_id:
                self.chief_department_id = department.manager_id.parent_id.user_id
                self.state = 'departement'
            if self.notif :
                self.send_notification('request_department_notif', self._context)

    @api.one
    def action_department(self):
        finance= self.env['hr.department'].search([('code', '=', 'FIN')])[0]
        if self.env.user == self.chief_department_id:
            if finance and finance.manager_id:
                self.chief_finance_id = finance.manager_id.user_id
                self.state= 'finance'
            if self.notif:
                self.send_notification('request_finance_notif', self._context)
            else:
                raise exceptions.except_orm(_('Veuillez voir avec votre administrateur.\n Aucun responsable financier définit dans le système'))
        else:
            raise exceptions.except_orm(_(u"Seul le responsable du departement %s peut valider la DA à ce niveau." % self.demandeur_id.department_id.name))

    @api.one
    def action_finance(self):
        direction = self.env['hr.department'].search([('code', '=', 'DG')])[0]
        if self.env.user == self.chief_finance_id:
            if direction and direction.manager_id:
                if direction.manager_id.user_id :
                    self.dg_id = direction.manager_id.user_id
                else:
                    raise exceptions.except_orm(_("Veuillez voir avec votre administrateur.\n Aucun utilisateur lié au Directeur."))
                self.state= 'direction'
                if self.notif:
                    self.send_notification('request_dg_notif', self._context)
            else:
                raise exceptions.except_orm(_('Veuillez voir avec votre administrateur.\n Aucun Directeur général définit dans le système.'))
        else :
            raise exceptions.except_orm(_("Seul le responsable des finances peut valider la DA."))

    @api.one
    def action_dg(self):
        if self.env.user == self.dg_id:
            self.state = 'ret_finance'
            if self.notif :
                self.send_notification('request_retour_finance_notif', self._context)
        else :
            raise exceptions.except_orm(_(u'Seul le Directeur Général peut valider la DA à ce niveau.'))

    @api.one
    def action_retour_finance(self):
        cashiers = self.env['res.users'].search([('is_cashier', '=', True)])
        achat= self.env['hr.department'].search([('code', '=', 'ACH')])[0]
        if self.env.user == self.chief_finance_id:
            if self.type_demande == 'divers':
                if cashiers :
                    self.cashier_id = cashiers[0]
                    self.state = 'caisse'
                    if self.notif :
                        self.send_notification('request_cashier_notif', self._context)
            else :
                self.achat_id = achat.manager_id.user_id
                self.state = 'achat'
                if self.notif :
                    self.send_notification('request_achat_notif', self._context)
        else :
            raise exceptions.except_orm(_("Seul le responsable des finances peut valider la DA."))

    @api.one
    def action_caissier(self):
        if self.env.user.is_cashier :
            if self.besoin_id.purchase_ids :
                self.besoin_id.purchase_ids.write({'state':'purchase'})
            self.state= 'done'
        else :
            raise exceptions.except_orm(_("Seul les caissiers peut proceder au paiement de la DA."))

    @api.one
    def action_responsable_achat(self):
        if self.env.user == self.achat_id :
            if self.besoin_id.purchase_ids :
                self.besoin_id.purchase_ids.write({'state':'purchase'})
            self.state = 'done'


class ResquestPurchaseLine(models.Model):
    _name = 'purchase.purchase.request.line'
    _description= "Gestion des lignes de demandes d'achats"

    @api.depends('requested_qty', 'price_unit', 'taxes_id')
    def _compute_amount(self):
        for line in self:
            taxes = line.taxes_id.compute_all(line.price_unit, line.purchase_request_id.currency_id, line.requested_qty, product=line.product_id, partner=line.supplier_id)
            line.update({
                'price_tax': taxes['total_included'] - taxes['total_excluded'],
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    product_id= fields.Many2one('product.product', 'Désignation', required=True)
    uom_id= fields.Many2one('product.uom', 'Unité de mesure', related="product_id.uom_id")
    description_line= fields.Text('Description')
    raison_demande= fields.Text('Raison de la demande', required=True)
    note= fields.Text('Caractéristiques techniques', required=False)
    requested_qty= fields.Float('Quantité demandée', required=True)
    date_livraison_souhaitee= fields.Date('Date de livraison souhaitée', required=False)
    remaining_qty= fields.Float('Quantité livrée', required=False)
    available_qty= fields.Float('Quantité Livrée', required=False)
    supplier_id= fields.Many2one('res.partner', 'Fournisseur potentiel', required=True, domain="[('supplier', '=', True)]")
    department_id= fields.Many2one('hr.department', 'Departement', required=True)
    periode_affection= fields.Char("Période d'affectation", required=False)
    taxes_id = fields.Many2many('account.tax', string='Taxes', domain=[('active', '=', True),('type_tax_use', '=', 'purchase')])
    discount= fields.Float('Remise (%)', required=False, default=0.0)
    price_unit= fields.Float('Prix unitaire', required=False, default=1.0)
    price_subtotal = fields.Monetary(string='Sous Total', store=False, compute=_compute_amount)
    price_total = fields.Monetary(string='Total', store=False, compute=_compute_amount)
    price_tax = fields.Monetary(string='Tax', store=False, compute=_compute_amount)
    purchase_request_id= fields.Many2one('purchase.purchase.request', 'Expression de besoin', required=False)
    currency_id = fields.Many2one('res.currency', 'Currency', related='purchase_request_id.currency_id')

    #compute='_compute_amount',




class PurchasePurchaseRequest(models.Model):
    _name = "purchase.purchase.request.comment"
    _description= "Gestion des commentaires au niveau des demandes d'achat"

    def _getDepartment(self):
        if self.user_id :
            employee = self.env['']


    commentaire= fields.Text('Commentaire', required=True)
    date= fields.Datetime('Date', default=fields.Datetime.now())
    user_id= fields.Many2one('res.users', 'Utilisateur', required=True, default=lambda self: self.env.user)
    department= fields.Char('Departement', compute=_getDepartment, size=255)
    purcahse_request_id= fields.Many2one('purchase.expression.besoin', 'Expression de besoin', requred=False)


