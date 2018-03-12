# -*- encoding: utf-8 -*-

from odoo import tools
from odoo import fields, models, api
from odoo import netsvc
from odoo.tools.translate import _
from datetime import datetime
from odoo import exceptions
import time
import werkzeug
from urlparse import urljoin


class demande_achat(models.Model):
    _name="purchase.exp.achat"
    # _logger = netsvc.Logger()
    _inherit = ['mail.thread', 'ir.needaction_mixin']
    _description="Demande d'achat"
    _order = "name desc"
    
    @api.multi
    def _get_montant_achat(self) :
        res={}
        for achat in self :
            cpt=0
            for det in achat.line_det_ids :
                cpt += det.subtotal
            achat.mtt_achat = cpt


    @api.onchange('quotation_id')
    def onchange_quotation_id(self):
        if  self.quotation_id:
            self.pricelist_id= self.quotation_id.pricelist_id
        else :
            self.pricelist_id = False
        
    @api.onchange('sale_id')
    def onchange_sale_id(self):
        if not self.sale_id:
            return {}
        self.sale_pricelist_id= self.sale_id.pricelist_id.id
    
    def _user_mail_get(self):
        self.email_user= self.user_id.login
    

    @api.multi
    def _get_devise(self):
        res={}
        for achat in self :
            achat.devise = achat.pricelist_id.currency_id.symbol

    @api.multi
    def _get_amount_untaxed(self):
        for achat in self :
            amount_untaxed = 0.00
            for line in achat.line_det_ids :
                amount_untaxed += line.subtotal
            achat.amount_untaxed = amount_untaxed
        
    @api.multi
    def _get_amount_tax(self):
        for achat in self:
            amount_tax = 0.00
            for line in achat.line_det_ids :
                if line.taxe_id :
                    amount_tax += line.subtotal * line.taxe_id.amount/100
            achat.amount_tax = amount_tax
        

    @api.multi
    def _get_amount_total(self):
        for achat in self :
            amount_untaxed = 0.00
            amount_tax = 0.00
            for line in achat.line_det_ids :
                amount_untaxed += line.subtotal
                if line.taxe_id :
                    amount_tax += line.subtotal * line.taxe_id.amount/100
            achat.amount_total = amount_untaxed + amount_tax

    @api.one
    def get_managers(self):
        dep_obj= self.env['hr.department']
        finance= dep_obj.search([('code', '=', 'FIN')])
        direction= dep_obj.search([('code', '=', 'DG')])
        achat= dep_obj.search([('code', '=', 'ACH')])
        cashier_id= self.env['res.users'].search([('is_cashier', '=', True)])
        support= dep_obj.search([('code', '=', 'SUPP')])
        if finance :
            self.chief_finance_id= finance[0].manager_id.user_id
        if direction :
            self.dg_id= direction[0].manager_id.user_id
        if achat :
            self.achat_id= achat[0].manager_id.user_id
        if cashier_id :
            self.cashier_id = cashier_id
        if self.type_demande == 'technique' and support:
            self.chief_support_id = support[0].manager_id.user_id

    @api.one
    def _get_url_direct_link(self):
        """
            génère l'url pour accéder directement au à l'expression de besoin en cours
        """
        res = {}
        res['view_type'] = 'form'
        res['model']= self._name
        base_url = self.env['ir.config_parameter'].get_param('web.base.url')
        ir_menu_obj = self.env['ir.ui.menu']
        menu_ref_id = False
        try :
            menu_ref_id = self.env['ir.model.data'].get_object_reference('talentys_custom',  'exp_demande_achat_menu')
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

    name = fields.Char('Référence',size=128,required=True,states={'done':[('readonly',True)]}, default='/')
    date = fields.Date('Date', help='Date',states={'done':[('readonly',True)]})
    date_prevue = fields.Datetime('Date', help='Date prévue',states={'done':[('readonly',True)]})
    demandeur_id = fields.Many2one('hr.employee', 'Demandeur', required=False, readonly=True, help='Employé en charge de la demande Selectionné automatiquement')
    supplier_id = fields.Many2one('res.partner', 'Fournisseur', required=False)
    customer_id = fields.Many2one('res.partner', 'Client', required=False)
    user_id = fields.Many2one('res.users', 'Validateur', required=False)
    pricelist_id = fields.Many2one('product.pricelist', "Liste de prix d'achat", required=True,states={'done':[('readonly',True)]})
    location_id = fields.Many2one('stock.location', 'Emplacement source', required=False,states={'done':[('readonly',True)]})
    location_dest_id = fields.Many2one('stock.location', 'Emplacement destination', required=False,states={'done':[('readonly',True)]})
    notes = fields.Text('Commentaires',states={'done':[('readonly',True)]})
    projet =  fields.Char('Projet')
    line_det_ids = fields.One2many('purchase.exp.achat.detail', 'demande_id', 'Détail demande', required=False,states={'done':[('readonly',True)]})
    bon_sortie_ids = fields.One2many('purchase.exp.sortie', 'achat_id', 'Bon de sortie',states={'done':[('readonly',True)]})
    commentaire_ids = fields.One2many('purchase.exp.commentaire','order_id', required=False)
    demande_id = fields.Many2one('purchase.exp.besoin', 'Référence du Besoin', required=False, ondelete="cascade", readonly=True)
    quotation_id = fields.Many2one('purchase.order', 'Devis Fournisseur', required=False, states={'done':[('readonly',True)]})
    sale_id = fields.Many2one('sale.order', 'Devis Client', required=False, states={'done':[('readonly',True)]})
    alerte_mail = fields.Boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement un e-mail d'alerte au responsable après la confirmation de la demande d'achat pour validation",states={'done':[('readonly',True)]})
    mail_user = fields.Char(compute='_user_mail_get',type='char', string='Mail user')
    notes_finance = fields.Text('Commentaires finance',states={'done':[('readonly',True)]})
    devise = fields.Char(compute='_get_devise',string='Devise')
    currency_id = fields.Many2one("res.currency" , related='pricelist_id.currency_id' , string="Currency", readonly=True, required=True)
    dg = fields.Boolean('DG')
    finance =fields.Boolean('Finance')
    amount_untaxed = fields.Float(compute='_get_amount_untaxed', string='Montant hors-taxe')
    amount_tax =  fields.Float(compute='_get_amount_tax',string='Taxe')
    amount_total = fields.Float(compute='_get_amount_total',string='Total')
    chief_finance_id= fields.Many2one('res.users', 'RAF', compute='get_managers')
    dg_id= fields.Many2one('res.users', 'DG', compute='get_managers')
    achat_id= fields.Many2one('res.users', 'Achat', compute='get_managers')
    cashier_id= fields.Many2one('res.users', 'Caissier(ière)', compute='get_managers')
    chief_support_id= fields.Many2one('res.users', 'Chef support', compute='get_managers')
    type_demande = fields.Selection([
      ('general','Général'),
      ('achat','Général direct'),
      ('technique','Technique'),
      ('divers','Dépenses diverses'),
      ], 'Type de demande', select=True, readonly=True,states={'done':[('readonly',True)]})
    mtt_achat = fields.Float(compute='_get_montant_achat',
                                    string='Montant', help='Montant évalué du besoin')
    state = fields.Selection([('draft','Brouillon'),
                                ('draft_tech','Brouillon'),
                                ('service','Service'),
                                ('departement','Département'),
                                ('finance','Finance'),
                                ('finance_ach','Finances'),
                                ('finance_cai','Finances'),
                                ('direction','Direction'),
                                ('ret_finance', 'Finances'),
                                ('achat','Achat'),
                                ('caisse','Caisse'),
                                ('commande','Commande'),
                                ('bon','BS émis'),
                                ('done','Terminé')],'Statut',readonly=True,required=True,states={'done':[('readonly',True)]})
    #message_ids = fields.One2many('mail.message','res_id','Message',required=False)
    chief_department_id = fields.Many2one('res.users', string='Chef département')
    url_link = fields.Char("Lien", compute='_get_url_direct_link')
    # message_follower_ids = fields.Many2many('mail.message', 'partner_achat_rel', 'achat_id', 'partner_id',
    #                                          'Followers')
    
    # _sql_constraints = [
    #     ('name_uniq', 'unique(demande_id)', "La reférence de l'expression de besoin doit être unique"),
    # ]

    @api.model
    def _user_get(self):
        return self._uid

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
        if self.demandeur_id and  self.demandeur_id.user_id:
            user = self.env.user
            if user == self.demandeur_id.user_id :
                if self.demandeur_id.service_id :
                    if self.demandeur_id.service_id.manager_id != self.demandeur_id  :
                        print 'o cool'
                        if self.demandeur_id.parent_id.user_id :
                            self.state = 'service'
                        else :
                            raise exceptions.except_orm(_("Veuillez voir avec votre administrateur.\n Aucun utilisateur défini pour l'employé %s."%self.demandeur_id.parent_id.name))
                        if self.alerte_mail :
                            self.send_notification('request_service_notif', self._context)
                    else:
                        self.action_service()
                else : self.action_service()
            else :
                raise exceptions.except_orm(_(u"Seul celui qui a initié la demande peut la soumettre."))

    @api.one
    def action_service(self):
        department= self.demandeur_id.department_id
        if department:
            if department.manager_id:
                self.chief_department_id = department.manager_id.user_id
                self.state = 'departement'
            if self.alerte_mail :
                self.send_notification('request_department_notif', self._context)

    @api.one
    def action_department(self):
        finance= self.env['hr.department'].search([('code', '=', 'FIN')])[0]
        if self.env.user == self.demandeur_id.department_id.manager_id.user_id:
            if finance and finance.manager_id:
                self.state= 'finance'
            else:
                raise exceptions.except_orm(_('Veuillez voir avec votre administrateur.\n Aucun responsable financier définit dans le système'))
            if self.alerte_mail:
                self.send_notification('request_finance_notif', self._context)
        else:
            raise exceptions.except_orm(_(u"Seul le responsable du departement %s peut valider la DA à ce niveau." % self.demandeur_id.department_id.name))

    @api.one
    def action_finance(self):
        direction = self.env['hr.department'].search([('code', '=', 'DG')])[0]
        finance = self.env['hr.department'].search([('code', '=', 'FIN')])[0]
        if finance and self.env.user == finance.manager_id.user_id:
            if direction and direction.manager_id:
                if not direction.manager_id.user_id :
                    raise exceptions.except_orm(_("Veuillez voir avec votre administrateur.\n Aucun utilisateur lié au Directeur."))
                self.state= 'direction'
                if self.alerte_mail:
                    self.send_notification('request_dg_notif', self._context)
            else:
                raise exceptions.except_orm(_('Veuillez voir avec votre administrateur.\n Aucun Directeur général définit dans le système.'))
        else :
            raise exceptions.except_orm(_("Seul le responsable des finances peut valider la DA."))

    @api.one
    def action_dg(self):
        direction = self.env['hr.department'].search([('code', '=', 'DG')])[0]
        if direction and self.env.user == direction.manager_id.user_id:
            self.state = 'ret_finance'
            if self.alerte_mail :
                self.send_notification('request_retour_finance_notif', self._context)
        else :
            raise exceptions.except_orm(_(u'Seul le Directeur Général peut valider la DA à ce niveau.'))

    @api.one
    def action_retour_finance(self):
        cashiers = self.env['res.users'].search([('is_cashier', '=', True)])
        achat= self.env['hr.department'].search([('code', '=', 'ACH')])[0]
        finance = self.env['hr.department'].search([('code', '=', 'FIN')])[0]
        if self.env.user == finance.manager_id.user_id:
            if self.type_demande == 'divers':
                if cashiers :
                    self.state = 'caisse'
                    if self.alerte_mail :
                        self.send_notification('request_cashier_notif', self._context)
                else :
                    raise exceptions.except_orm(_("Il n'existe aucun(ne) caisser(ière) dans le système."))
            else :
                self.state = 'achat'
                if self.alerte_mail :
                    self.send_notification('request_achat_notif', self._context)
        else :
            raise exceptions.except_orm(_("Seul le responsable des finances peut valider la DA."))

    @api.one
    def action_caissier(self):
        if self.env.user.is_cashier :
            print "Juste pour le test"
