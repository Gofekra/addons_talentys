# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from odoo import exceptions
from odoo.tools.translate import _
import time
from itertools import groupby
from urlparse import urljoin
import werkzeug



class type_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.type"
    _description="Type aeronef"
    name=fields.Char('Désignation', size=64, required=True, readonly=False)
 
class chapitre_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.chapitre"
    _description="Chapitre aeronef"

    name = fields.Char('Désignation', size=64, required=True, readonly=False)
 
 
class secteur_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.secteur"
    _description="Secteur aeronef"

    name = fields.Char('Désignation', size=64, required=True, readonly=False)
 
 
class figure_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.figure"
    _description="Figure aeronef"

    name = fields.Char('Désignation', size=64, required=True, readonly=False)

 
 
class page_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.page"
    _description="Page aeronef"

    name = fields.Char('Désignation', size=64, required=True, readonly=False)
 
 
class item_aeronef(models.Model):
    _name="purchase.exp.besoin.aeronef.item"
    _description="Item aeronef"

    name = fields.Char('Désignation', size=64, required=True, readonly=False)
 
 
class product(models.Model):
    _name="product.product"
    _inherit="product.product"
    _description="Produit"

    aeronef_ok = fields.Boolean('Aeronef',
                                help="Détermine si le produit est visible lors du choix du produit sur une ligne de demande d'achat de type Aeronef")


class urgence_besoin(models.Model):
    _name="purchase.exp.besoin.urgence"
    _description="Urgence des besoins"

    name = fields.Char('Urgence', size=64, required=True, readonly=False)


class template_mail_exp(models.Model):
    _name = "purchase.exp.achat.template.mail"
    _description = "Template mail des expressions de besoins"

    name = fields.Selection([('dmde_achat',"Demande d'achat"),
                            ('cotation','Demande de cotation')],'Type',readonly=False,required=True
                           )
    active = fields.Boolean('Active' , default=True)
    dest_ids = fields.One2many('purchase.exp.achat.dest.mail', 'template_id', 'Destinataires', required=False)
    mail = fields.Text('E-mail')


class dest_mail(models.Model):
    _name = "purchase.exp.achat.dest.mail"
    _description = "Destinaires des alertes mails des expressions de besoin"
    

    @api.onchange('name')
    def onchange_employee_id(self):
        if self.employee_id:
            emp = self.env['hr.employee'].browse(self.employee_id.id)
            self.mail =  emp.work_email

    name=fields.Many2one('hr.employee','Employé',required=True)
    template_id = fields.Many2one('purchase.exp.achat.template.mail','Template mail', ondelete='cascade')
    mail = fields.Char('Mail', size=128, required=False, readonly=False)


class urgence(models.Model):
    _name="purchase.exp.besoin.urgence"
    _description="urgence"

    name = fields.Char('Libellé', size=64, required=True, readonly=False)
 
 
class matricule(models.Model):
    _name="purchase.exp.besoin.matricule"
    _description="Matricule Aeronef"

    name = fields.Char('Libellé', size=64, required=True, readonly=False)


