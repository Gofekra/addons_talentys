# -*- coding:utf-8 -*-

from odoo import api, fields, models, _, exceptions
from urlparse import urljoin
import werkzeug
from datetime import datetime


class ExpressionBesoin(models.Model):
    _name = 'purchase.expression.besoin'
    _description = "Gestion des expressions de besoin"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = 'id desc'

    @api.model
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('purchase.expression.besoin')
        print vals['name']
        return super(ExpressionBesoin, self).create(vals)


    # @api.depends('order_line.invoice_lines.invoice_id.state')
    # def _compute_invoice(self):
    #     for order in self:
    #         invoices = self.env['account.invoice']
    #         for line in order.order_line:
    #             invoices |= line.invoice_lines.mapped('invoice_id')
    #         order.invoice_ids = invoices
    #         order.invoice_count = len(invoices)
    def _get_purchase_count(self):
        if self.purchase_ids :
            # print len(self.purchase_ids)
            self.purchase_count =  len(self.purchase_ids)

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

    @api.one
    def _get_url_direct_link(self):
        """
        	génère l'url pour accéder directement au document en cours
        """
        res = {}
        res['view_type'] = 'form'
        res['model']= 'purchase.request'
        ir_menu_obj = self.env['ir.ui.menu']
        menu_ref_id = False

        try :
            menu_ref_id = self.env['ir.model.data'].get_object_reference('talentys_custom',  'expression_besion_purchase')
            base_url = self.env['ir.config_parameter'].get_param('web.base.url')

            if menu_ref_id :
                menu = ir_menu_obj.search([('id', '=', menu_ref_id[1])])
                res['menu_id']= menu.id
                res['action']= menu.action.id
                res['id']= self.id
            lien = werkzeug.url_encode(res)
            url= urljoin(base_url, "/web/?#%s" % (lien))
            self.url_link = url
            print(url)
        except :

            self.url_link = '#'

    name = fields.Char('Expression de besoin', size=225, required=True, default="/", readonly=True)
    date_expression= fields.Date("Date d'expression", default=fields.Datetime.now, required=True)
    notif = fields.Boolean('Notif', default=True)
    url_link = fields.Char("Lien", compute=_get_url_direct_link)
    department_id = fields.Many2one('hr.department', 'Département', readonly=True)
    type_demande= fields.Selection([('general','Général'),('achat',"Général Direct"),('technique','Technique'),
                                    ('divers','Dépenses Diverses')], 'Type de demande', required=True)
    process_view = fields.Char(compute = _get_process_view)
    urgence= fields.Selection([('normal', 'Normal'),('urgent', 'Urgent')], 'Urgence', required=False)
    listPrice_id= fields.Many2one('product.pricelist', 'Liste de prix', required=True)
    user_id= fields.Many2one('res.users', 'Demandeur', required=True, readonly=True, index=True,
             track_visibility='onchange', default=lambda self: self.env.user)
    technicien_id= fields.Many2one("res.users", 'Technicien', required=False, domain="[('is_technicien', '=', True)]")
    chief_service_id= fields.Many2one('res.users', 'Chef de service', required=False)
    chief_department_id= fields.Many2one('res.users', 'Chef de departément', required=False)
    chief_purchase_id= fields.Many2one('res.users', 'Responsable achats', required=False)
    line_ids= fields.One2many('purchase.expression.besoin.line', 'expression_besoin_id', 'Détails', requred=True, copy=True)
    state= fields.Selection([('draft','Brouillon'), ('confirmed','Soumis'), ('general','Soumis'),
            ('technique','Soumis'), ('affected','Technicien'), ('service_tec','Chef Sce Support'),('technique_ret', 'Chef de Service'),
            ('service','Chef Sce Support'), ('departement','Chef Dep. Technique'), ('demandeur','Demandeur'),('achat', 'Resp. Achat'),
            ('transmitted','Transmis'), ('quotation','Attente retour frns.'), ('quotation_conf','Retour frns.'),
            ('cancel','Annulé'), ('done', 'Terminé')], 'Status', default='draft', required=True, track_visibility = 'onchange')
    purchase_ids= fields.One2many('purchase.order',  'expression_besoin_id', 'Demandes de cotation', required=False)
    purchase_count = fields.Integer('Nombre de cotation', required=False, compute='_get_purchase_count')
    comment_ids= fields.One2many('purchase.expression.besoin.comment','expression_besoin_id', 'Commentaires', required=False)

    @api.multi
    def action_view_quotation(self):
        purchase_ids = self.mapped('purchase_ids')
        print purchase_ids
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('talentys_custom.purchase_form_besoin_action')
        list_view_id = imd.xmlid_to_res_id('purchase.purchase_order_tree')
        form_view_id = imd.xmlid_to_res_id('purchase.purchase_order_form')
        print action

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form'], [False, 'graph'], [False, 'kanban'], [False, 'calendar'], [False, 'pivot']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        if len(purchase_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % purchase_ids.ids
        elif len(purchase_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            print purchase_ids.ids[0]
            result['res_id'] = purchase_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result


    @api.multi
    def action_view_request(self):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('talentys_custom.action_purchase_request1')
        list_view_id = imd.xmlid_to_res_id('talentys_custom.purchase_request_tree_view')
        form_view_id = imd.xmlid_to_res_id('talentys_custom.purchase_request_form_view')
        print action

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
        }
        request_ids = self.env['purchase.purchase.request'].search([('besoin_id', '=', self.id)])
        print request_ids.ids

        if len(request_ids) > 1:
            result['domain'] = "[('id','in',%s)]" % request_ids.ids
        elif len(request_ids) == 1:
            result['views'] = [(form_view_id, 'form')]
            print request_ids.ids[0]
            result['res_id'] = request_ids.ids[0]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result
        # if request_id :
        #     result['views'] = [(form_view_id, 'form')]
        #     result['res_id'] = request_id.id
        # return result

    @api.one
    def generateQuotation(self):
        purchase_obj = self.env['purchase.order']
        purchase_line_obj= self.env['purchase.order.line']
        supplier_ids = list(set(self.line_ids.mapped(lambda r: r.supplier_id.id)))
        order_ids = []
        for supplier_id in supplier_ids :
            vals = {
                'partner_id': supplier_id,
                'date_order': fields.Datetime.now(),
                'expression_besoin_id': self.id,
                'date_planned': fields.Datetime.now(),
            }
            lines = self.line_ids.search([('supplier_id', '=', supplier_id),('expression_besoin_id', '=', self.id)])
            order_line = []
            for line in lines :
                line = {
                    'product_id': line.product_id.id,
                    'product_qty': line.requested_qty,
                    'name': line.product_id.name,
                    'date_planned': line.date_livraison_souhaitee,
                    'price_unit': 0.0,
                    'product_uom': line.uom_id.id
                }
                order_line+=[[0,False, line]]
            vals['order_line'] = order_line
            print vals
            purchase_id = purchase_obj.create(vals)
            order_ids+=[purchase_id]
        return order_ids

    def generatePurchaseRequest(self):
        request_obj= self.env['purchase.purchase.request']
        vals = {
            "besoin_id": self.id,
            "name": self.env['ir.sequence'].next_by_code('purchase.purchase.request') or '/',
            'type_demande': self.type_demande,
            'usr_id': self.user_id.id,
            'technicien_id': self.technicien_id.id,
            'chief_service_id': self.chief_service_id.id,
            'chief_department_id': self.chief_department_id.id,
            'listPrice_id': self.listPrice_id.id,
            'notif': self.notif,
            'date': datetime.today(),
            'state': 'draft'
        }

        line_ids = []
        supplier_ids = []

        #Reporter automatiquement les prix de la cotation fournisseur sur la DA
        for line in self.line_ids:
            vals_line= {
               'supplier_id': line.supplier_id.id,
                    'product_id': line.product_id.id,
                    'description_line': line.description_line,
                    'raison_demande': line.raison_demande,
                    'note': line.note,
                    'price_unit': 0.0,
                    'requested_qty': line.requested_qty,
                    'department_id': line.department_id.id,
            }
            line_ids += [[0, False, vals_line ]]



        if self.purchase_ids :
            for purchase in self.purchase_ids :
                supplier_ids.append(purchase.partner_id.id)
        vals['line_ids']= line_ids
        vals['supplier_ids'] = supplier_ids
        request_id = request_obj.create(vals)
        result = self.action_view_request()





        return result

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
        """
        L'action du workflow qui s'execute lorsqu'une expression de besoin est créée
        :return:
        """
        if self.notif :
            self.send_notification('besoin_draft_notif', self._context)
        self.state = 'draft'

    @api.one
    def action_confirmed(self):
        """
        Action executée lorsqu'un demandeur confirme sa demande d'expression de besoin
        :return:
        si type_demande in (achat, divers) => state = done
        si type_demande = general => state = general
        si type_demande = technique => state = technique
        """
        if self.type_demande in ('achat', 'divers'):
            self.action_done()
        elif self.type_demande == 'general':
            self.state = 'general'
        else :
            self.state = 'technique'

    @api.multi
    def action_transmettre_achat(self):
        # self.ensure_one()
        # self.generateQuotation()
        department= self.env['hr.department'].search([('code', '=', 'ACH')])[0]
        result = False
        if department :
            if department.manager_id.user_id:
                self.chief_purchase_id = department.manager_id.user_id
                self.state = 'transmitted'
            else :
                raise exceptions.MissingError(_("Le Service Achat n'a aucun responsable définit.\nVeuillez le signifier à l'administrateur. "))
            if self.notif :
                result = self.send_notification('besoin_achat_notif', self._context)
                print result

    @api.one
    def action_achat(self):
        results = self.generateQuotation()
        if results :
            self.state = 'quotation'

    @api.one
    def action_retour_quotation(self):

        if self.notif and self.user_id:
            result = self.send_notification('besoin_retour_fournisseur_notif', self._context)
            print result
            self.state = 'quotation_conf'



    @api.one
    def action_done(self):
        if self.user_id.id != self._uid :
            raise exceptions.ValidationError("Désolé, cette action est reservée à l'initiateur de cette demande")
        self.state = 'done'
        self.generatePurchaseRequest()
        self.send_notification('request_purchase_draft', self._context)


    @api.one
    def action_quotation(self):
        self.state = 'quotation'


    @api.multi
    def action_submit(self):
        service= self.env['hr.department'].search([('code', '=', 'SUPP')])[0]
        if self.type_demande == 'technique':
            if service and service.manager_id:
                self.chief_service_id = service.manager_id.user_id
                self.state = 'service'
            else :
                exceptions.except_orm(_("Le service Support n'a aucun manager definit"))
            if self.notif :
                result = self.send_notification('besoin_service_notif', self._context)

    @api.one
    def action_return_technique(self):
        if self.notif :
            result = self.send_notification('besoin_service_notif', self._context)
        self.state = 'technique_ret'

    @api.one
    def action_submit_departmentChef(self):
        department= self.env['hr.department'].search([('code', '=', 'INFO')])[0]
        if self.type_demande == 'technique':
            if department and department.manager_id:
                self.chief_department_id = department.manager_id.user_id
                self.state = "departement"
            else :
                exceptions.except_orm(_("Veuillez renseigner le responsable du departement Informatique"))
            if self.notif:
                result = self.send_notification('besoin_department_notif', self._context)

    @api.one
    def action_submit_demandeur(self):
        if self.notif :
            result = self.send_notification('besoin_demandeur_notif', self._context)
            print result
        self.state = 'demandeur'