#            if self.besoin_id.purchase_ids :
#                self.besoin_id.purchase_ids.write({'state':'purchase'})
            self.state= 'done'
        else :
            raise exceptions.except_orm(_("Seul les caissiers peut proceder au paiement de la DA."))

    @api.one
    def action_responsable_achat(self):
        purch_obj= self.env['purchase.order']
        achat= self.env['hr.department'].search([('code', '=', 'ACH')])[0]
        if self.env.user == achat.manager_id.user_id :
            if self.type_demande in ('general','technique'):
                if self.quotation_id :
                    self.quotation_id.write({'state':'purchase'})
                    self.state = 'done'
                else :
                    raise exceptions.except_orm(_("La demande d'achat ne contient aucune quotation."))
            else:
                #raise exceptions.except_orm(_("type non general et technique."))
                self.state = 'done'

        else:
            raise exceptions.except_orm(_("Seul le responsable achat peut faire cette action."))



    @api.onchange('quotation_id')
    @api.depends('quotation_id')
    def onChangeQuotation(self):
        if self.quotation_id :
            for line in self.line_det_ids :
                qline = self.quotation_id.order_line.filtered(lambda r: r.product_id == line.product_id)
                if qline :
                    line.taxe_id = qline.taxes_id.id or False
                    line.price_unit = qline.price_unit
                    line.discount = qline.discount
    
    _defaults={
               'user_id':_user_get,
               'date':time.strftime('%Y-%m-%d'),
               #'state':'draft', 
               #'alerte_mail':True,
               'notes': "La présente demande s'inscrit dans le cadre de...",
               'location_dest_id':lambda obj, cr, uid, conText: obj.pool.get('stock.location').search(cr, uid, [('name', '=', 'Output')], conText=conText)[0],
               }