class exp_besoin(models.Model):
    _name="purchase.exp.besoin"
    _description="Expression des besoins"
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _order = "name desc"
    
    @api.model
    def create(self, vals):
        pricelist_id = False
        location_id = False
        if vals.get('name','/')=='/':
            vals['name'] = self.env['ir.sequence'].get('purchase.exp.besoin') or '/'

        order = super(exp_besoin, self).create(vals)

        if order.alerte_mail:
            order.send_notification('besoin_draft_notif', self._context)

        return order

    @api.multi
    def copy(self,default=None):
        if not default:
            default = {}

        default.update({
            'date': fields.Datetime.now(),
            'state': 'draft',
            'commentaire_ids': [],
            'quotation_ids': [],
#             'pricelist_id' : self.pool.get('product.pricelist').search(cr, uid, [('type', '=', 'purchase')], context=context)[0],
#             'location_id' : self.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')], context=context)[0],
            'name': self.env['ir.sequence'].get('purchase.exp.besoin'),
        })
        return super(exp_besoin, self).copy(default)

    def _get_remaining_requests(self,qte_dmde,qte_livr):
        if qte_dmde ==0:
            return 0
        return (100*(qte_livr)/qte_dmde) or 0
    

    @api.one
    def _remaining_requests_percent(self):
        res={}
        cr = self._cr
        try :
            
            cr.execute("""SELECT sum(quantite),besoin_id
                        FROM purchase_exp_sortie_detail
                        GROUP BY besoin_id""")
            produits_livres = cr.fetchall()
            
            cr.execute("""SELECT sum(quantite),besoin_id
                        FROM purchase_exp_besoin_detail
                        GROUP BY besoin_id""")
            produits_demandes = cr.fetchall()

            b = 0
            l = 0
            for prod_l in produits_livres :
                for prod_d in produits_demandes :
                    if self.id == prod_l[1] and self.id == prod_d[1]:
                        b = prod_l[0]
                        l = prod_d[0]
            self.remaining_request = self._get_remaining_requests(l,b)
        except ValueError :
            print ""
            raise

    @api.model
    def _template_mail_get(self):
        ids = self.env['purchase.exp.achat.template.mail'].search([('name', '=', 'dmde_achat')])
        if ids:
            return ids[0]
        return False

    @api.onchange('user_id')
    def onchange_user_id(self):
        if not self.user_id:
            return {}
        user = self.env['res.users'].browse(self.user_id.id)
        self.partner_id = user.partner_id

    @api.model
    def _employee_get(self):
        ids = self.env['hr.employee'].search([('user_id', '=', self._uid)])
        if ids:
            return ids[0]
        return False

    @api.model
    def _user_get(self):
        return self._uid

    def get_default(self):
        return self.env['stock.location'].search([('type', '=', 'interne')])[0]

    @api.one
    def get_managers(self):
        dep_obj= self.env['hr.department']
        finance= dep_obj.search([('code', '=', 'FIN')])
        direction= dep_obj.search([('code', '=', 'DG')])
        achat= dep_obj.search([('code', '=', 'ACH')])
        support= dep_obj.search([('code', '=', 'SUPP')])
        if finance :
            self.chief_finance_id= finance[0].manager_id.user_id
        if direction :
            self.dg_id= direction[0].manager_id.user_id
        if achat :
            self.achat_id= achat[0].manager_id.user_id
        if self.type_demande == 'technique' and support:
            self.chief_support_id = support[0].manager_id.user_id

    @api.one
    def _get_url_direct_link(self):
        """
            génère l'url pour accéder directement au à l'expression de besoin en cours
        """
        res = {}
        res['view_type'] = 'form'
        res['model']= 'purchase.exp.besoin'
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        ir_menu_obj = self.env['ir.ui.menu']
        menu_ref_id = False
        try :
            menu_ref_id = self.env['ir.model.data'].get_object_reference('talentys_custom',  'exp_besoin_achat_menu')
            if menu_ref_id :
                menu = ir_menu_obj.search([('id', '=', menu_ref_id[1])])
                res['menu_id']= menu.id
                res['action']= menu.action.id
                res['id']= self.id
            lien = werkzeug.url_encode(res)
            url= urljoin(base_url, "/web/?#%s" % (lien))
            self.url_link = url
        except :
            self.url_link = '#'



    name = fields.Char('Libellé',size=128,required=True,states={'done':[('readonly',True)]} , default='/')
    date  = fields.Date('Date', required=True, help='Date',states={'done':[('readonly',True)]})
    demandeur_id = fields.Many2one('hr.employee', 'Demandeur', required=True, readonly=True,
                                   states={'done':[('readonly',True)]},default=_employee_get, help='Employé en Charge de la demande selectionné automatiquement')
    write_uid = fields.Many2one('res.users', 'User', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True , default=_user_get)
    urgence = fields.Selection([
                          ('normal','Normal'),
                          ('urgent','Urgent'),
                          ], 'Urgence', select=True, readonly=False,states={'done':[('readonly',True)]} , default='normal')
    option = fields.Selection([
                      ('achat','Achat'),
                      ('reparation','Réparation'),
                      ('echange','Echange standard'),
                      ], 'Option', select=True, readonly=False,states={'done':[('readonly',True)]} , default='achat')
    type_demande = fields.Selection([
                      ('general','Général'),
                      ('achat','Général direct'),
                      ('technique','Technique'),
                      ('divers','Dépenses diverses'),
                      ], 'Type de demande', select=True, readonly=True,states={'draft':[('readonly',False)]} , default='divers')
    remaining_request = fields.Float(compute='_remaining_requests_percent', string='Niv. satisfaction (%)')
    date_relance  = fields.Date('Date de relance',states={'done':[('readonly',True)]})
    type_aeronef_id = fields.Many2one('purchase.exp.besoin.aeronef.type', 'Type Aeronef', required=False,states={'done':[('readonly',True)]})
    matricule_id = fields.Many2one('purchase.exp.besoin.matricule', 'Immatriculation', required=False,states={'done':[('readonly',True)]})
    pricelist_id = fields.Many2one('product.pricelist', 'Liste de prix', required=True,states={'done':[('readonly',True)]})
    location_id = fields.Many2one('stock.location', 'Emplacement', required=False,states={'done':[('readonly',True)]}, deafult='get_default')
    description=fields.Text('Description',states={'done':[('readonly',True)]})
    alerte_mail = fields.Boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement un e-mail d'alerte au responsable après la confirmation de la demande d'achat pour validation",states={'done':[('readonly',True)]} , default=True)
    template_mail_id = fields.Many2one('purchase.exp.achat.template.mail','Template mail achat', required=False , default=_template_mail_get)
    detail_besoin = fields.One2many('purchase.exp.besoin.detail', 'besoin_id', 'Détails du besoin', states={'done':[('readonly',True)]})
    # commentaire_ids = fields.One2many('purchase.exp.commentaire','besoin_id', required=False)
    project_id = fields.Many2one('project.project', 'Projet', required=False)
    technician_id = fields.Many2one('res.users', 'Technicien en Charge', required=False)
    technician =  fields.Boolean('Affecté à un technicien')
    # message_ids = fields.One2many('mail.message','res_id','Message',required=False)
    # message_follower_ids = fields.Many2many('mail.message', 'partner_besoin_rel', 'besoin_id', 'partner_id', 'Followers')
    state  =fields.Selection([('draft','Brouillon'),
                            ('confirmed','Soumis'),
                            ('general','Soumis'),
                            ('technique','Soumis'),
                            ('affected','Technicien'),
                            ('technique_ret','Chef Sce Support'),
                            ('service','Chef Sce Support'),
                            ('departement','Chef Dep. Technique'),
                            ('demandeur','Demandeur'),
                            ('transmitted','Transmis'),
                            ('quotation','Attente retour frns.'),
                            ('quotation_conf','Retour frns.'),
                            ('cancel','Annulé'),
                            ('done','Terminé')],'Statut',readonly=True,required=True,states={'done':[('readonly',True)]}, help='Statut du workflow de validation' , default='draft'
                           )
    quotation_ids = fields.One2many('purchase.order', 'besoin_id', 'Cotation', required=False)
    partner_id = fields.Many2one('res.partner', 'Follower',required=True)
    chief_finance_id= fields.Many2one('res.users', 'RAF', compute='get_managers')
    dg_id= fields.Many2one('res.users', 'DG', compute='get_managers')
    achat_id= fields.Many2one('res.users', 'Achat', compute='get_managers')
    chief_service_id = fields.Many2one('res.users',string='Chef Service')
    chief_department_id = fields.Many2one('res.users',string='Chef département')
    url_link = fields.Char("Lien", compute='_get_url_direct_link')
    chief_support_id= fields.Many2one('res.users', 'Chef support', compute='get_managers', store=True)


    

    @api.multi
    def unlink(self):
        sale_orders = self.read(['state'])
        unlink_ids = []
        for s in sale_orders:
            if s['state'] in ['draft', 'cancel']:
                unlink_ids.append(s['id'])
            else:
                raise exceptions.except_orm(_("Avant de supprimer cette demande, veuillez l'annuler ou la mettre en brouillon !"))

        return models.Model.unlink(unlink_ids)
    

    
    @api.multi
    def action_view_quotation(self):
        purchase_ids = self.mapped('quotation_ids')
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


    def show_request(self, requests=None):
        imd = self.env['ir.model.data']
        action = imd.xmlid_to_object('talentys_custom.action_exp_achat_view')
        list_view_id = imd.xmlid_to_res_id('talentys_custom.object_name_tree_view')
        form_view_id = imd.xmlid_to_res_id('talentys_custom.demande_achat_form_view')
        print action

        result = {
            'name': action.name,
            'help': action.help,
            'type': action.type,
            #'views': [[list_view_id, 'tree'], [form_view_id, 'form']],
            'views': [[form_view_id, 'form']],
            'target': action.target,
            'context': action.context,
            'res_model': action.res_model,
            #'res_id':requests.ids,
            'domain':[('id','in',requests.ids)],
        }

        # if len(requests) > 1:
        #     result['domain'] = "[('id','in',%s)]" % requests.ids
        # elif len(requests) == 1:
        #     # result['views'] = [(form_view_id, 'form')]
        #     print requests.ids[0]
        #     #result['res_id'] = requests
        #     result['res_id'] = requests.ids[0]
        # else:
        #     result = {'type': 'ir.actions.act_window_close'}


        if  len(requests) > 1:
            print "ok"
            result['views'] = [(list_view_id, 'tree'),(form_view_id, 'form')]
        elif len(requests) == 1:
            result['res_id'] = requests.ids[0]
            result['views'] = [(form_view_id, 'form')]
        else:
            result = {'type': 'ir.actions.act_window_close'}
        return result

    @api.multi
    def action_view_request(self):
        request_ids = self.env['purchase.exp.achat'].search([('demande_id', '=', self.id)])
        print request_ids.ids
        if request_ids :
            return self.show_request(request_ids)

    @api.one
    def generateQuotation(self):
        purchase_obj = self.env['purchase.order']
        purchase_line_obj= self.env['purchase.order.line']
        order_ids = []
        for partner, lines in groupby(self.detail_besoin, lambda l: l.partner_id):
            if not partner.id:
                raise exceptions.ValidationError("Veuillez renseigner le fournisseur au niveau de l'onglet 'Demande Achat'.")
            print partner
            reference = self.env['ir.sequence'].get('purchase.order')
            vals = {
                'name': reference,
                'date_order': time.strftime('%Y-%m-%d'),
                'state': 'draft',
                'partner_id': partner.id,
                'pricelist_id': self.pricelist_id.id,
                'location_id':self.location_id.id,
                'invoice_method':'order',
                'besoin_id': self.id,
            }
            tmp = list(lines)
            order_line = []
            for line in tmp :
                line_data = {
                    'product_id': line.product_id.id,
                    'product_qty': line.quantite,
                    'product_uom': line.product_id.uom_po_id.id,
                    'name': line.product_id.name,
                    'date_planned': time.strftime('%Y-%m-%d'),
                    'price_unit': 0,
                }
                order_line+=[[0,False, line_data]]
            vals['order_line'] = order_line
            purchase_id = purchase_obj.create(vals)
            order_ids+=[purchase_id]
        return order_ids

    def generatePurchaseRequest(self):
        #reference = self.env['ir.sequence'].next_by_code('purchase.exp.achat')
        request_obj= self.env['purchase.exp.achat']
        request_ids = []

        line_ids = []
        supplier_ids = []
        for partner, lines in groupby(self.detail_besoin, lambda r: r.partner_id):
            tmp = list(lines)
            vals = {
                'name': self.env['ir.sequence'].next_by_code('purchase.exp.achat'),
                'demande_id': self.id,
                'date': time.strftime('%Y-%m-%d'),
                'user_id': self._uid,
                'pricelist_id': self.pricelist_id.id,
                'currency_id': self.pricelist_id.currency_id.id,
                'location_id': self.location_id.id,
                'demandeur_id': self.demandeur_id.id,
                'type_demande': self.type_demande,
                'alerte_mail': self.alerte_mail,
                'state': 'draft',
            }
            # Attribuer le PO à quotation_id(devis fournisseur)
            # quotation_id=None
            # for i in self.quotation_ids:
            #     if i.partner_id.id == partner.id:
            #         vals['quotation_id'] = i.id
            #         quotation_id=i
            #         break
            # # Attribuer le PO à quotation_id(devis fournisseur)
            # if quotation_id:
            line_ids =  [
                    (0, 0, {
                        'partner_id': line.partner_id.id,
                        'product_id': line.product_id.id,
                        'product_qty': line.quantite,
                        'product_uom': line.product_id.uom_po_id.id,
                        'name': line.product_id.name,
                        'date_planned': time.strftime('%Y-%m-%d'),
                        'price_unit': 0.0,
                    })
                    for line in tmp]

            if self.quotation_ids :
                quotation = self.quotation_ids.filtered(lambda r: r.partner_id == partner)
                if quotation :
                    vals['quotation_id'] = quotation.id
                    line_ids =  [
                            (0, 0, {
                                'partner_id': partner.id,
                                'product_id': line.product_id.id,
                                'product_qty': line.product_qty,
                                'product_uom': line.product_uom.id,
                                'name': line.name,
                                'date_planned': time.strftime('%Y-%m-%d'),
                                'price_unit': line.price_unit,
                                'taxe_id': line.taxes_id.id or False,
                                'discount': line.discount,
                            })
                            for line in quotation.order_line]
                    print line_ids

            vals['supplier_id'] = partner.id
            vals['line_det_ids']= line_ids



            request = request_obj.create(vals)
            if request :
                request_ids.append(request.id)
        if request_ids :
            requests = request_obj.browse(request_ids)
            result = self.show_request(requests)
            return result
        else :
            return True

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
        if self.alerte_mail :
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
        lien = self._get_url_direct_link()
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
                #self.chief_purchase_id = department.manager_id.user_id
                self.state = 'transmitted'
            else :
                raise exceptions.MissingError(_("Le Service Achat n'a aucun responsable définit.\nVeuillez le signifier à l'administrateur."))
            if self.alerte_mail :
                result = self.send_notification('besoin_achat_notif', self._context)

    @api.one
    def action_achat(self):

        results = self.generateQuotation()
        if results :
            self.state = 'quotation'

    @api.one
    def action_retour_quotation(self):
        if self.user_id:
            self.state = 'quotation_conf'
        if self.alerte_mail :
            result = self.send_notification('besoin_retour_fournisseur_notif', self._context)



    @api.one
    def action_done(self):
        if self.demandeur_id and  self.demandeur_id.user_id:
            user = self.env.user
            if user == self.demandeur_id.user_id :
                self.state = 'done'
                self.generatePurchaseRequest()
                self.send_notification('request_purchase_draft', self._context)
            else :
                raise exceptions.except_orm(_(u"Seul celui qui a initié la demande peut la valider."))


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
            if self.alerte_mail :
                result = self.send_notification('besoin_service_notif', self._context)

    @api.one
    def action_return_technique(self):
        if self.alerte_mail :
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
            if self.alerte_mail:
                result = self.send_notification('besoin_department_notif', self._context)

    @api.one
    def action_submit_demandeur(self):
        if self.alerte_mail :
            result = self.send_notification('besoin_demandeur_notif', self._context)
            print result
        self.state = 'demandeur'


    _sql_constraints = [
        ('name_uniq', 'unique(name)', _('La reférence doit être unique !')),
    ]