class ExpressionBesoinLine(models.Model):
    _name = 'purchase.expression.besoin.line'
    _description = "Gestion des lignes d'expressions de besoin"

    product_id= fields.Many2one('product.product', 'Désignation', required=True)
    uom_id= fields.Many2one('product.uom', 'Unité de mesure', related="product_id.uom_id")
    description_line= fields.Text('Description')
    raison_demande= fields.Text('Raison de la demande', required=True)
    note= fields.Text('Caractéristiques techniques', erquired=False)
    requested_qty= fields.Float('Quantité demandée', required=True)
    date_livraison_souhaitee= fields.Date('Date de livraison souhaitée', required=False)
    remaining_qty= fields.Float('Quantité restante', required=False)
    delivered_qty= fields.Float('Quantité Livrée', required=False)
    supplier_id= fields.Many2one('res.partner', 'Fournisseur potentiel', required=True, domain="[('supplier', '=', True)]")
    department_id= fields.Many2one('hr.department', 'Departement', required=True)
    periode_affection= fields.Char("Période d'affectation", required=False)
    expression_besoin_id= fields.Many2one('purchase.expression.besoin', 'Expression de besoin', required=False)

class PurchaseOrder(models.Model):
    _inherit= "purchase.order"

    expression_besoin_id= fields.Many2one('purchase.expression.besoin', 'Expression de besoin', required=False)

class PurchaseExpressionBesoinComment(models.Model):
    _name = "purchase.expression.besoin.comment"
    _description= "Gestion des commentaires au niveau des expressions de besoin"


    commentaire= fields.Text('Commentaire', required=True)
    user_id= fields.Many2one('res.users', 'Utilisateur', required=True, default=lambda self: self.env.user)
    expression_besoin_id= fields.Many2one('purchase.expression.besoin', 'Expression de besoin', requred=False)