class detail_demande_achat(models.Model):
    _name="purchase.exp.achat.detail"
    _description="Détail demande d'achat"


    @api.multi
    def _get_quantite(self):
        for s in self:
            s.available_qty= s.product_id.qty_available

    @api.multi
    def _get_quantite_cmde(self):
        res={}
        self._cr.execute("SELECT sum(product_qty),product_id,state FROM  purchase_order_line WHERE state='confirmed' GROUP BY product_id,state")
        produits = self._cr.fetchall()

        for det in self:
            qte = 0
            for prod in produits:
                if det.product_id.id==prod[1] :
                    qte=prod[0]
            det.ordered_qty = qte

    @api.multi
    def quantite_livree(self):
        self._cr.execute("""SELECT SUM(ds.quantite),ds.product_id,a.id FROM purchase_exp_sortie AS s,purchase_exp_sortie_detail AS ds, purchase_exp_achat a,purchase_exp_besoin b WHERE a.id=s.achat_id AND s.id=ds.sortie_id AND a.demande_id=b.id GROUP BY ds.product_id,a.id""")
        produits = self._cr.fetchall()
        
        for detail in self:
            qte = 0
            for prod in produits:
                if detail :
                    if detail.demande_id.id==prod[2] :
                        if detail.product_id.id==prod[1] :
                                qte=prod[0]
            detail.gave_qty= qte


    @api.model
    def _check_qte_livree(self):
        if self.product_qty < self.gave_qty :
            return False
        return True

    @api.model
    def _check_qte_null(self):
        res={}
        if self.product_qty ==0 :
            return False
        return True

    @api.multi
    def _get_sub_total(self):
        remise = 0.00
        subtotal = 0.00
        taxe = 0.00
        for i in self:
            if i.taxe_id :
                taxe = i.taxe_id.amount
            remise = i.discount
            subtotal= i.price_unit * (1 - remise/100) * i.product_qty
            i.subtotal= subtotal


    name = fields.Char('Désignation', size=256, required=True)
    product_qty = fields.Float('Qté dmdée', required=True , default=1)
    available_qty = fields.Float(compute='_get_quantite',string='Qté dispo.', help='Quantité réelle du produit disponible en stock')
    ordered_qty = fields.Float(compute='_get_quantite_cmde',string='Qté cmdée.', help='Quantité commandée du produit demandé')
    gave_qty = fields.Float(compute='quantite_livree',string='Qté livrée', help='Quantité livrée du produit demandé')
    date_planned = fields.Date('Date', required=True, select=True)
    product_uom = fields.Many2one('product.uom', 'Product UOM', required=True, help='Unité de mesure du produit')
    product_id = fields.Many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True)
    price_unit = fields.Float('Prix unitaire', required=True)
    taxe_id = fields.Many2one('account.tax','Taxe', domain=[('type_tax_use','in',('purchase','all'))])
    partner_id = fields.Many2one('res.partner', 'Fournisseur potentiel', required=False, domain=[('supplier','=',True)],
                                 help='Fournisseur potentiel de la demande')
    notes= fields.Text('Notes')
    demande_id = fields.Many2one('purchase.exp.achat', 'Demande', required=False, ondelete='cascade')
    discount = fields.Float('Remise (%)')
    subtotal = fields.Float(compute='_get_sub_total',string="Sous-Total")


    _constraints=[(_check_qte_livree,"La quantité de produit à livrer ne peut être supérieure à la quantité initiale demandée",['product_qty'])]
    # _constraints=[(_check_qte_null,"Les quantités nulles ne sont pas admises",['product_qty'])]