class detail_exp_besoin(models.Model):
    _name="purchase.exp.besoin.detail"
    _description="Détails des expressions de besoins"
    _order = "name desc"

    @api.model
    def _get_remaining_requests(self,s,attendees):
        if s ==0:
            return 0
        return (100*(attendees)/s) or 0
    
    @api.multi
    def _remaining_requests_percent(self):
        res={}
        # selfoin_ids = self.browse(cr,uid,ids,context)
        qte_eb = 0
        qte_da = 0
        for db in self:
            qte_eb += db.quantite
            db.remaining_request = qte_eb
            """for da in besoin.demande_ids:
                for detail in da.demande_id.line_det_ids :
                    if besoin.state == 'confirmed' or besoin.state =='done' :
                        if da.state == 'done' :
                            qte_da += detail.product_qty         
        
            res[besoin.id]=self._get_remaining_requests(qte_eb, qte_da)"""

    @api.multi
    def _get_qte_restante(self):
        for details in self :
            if details.quantite >= details.gave_qty :
                details.qte_restante = details.quantite - details.gave_qty
    
    @api.multi
    def quantite_livree(self):
        cr = self._cr
        cr.execute("""SELECT SUM(ds.quantite),ds.product_id,b.id FROM purchase_exp_sortie AS s,purchase_exp_sortie_detail AS ds, purchase_exp_achat a,purchase_exp_besoin b WHERE a.id=s.achat_id AND s.id=ds.sortie_id AND a.demande_id=b.id GROUP BY ds.product_id,b.id""")
        produits = cr.fetchall()
        
        for detail in self:
            qte = 0
            for prod in produits:
                if detail :
                    if detail.besoin_id.id==prod[2] :
                        if detail.product_id.id==prod[1] :
                                qte=prod[0]
            detail.gave_qty = qte


    name=fields.Integer('Item')
    product_id = fields.Many2one('product.product', 'Désignation', required=True, domain=[('purchase_ok','=',True)])
    quantite  = fields.Integer('Quantité', required=True, help='Quantité de produit demandée par celui qui exprime le besoin' , default=1)
    aeronef_qty = fields.Integer('Qté Aeronef', size=64, required=False, readonly=False)
    magasin_qty = fields.Integer('Qté Magasin', size=64, required=False, readonly=False)
    product_uom =  fields.Many2one('product.uom', 'Unité de mesure', required=True, help='Unité de mesure du produit')
    qte_restante = fields.Integer(compute='_get_qte_restante', string='Qte restante')
    gave_qty = fields.Float(compute='quantite_livree', string='Qté livrée', help='Quantité livrée du produit demandé')
    prix = fields.Float('Prix', required=False)
    partner_id = fields.Many2one('res.partner', 'Fournisseur potentiel', required=False, domain=[('supplier','=',True)], help='Fournisseur potentiel de la demande')
    department_id = fields.Many2one('hr.department', 'Département', required=True)
    periode_affectation = fields.Char("Période d'affectation", size=64, required=False)
    debut_periode = fields.Date('Début période')
    fin_periode =fields.Date('Fin période')
    pb_item = fields.Text('Pb. recontré sur item')
    solution_sub = fields.Text('Solution de sub. éventuelle')
    date_livr_souhaitee = fields.Date('Date livr. souhaitée')
    date_livr_limite = fields.Date('Date livr. limite')
    raison_demande = fields.Text('Raison de la Demande', size=128, required=True)
    type = fields.Char('Type', size=32, required=False, readonly=False)
    type_aeronef_id =fields.Many2one('purchase.exp.besoin.aeronef.type', 'Type Aeronef', required=False)
    chapitre_id = fields.Many2one('purchase.exp.besoin.aeronef.chapitre', 'Chapitre', required=False)
    secteur_id = fields.Many2one('purchase.exp.besoin.aeronef.secteur', 'Secteur', required=False)
    figure_id = fields.Many2one('purchase.exp.besoin.aeronef.figure', 'Figure', required=False)
    page_id = fields.Many2one('purchase.exp.besoin.aeronef.page', 'Page', required=False)
    item_id = fields.Many2one('purchase.exp.besoin.aeronef.item', 'Item', required=False)
    part_number = fields.Char('P/N', size=64, required=False, readonly=False)
    fournisseur_propose = fields.Char('Fournisseur proposé', size=128, required=False, readonly=False)
    adr_fournisseur_propose =fields.Char('Adr. Frs. proposé', size=256, required=False, readonly=False)
    email_fournisseur_propose = fields.Char('E-mail', size=256, required=False, readonly=False)
    etat_stock = fields.Selection([
      ('dispo','Disponible'),
      ('insu','Insuffisant'),
      ('rupture','En rupture'),
      ], 'Etat stock', select=True, readonly=False)
    option_frs =fields.Selection([
      ('existant','Fournisseur existant'),
      ('non_existant','Fournisseur non-existant'),
      ], 'Option', select=True, readonly=False , default='existant')
    visa_livr_stock = fields.Char('Visa livr. sur stock', size=128, required=False)
    proven_item = fields.Char('Provenance item', size=128, required=False)
    note = fields.Text('Caractéristiques techniques')
    besoin_id = fields.Many2one('purchase.exp.besoin', 'Besoin', required=False, ondelete='cascade')
  
    
    @api.one
    def action_create_frs(self):
        obj_frs = self.env['res.partner']
        obj_adr_frs = self.env['res.partner']
        
        fournisseur = {
                   'name': self.fournisseur_propose,
                   'customer': False,
                   'supplier': True
                   }
        id = obj_frs.create(fournisseur)

        adr_fournisseur = {
                       'parent_id': id,
                       'name':self.fournisseur_propose,
                       'type':'default',
                       'street':self.adr_fournisseur_propose,
                       'email':self.email_fournisseur_propose,
                       }
        ida = obj_adr_frs.create(adr_fournisseur)
            
        return self.write({'partner_id':id,})


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            pro = self.env['product.product'].browse(self.product_id.id)
            self.product_uom = pro.uom_id.id

    @api.onchange('date_from' , 'date_to')
    def onchange_date_from(self):
        date_from = self.date_from
        date_to = self.date_to

        if self.date_to and self.date_from:
            self.periode_affectation =  ('Période du %s/%s/%s au %s/%s/%s') % (date_from[8:10],date_from[5:7],date_from[0:4], date_to[8:10],date_to[5:7],date_to[0:4])

# class mail(models.Model):
#     _inherit="mail.message"
#
#     besoin_id = fields.Many2one('purchase.exp.besoin', 'Besoin', required=False)