class bon_sortie(models.Model):
    _name="purchase.exp.sortie"
    _description="Bon de sortie"
    _order = 'name desc'
    
    def _receveur_get(self, cr, uid,ids, conText=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            id_ach = 6
            
        cr.execute("""SELECT demandeur_id FROM purchase_exp_achat WHERE id=%s""",str(id_ach))
        demandeur = cr.fetchall()
        for s in self.browse(cr,uid,ids) :
            for d in demandeur :
                res[s.id]=d[0]
        return res

    
    def _check_state(self,cr,uid,ids,conText=None):
        for s in self.browse(cr,uid,ids) :
            if s.achat_id.state == "confirmed" :
                return False
        return True
    
    
    def _check_produits(self,cr,uid,ids,conText=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            id_achat = s.achat_id.id

        cr.execute("""SELECT product_id,b.id FROM purchase_exp_achat_detail AS pd, purchase_exp_achat AS pa,purchase_exp_besoin b WHERE pa.id=pd.demande_id AND pa.demande_id=b.id""")
        prod = cr.fetchall()
        
        for bon in self.browse(cr,uid,ids) :
            if bon.achat_id.id == id_achat :
                for d in bon.det_sortie_ids :
                    cpt=0
                    for p in prod :
                        if d.product_id.id == p[0] :
                            cpt+=1              
                    if cpt == 0 :
                        return False
            if bon.achat_id.state != "confirmed" and bon.achat_id.state != "cotation" :
                return False
            
            return True                
    
    
    def get_inputs(self, cr, uid,ids, conText=None):
        res=[]
        for bon in self.browse(cr,uid,ids) :
                inputs = {
                       'product_id':1,
                       'quantite':1,
                       }
                res += [inputs]
        return res
    
    
    def onchange_achat_id(self, cr, uid, ids, achat_id):
        if not achat_id:
            return {}
        ach = self.pool.get('purchase.exp.achat').browse(cr, uid, achat_id)
        input_line_ids = self.get_inputs(cr, uid,ids)
        return {'value': {    
                            'receveur_id': ach.demandeur_id.id,
                            'det_sortie_ids':input_line_ids
                        },
        }

    

    name = fields.Char('Référence', size=64, required=True, readonly=False , default=lambda obj, cr, uid, conText: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.exp.sortie'))
    datetime = fields.Datetime('Date',required=True , default=time.strftime('%Y-%m-%d %H:%M:%S'))
    achat_id = fields.Many2one('purchase.exp.achat', "Demande d'achat", required=True, ondelete='cascade')
    receveur_id = fields.Many2one('hr.employee', 'Destinataire', required=False)
    det_sortie_ids = fields.One2many('purchase.exp.sortie.detail', 'sortie_id', 'Détail bon de sortie', required=False)
    notes = fields.Text('Notes')

    #_constraints=[(_check_produits,"Veuillez Selectionnez des produits de la demande d'achat confirmée pour la saisie du bon de sortie",['achat_id'])]
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'La reférence doit être unique !'),
    ]


class bon_sortie_detail(models.Model):
    _name="purchase.exp.sortie.detail"
    _description="Détail bon de sortie"
    
    
    def onchange_product_id(self, cr, uid, ids, product_id):
      if not product_id:
       return {}
      pro = self.pool.get('product.product').browse(cr, uid, product_id)
      return {'value': { 'qte_dispo': pro.qty_available,       
          },
       }
    
    
    def _check_qte_produits(self,cr,uid,ids,conText=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            if s.quantite > s.qte_dispo or s.quantite == 0 or s.qte_dispo == 0:
                return False
        return True
    

    name = fields.Char('Reference', size=128, required=False)
    product_id = fields.Many2one('product.product', 'Désignation', required=True)
    quantite = fields.Integer('Quantité', required=True , default=1)
    qte_dispo = fields.Integer('Qté dispo', required=True)
    besoin_id = fields.Many2one('purchase.exp.besoin', 'Besoin', required=False, ondelete='cascade')
    sortie_id = fields.Many2one('purchase.exp.sortie', 'Demande', required=False, ondelete='cascade')

    _constraints=[(_check_qte_produits,"Vous ne pouvez générer de bon de sortie pour des produits en quantité insuffisante ou nulle",['product_id'])]


class cotation_groupee(models.Model):
    _name="purchase.exp.cotation.groupee"
    _description="Demande de cotations groupées"
    _order  = "id desc"
    
    def _template_mail_get(self, cr, uid,ids, conText=None):
        ids = self.pool.get('purchase.exp.achat.template.mail').search(cr, uid, [('name', '=', 'cotation')], conText=conText)
        if ids:
            return ids[0]
        return False

    def _employee_get(self):
        employee = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)])
        if employee :
            return employee[0].id

    @api.model
    def _get_default_listPrice(self):
        res = {}
        listprice= self.env['product.pricelist'].search([])
        if listprice :
            return listprice[0].id
        return False

    @api.model
    def _get_default_location(self):
        location= self.env['stock.location'].search( [('name', '=', 'Stock')])
        if location :
            return location.id
        return False


    name = fields.Char('Libellé', size=128, required=True, readonly=False,states={'done':[('readonly',True)]} , default='Cotation groupée du %s' % time.strftime('%d/%m/%Y %H:%M:%S'))
    date = fields.Date('Date', required=True,states={'done':[('readonly',True)]} , default=time.strftime('%Y-%m-%d'))
    pricelist_id = fields.Many2one('product.pricelist', 'Liste de prix', required=True,states={'done':[('readonly',True)]} , default=_get_default_listPrice)
    location_id = fields.Many2one('stock.location', 'Emplacement', required=True,states={'done':[('readonly',True)]} , default=_get_default_location)
    employee_id = fields.Many2one('hr.employee', 'Employé', required=False , default=_employee_get)
    template_mail_id = fields.Many2one('purchase.exp.achat.template.mail','Template mail achat', required=False)
    appel_offre = fields.Boolean("Appel d'offre", help="Si coché, permet de générer automatiquement un appel d'offre qui contiendra toutes les cotations groupées",states={'done':[('readonly',True)]})
    alerte_mail = fields.Boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement des e-mails aux fournisseurs séléctionnés",states={'done':[('readonly',True)]})
    note = fields.Text('Notes',states={'done':[('readonly',True)]})
    cotation_ids = fields.Many2many('purchase.exp.achat', 'cotation_achat_rel', 'cotation_id', 'achat_id', "Demandes d'achat", domain=[('state','in',('cotation','confirmed'))],states={'done':[('readonly',True)]})
    fournisseur_ids = fields.Many2many('res.partner', 'partner_quotation_rel', 'cotation_id', 'partner_id', 'Autres Fournisseurs', domain=[('supplier','=','True')], help="L'on donne la possibilité à l'utilisateur de choisir d'autres fournisseur pour les demande de cotation hors mis ceux ceux choisi dans les expressions de besoins")
    state = fields.Selection([('draft','Brouillon'),
                            ('confirmed','Confirmé'),
                            ('done','Clôturé')],'Statut',readonly=True,required=True,states={'done':[('readonly',True)]} , default='draft'
                           )

    def action_draft(self,cr,uid,ids,conText=None):
        return self.write(cr,uid,ids,{'state':'draft'})
    
    def action_confirm(self,cr,uid,ids,conText=None):
        return self.write(cr,uid,ids,{'state':'confirmed'})
    
    def action_done(self,cr,uid,ids,conText=None):
        
        #obj_cotation = self.browse(cr,uid,ids,conText)
        obj_purchase_order = self.pool.get('purchase.order')
        obj_purchase_order_line = self.pool.get('purchase.order.line')
        #obj_bon = self.pool.get('purchase.exp.sortie')
        obj_offre = self.pool.get('purchase.requisition')
        obj_offre_line = self.pool.get('purchase.requisition.line')
        purchase_id = False
        
        cr.execute("""SELECT product_id,sum(product_qty),c.id,product_uom,price_unit,pdt.default_code,pdt.name_template,partner_id
                    FROM purchase_exp_achat_detail p, purchase_exp_cotation_groupee c, cotation_achat_rel car,product_product pdt
                    WHERE p.demande_id=car.achat_id
                    AND c.id=car.cotation_id
                    AND pdt.id=p.product_id
                    GROUP BY product_id,c.id,product_uom,price_unit,pdt.default_code,pdt.name_template,partner_id""")
        produits = cr.fetchall()
        
        
        four = {}
        for cotation in self.browse(cr,uid,ids,conText):
            #test = _unique(cotation.cotation_ids)
            
            def unique():
                found = set([])
                keep = []
            
                for dmde_achat in cotation.cotation_ids :
                    for det_achat in dmde_achat.line_det_ids :
                        if det_achat.partner_id.id not in found :
                            found.add(det_achat.partner_id.id)
                            keep.append(det_achat.partner_id.id)
                    
                    """for autre_fournisseur in cotation.fournisseur_ids :
                        if autre_fournisseur.id not in found :
                            found.add(autre_fournisseur.id)
                            keep.append(autre_fournisseur.id)"""
            
                return keep
            
            
            def unique_produits():
                found = set([])
                keep = []
            
                for dmde_achat in cotation.cotation_ids :
                    for det_achat in dmde_achat.line_det_ids :
                        if det_achat.product_id not in found:
                            found.add(det_achat.product_id)
                            keep.append(det_achat.product_id)
            
                return keep
            
            
            id_offre = 0
            if cotation.appel_offre :
                offre = {
                                'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'state': 'draft',
                                'exclusive': 'multiple',
                                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.requisition', conText=conText),
                                'user_id': uid,
                                'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.requisition'),
                             }
                id_offre = obj_offre.create(cr, uid, offre, conText=conText)
                 
            #try :  
                    
            four = unique()
            
            for frs in  four:
                reference = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
                #partner_id = self.pool.get('res.partner').search(cr,uid,[('partner_id','=',frs)])[0]
                order_data = {
                                       'name': reference,
                                       'date_order': time.strftime('%Y-%m-%d'),
                                       'state': 'draft',
                                       'partner_id': frs,
                                       #'partner_address_id': partner_id,
                                       'pricelist_id': cotation.pricelist_id.id,
                                       'location_id':cotation.location_id.id,
                                       'invoice_method':'order',
                                       'requisition_id':id_offre,
                                 }
                purchase_id = obj_purchase_order.create(cr, uid, order_data, conText=conText)
                #raise exceptions.except_orm('Warning test', purchase_id)  
                line = ""
                for pdt in produits :
                    if pdt[2]==cotation.id and pdt[7]==frs:
                        cr.execute("""SELECT product_id,sum(product_qty),c.id
                                    FROM purchase_exp_achat_detail p, purchase_exp_cotation_groupee c, cotation_achat_rel car,product_product pdt
                                    WHERE p.demande_id=car.achat_id
                                    AND c.id=car.cotation_id
                                    AND pdt.id=p.product_id
                                    AND p.product_id=%s
                                    AND c.id=%s
                                    GROUP BY product_id,c.id""",(pdt[0],cotation.id))
                        quantite=cr.fetchall()
                        qty=0
                        for qte in quantite :
                            qty=qte[1]
                        line_data = {
                                    'product_id': pdt[0],
                                    'product_qty': qty,
                                    'product_uom': pdt[3],
                                    'name': pdt[6],
                                    'date_planned': time.strftime('%Y-%m-%d'),
                                    'price_unit': pdt[4],
                                    'order_id': purchase_id,
                                    }
                        line = line +  str(pdt[5]) + ' ' + str(pdt[6]) + "\n"
                        obj_purchase_order_line.create(cr, uid, line_data, conText=conText)
                
                        #Création des produits de l'appel d'offre
                        found = set([])
                        keep = []
                        if pdt[0] not in found:
                            
                            cr.execute('select uom_id from product_product p, product_template t where p.product_tmpl_id=t.id and p.id=%s',(pdt[0],))
                            uom_id = cr.fetchone()[0]
                            cr.execute('select company_id from product_product p, product_template t where p.product_tmpl_id=t.id and p.id=%s',(pdt[0],))
                            company_id = cr.fetchone()[0]
                            
                            produits_offre = {
                                                'product_id': pdt[0],
                                                'product_uom_id': uom_id,
                                                'product_qty': qty,
                                                'requisition_id' : id_offre,
                                                'company_id': company_id,
                                              }
                            obj_offre_line.create(cr, uid, produits_offre, conText=conText)
                            found.add(pdt[0])
                            #keep.append(pdt[0])
                
                cr.execute("""SELECT   COUNT(*) AS nbr_doublon,product_id
                            FROM     purchase_requisition_line
                            WHERE requisition_id=%s
                            GROUP BY product_id
                            HAVING   COUNT(*) > 1""",(id_offre,))
                
                #Send mail sans queue
                if cotation.alerte_mail :
                    #Vérification de possession d'adresse mail des fournisseurs
                    for cot in cotation.cotation_ids :
                        for cota  in cot.line_det_ids :
                            if not cota.partner_id.email :
                                raise exceptions.except_orm('Error','Assurez-vous que chaque fournisseur possède une adresse mail')
                            
                    cr.execute('select email from res_partner where id=%s',(frs,))
                    email = cr.fetchone()[0]
                    if cotation.template_mail_id.active :
                        ir_mail_server = self.pool.get('ir.mail_server')
                        msg = ir_mail_server.build_email(cotation.employee_id.work_email, [email], "Demande de cotation " + reference, cotation.template_mail_id.mail + "\n\n" + line)
                        ir_mail_server.send_email(cr, uid, msg)
            #except :
            #    partner_id = ''
                    
            for c in cotation.cotation_ids :
                cr.execute("""UPDATE purchase_exp_achat SET state = %s WHERE state = %s AND id = %s""",('cotation','confirmed',str(c.id)))
            
            
            return self.write(cr,uid,ids,{'state':'done'})



class stock_picking(models.Model):
    _inherit = "stock.picking"
    _name = "stock.picking"

    achat_id = fields.Many2one('purchase.exp.achat', "Demande d'achat", required=False)

class product_category_temp(models.Model):
    _name = "product.category.temp"
    
    catogory_id = fields.Many2one('product.category', "Category", required=False)

class commentaire(models.Model):
    _name="purchase.exp.commentaire"
    _description="Commentaires des expressions de besoin"

    @api.model
    def _user_get(self):
        return self._uid
        
    name = fields.Char('Name', size=64, required=False, readonly=False)
    user_id = fields.Many2one('res.users', 'Utilisateur', required=False, readonly=True , default=_user_get)
    date = fields.Datetime('Date' , default=lambda *a: str(datetime.now()))
    commentaire = fields.Text('Commentaire', required=True)
    besoin_id = fields.Many2one('purchase.exp.besoin', 'Besoin', required=False)
    order_id = fields.Many2one('purchase.exp.achat', 'Ordre achat', required=False)

    @api.multi
    def unlink(self):
        if self.user_id.id != self._uid :
            raise exceptions.except_orm('Erreur', "Vous ne pouvez supprimer le commentaire d'un autre utilisateur !")
        
        return models.Model.unlink(self)


