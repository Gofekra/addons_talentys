# -*- encoding: utf-8 -*-

from odoo import api , fields, models, _
import time
from datetime import datetime
from odoo import netsvc



class demande_achat(models.Model):
    _name="purchase.exp.achat"
    _logger = netsvc.Logger()
    _description="Demande d'achat"
    _order = "name desc"
    
    
    def _get_montant_achat(self,cr,uid,ids,field,args,context=None) :
        res={}
        for achat in self.browse(cr,uid,ids,context) :
            cpt=0
            for det in achat.line_det_ids :
                cpt += det.subtotal
            res[achat.id] = cpt
        return res
    
    
    def onchange_quotation_id(self, cr, uid, ids, quotation_id):
        if not quotation_id:
            return {}
        quo = self.pool.get('purchase.order').browse(cr, uid, quotation_id)
        return {'value': {'pricelist_id': quo.pricelist_id.id,
                          },
                            
            }
        
        
    def onchange_sale_id(self, cr, uid, ids, sale_id):
        if not sale_id:
            return {}
        sale = self.pool.get('sale.order').browse(cr, uid, sale_id)
        return {'value': {'sale_pricelist_id': sale.pricelist_id.id,
                          },
                            
            }
    
    def _user_mail_get(self, cr, uid, ids, context=None):
        results = self.pool.get('res.users').read(cr, uid, [uid],['email'])
        if results:
            return results[0]['email']
        return False 
    
    
    def _get_devise(self, cr, uid, ids, field, arg, context=None):
        res={}
        for demande in self.browse(cr,uid,ids) :
            devise = demande .pricelist_id.currency_id.symbol
            res[demande.id] = devise
        return res
    
    
    def _get_amount_untaxed(self, cr, uid, ids, field, arg, context=None):
        res={}
        amount_untaxed = 0.00
        
        for achat in self.browse(cr, uid, ids) :
            for line in achat.line_det_ids :
                amount_untaxed += line.subtotal
                
            res[achat.id] = amount_untaxed
        
        return res
    
    
    def _get_amount_tax(self, cr, uid, ids, field, arg, context=None):
        res={}
        amount_tax = 0.00
        
        for achat in self.browse(cr, uid, ids) :
            for line in achat.line_det_ids :
                if line.taxe_id :
                    amount_tax += line.subtotal * line.taxe_id.amount
                
            res[achat.id] = amount_tax
        
        return res
    
    
    def _get_amount_total(self, cr, uid, ids, field, arg, context=None):
        res={}
        
        for achat in self.browse(cr, uid, ids) :
            amount_untaxed = 0.00
            amount_tax = 0.00
            for line in achat.line_det_ids :
                amount_untaxed += line.subtotal
                if line.taxe_id :
                    amount_tax += line.subtotal * line.taxe_id.amount
                
            res[achat.id] = amount_untaxed + amount_tax
        
        return res
        
    
    
    _columns={
              'name':fields.char('Référence',128,required=True,states={'done':[('readonly',True)]}),
              'date':fields.date('Date', help='Date',states={'done':[('readonly',True)]}),
              'date_prevue':fields.datetime('Date', help='Date prévue',states={'done':[('readonly',True)]}),
              'demandeur_id':fields.many2one('hr.employee', 'Demandeur', required=False, readonly=True, help='Employé en charge de la demande selectionné automatiquement'),
              'user_id':fields.many2one('res.users', 'Validateur', required=True),
              'pricelist_id':fields.many2one('product.pricelist', "Liste de prix d'achat", required=True,states={'done':[('readonly',True)]}),
              'location_id':fields.many2one('stock.location', 'Emplacement source', required=True,states={'done':[('readonly',True)]}),
              'location_dest_id':fields.many2one('stock.location', 'Emplacement destination', required=True,states={'done':[('readonly',True)]}),
              'notes': fields.text('Commentaires',states={'done':[('readonly',True)]}),
              'projet': fields.char('Projet'),
              'line_det_ids':fields.one2many('purchase.exp.achat.detail', 'demande_id', 'Détail demande', required=False,states={'done':[('readonly',True)]}),
              'bon_sortie_ids':fields.one2many('purchase.exp.sortie', 'achat_id', 'Bon de sortie',states={'done':[('readonly',True)]}),
              'commentaire_ids':fields.one2many('purchase.exp.commentaire','order_id', required=False),
              'demande_id':fields.many2one('purchase.exp.besoin', 'Référence du Besoin', required=False, ondelete="cascade", readonly=True),
              'quotation_id':fields.many2one('purchase.order', 'Devis Fournisseur', required=False, states={'done':[('readonly',True)]}),
              'sale_id':fields.many2one('sale.order', 'Devis Client', required=False, states={'done':[('readonly',True)]}),
              'alerte_mail':fields.boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement un e-mail d'alerte au responsable après la confirmation de la demande d'achat pour validation",states={'done':[('readonly',True)]}),
              'mail_user':fields.function(_user_mail_get, method=True, type='char', string='Mail user'), 
              'notes_finance': fields.text('Commentaires finance',states={'done':[('readonly',True)]}),
              'devise':fields.function(_get_devise, method=True, type='char', string='Devise'), 
              'currency_id': fields.related('pricelist_id', 'currency_id', type="many2one", relation="res.currency", string="Currency", readonly=True, required=True),
              'dg':fields.boolean('DG'),
              'finance':fields.boolean('Finance'),
              'amount_untaxed': fields.function(_get_amount_untaxed, method=True, type='float', string='Montant hors-taxe'),
              'amount_tax': fields.function(_get_amount_tax, method=True, type='float', string='Taxe'),
              'amount_total': fields.function(_get_amount_total, method=True, type='float', string='Total'),
              'type_demande':fields.selection([
                  ('general','Général'),
                  ('achat','Général direct'),
                  ('technique','Technique'),
                  ('divers','Dépenses diverses'),
                  ], 'Type de demande', select=True, readonly=True,states={'done':[('readonly',True)]}),
              'mtt_achat':fields.function(_get_montant_achat,
                                                method=True,
                                                type='float',
                                                string='Montant', help='Montant évalué du besoin'),
              'state':fields.selection([('draft','Brouillon'),
                                        ('draft_tech','Brouillon'),
                                        ('service','Service'),
                                        ('departement','Département'),
                                        ('finance','Finance'),
                                        ('finance_ach','Finance'),
                                        ('finance_cai','Finance'),
                                        ('direction','Direction'),
                                        ('achat','Achat'),
                                        ('caisse','Caisse'),
                                        ('commande','Commande'),
                                        ('bon','BS émis'),
                                        ('done','Terminé')],'Statut',readonly=True,required=True,states={'done':[('readonly',True)]}
                                       ),
              'message_ids':fields.one2many('mail.message','res_id','Message',required=False),
              }
    
    _sql_constraints = [
        ('name_uniq', 'unique(demande_id)', "La reférence de l'expression de besoin doit être unique"),
    ]

    def _user_get(self, cr, uid, context=None):
        ids = self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False
    
    def _get_notification(self, cr, uid, ids, model, name, body, subject, object_id, user_id, demande, context=None):
        besoin_obj = self.pool.get('purchase.exp.besoin')
        besoin_obj._get_notification(cr, uid, ids, model, demande.name, body, subject, object_id, user_id, context)
        return True
            
    def notif_mail(self, cr, uid, ids, user_from, user_to, subject, mail, demande):
        url1 = "http://erp:8069/?db=TALENTYS#id="
        url2 = "&view_type=form&model=purchase.exp.achat&menu_id=614&action=780"
        url = url1 + str(demande.id) + url2
        if demande.alerte_mail :
            if not demande.demandeur_id.work_email :
                raise osv.except_osv('Warning',"Veuiller renseigner l'adresse mail du demandeur")
            if not demande.demandeur_id.parent_id.work_email :
                raise osv.except_osv('Warning',"Veuiller renseigner l'adresse mail du responsable du demandeur")
        
            mail = mail + "\n\n" + url
            ir_mail_server = self.pool.get('ir.mail_server')
            msg = ir_mail_server.build_email(user_from, [user_to], subject, mail)
            ir_mail_server.send_email(cr, uid, msg)
                  
        return True
    
    
    def action_draft(self,cr,uid,ids,context=None):
        
        for achat in self.browse(cr, uid, ids) :
            if achat.alerte_mail :
                user = self.pool.get('res.users').read(cr, uid, [uid],['name'])[0]['name']
                message = """Bonjour M/Mme\n\n Votre demande d'achat a été mise en brouillon. \n\nCordialement !\n\n"""
                titre = 'Demande d\'achat %s : Mise en brouillon par %s' % (achat.name, user)
                emetteur = 'openerp@talentys.ci'
                self.notif_mail(cr, uid, ids, emetteur, achat.demandeur_id.work_email, titre, message, achat)
                
        results = self.pool.get('res.users').read(cr, uid, [uid],['technicien'])
        technicien = False
        if results:
            technicien = results[0]['technicien']
        
        if technicien :
            return self.write(cr,uid,ids,{'state':'draft_tech'})
        else :
            return self.write(cr,uid,ids,{'state':'draft'})
            
            
        
    def button_dummy(self, cr, uid, ids, context=None):
        return True  


    def action_service(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise au Chef de Service Support pour validation</p>", "Demande d'achat", demande.id, demande.user_id.id,demande, context)
            
            message = """Bonjour M/Mme\n\nJe vous prie de bien vouloir valider ma demande d'achat ci-dessous.\nCordialement \n\n"""
            self.notif_mail(cr, uid, ids, demande.demandeur_id.work_email, demande.demandeur_id.parent_id.work_email, 'Expression de besoin : Validée par le Chef de Service', message, demande)
            
        return self.write(cr,uid,ids,{'state':'service'})
    
    def action_departement(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            
            if demande.demandeur_id.user_id.id == uid and  demande.demandeur_id.user_id.technicien == True and demande.demandeur_id.manager == False:
                raise osv.except_osv('Warning', _('Vous n\'êtes pas autorisé à valider cette demande, Veuillez vous référer à votre chef de service '))
            
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise au Chef du Département pour validation</p>", "Demande d'achat", demande.id, demande.user_id.id,demande, context)
            message = """Bonjour M/Mme\n\nJe vous prie de bien vouloir valider la demande d'achat ci-dessous.\nCordialement \n\n"""
            self.notif_mail(cr, uid, ids, demande.demandeur_id.work_email, demande.demandeur_id.parent_id.work_email, "Demande d'achat : En attente de validation", message, demande)
        return self.write(cr,uid,ids,{'state':'departement'})
    
    
    def action_finance(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            besoin_obj = self.pool.get('purchase.exp.besoin')
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise au Responsable des Finances pour validation</p>", "Demande d'achat", demande.id, demande.user_id.id,demande, context)
            message = """Bonjour M/Mme\n\nJe vous prie de bien vouloir valider la demande d'achat ci-dessous.\nCordialement \n\n"""
            emetteur = self._user_mail_get(cr,uid,ids,context)
            destinataire = besoin_obj._company_param_get(cr, uid, ids, 'mail_dep_finance', context)
            self.notif_mail(cr, uid, ids, emetteur, destinataire, "Demande d'achat : En attente de validation", message, demande)
        
            if demande.state == 'direction' : 
                self.write(cr, uid, ids, {'dg' : True})
                if demande.type_demande in ('general', 'technique', 'achat') :
                    self.write(cr, uid, ids, {'state' : 'finance_ach'})
                else : 
                    self.write(cr,uid,ids,{'state':'finance_cai'})
            else :
                return self.write(cr,uid,ids,{'state':'finance'})
            
    
    
    def action_direction(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            besoin_obj = self.pool.get('purchase.exp.besoin')
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise au Directeur Général pour validation</p>", "Demande d'achat", demande.id, demande.user_id.id,demande, context)
            message = """Bonjour M/Mme\n\nMerci de bien vouloir prendre en compte la demande d'achat ci-dessous.\nCordialement \n\n"""
            emetteur = self._user_mail_get(cr,uid,ids,context)
            destinataire = besoin_obj._company_param_get(cr, uid, ids, 'mail_direction_gle', context)
            self.notif_mail(cr, uid, ids, emetteur, destinataire, "Demande d'achat : En attente de validation", message, demande)
        return self.write(cr,uid,ids,{'state':'direction',
                                      'finance': True})
    
    def action_achat(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            if demande.type_demande == 'divers' :
                raise osv.except_osv(_('Warning'),_('Les demandes de type Dépense diverses doivent être transmises à la caisse'))
            
            if not demande.dg :
                raise osv.except_osv(_('Warning'),_('La demande doit être d\'abord validée par la Direction Générale !'))
            
            besoin_obj = self.pool.get('purchase.exp.besoin')
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise au responsable des achats pour émission du Bon de Commande</p>", "Demande d'achat", demande.id, demande.user_id.id, demande, context)
            message = """Bonjour M/Mme\n\nMerci de bien vouloir prendre en compte la demande d'achat ci-dessous.\nCordialement \n\n"""
            emetteur = self._user_mail_get(cr,uid,ids,context)
            destinataire = besoin_obj._company_param_get(cr, uid, ids, 'mail_sce_achat', context)
            self.notif_mail(cr, uid, ids, emetteur, destinataire, "Demande d'achat : Validée par le Département des Finances", message, demande)
        
        return self.write(cr,uid,ids,{'state':'achat'})
    
    
    def action_caisse(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            if demande.type_demande == 'achat' :
                raise osv.except_osv(_('Warning'),_('Les demandes de type Dépense diverses achat doivent être transmises aux achats'))
            
            besoin_obj = self.pool.get('purchase.exp.besoin')
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat transmise à la caisse pour paiement</p>", "Demande d'achat", demande.id, demande.user_id.id, demande, context)
            message = """Bonjour M/Mme\n\nMerci de bien vouloir prendre en compte la demande d'achat ci-dessous pour paiement.\nCordialement \n\n"""
            emetteur = self._user_mail_get(cr,uid,ids,context)
            destinataire = besoin_obj._company_param_get(cr, uid, ids, 'mail_sce_caisse', context)
            self.notif_mail(cr, uid, ids, emetteur, destinataire, "Demande d'achat : Validée par le Département des Finances", message, demande)
        return self.write(cr,uid,ids,{'state':'caisse'})
    
    
    def action_commande(self,cr,uid,ids,context=None):
        for achat in self.browse(cr,uid,ids) :
            if not achat.quotation_id :
                raise osv.except_osv('Erreur','Veuillez selectionner un devis fournisseur')
            self.pool.get('purchase.order').wkf_approve_order(cr, uid, [achat.quotation_id.id])
            self.pool.get('purchase.order').action_picking_create(cr, uid, [achat.quotation_id.id])
        
        for demande in self.browse(cr,uid,ids):
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Emission du Bon de Commande au fournisseur </p>" + demande.quotation_id.partner_id.name, "Bon de Commande", demande.id, demande.user_id.id, demande, context)
        return self.write(cr,uid,ids,{'state':'commande'})
    
    def action_cotation(self,cr,uid,ids,context=None):
        obj_cotation = self.browse(cr,uid,ids,context)
        obj_purchase_order = self.pool.get('purchase.order')
        obj_purchase_order_line = self.pool.get('purchase.order.line')
        obj_bon = self.pool.get('purchase.exp.sortie')
        
        cr.execute("""SELECT product_id,sum(product_qty),p.id,product_uom,price_unit,pdt.default_code,pdt.name_template,partner_id
                    FROM purchase_exp_achat p,purchase_exp_achat_detail dp,product_product pdt
                    WHERE p.id=dp.demande_id
                    and pdt.id=dp.product_id
                    GROUP BY product_id,p.id,product_uom,price_unit,pdt.default_code,pdt.name_template,partner_id""")
        produits = cr.fetchall()
        
        four = {}
        for demande in self.browse(cr,uid,ids,context):
            #test = _unique(cotation.cotation_ids)
            
            def unique():
                found = set([])
                keep = []
            
                for dmde_achat in demande.line_det_ids :
                    if dmde_achat.partner_id.id not in found:
                        found.add(dmde_achat.partner_id.id)
                        keep.append(dmde_achat.partner_id.id)
            
                return keep
            
            """"id_offre = 0
            if cotation.appel_offre :
                offre = {
                                'date_start': time.strftime('%Y-%m-%d %H:%M:%S'),
                                'state': 'draft',
                                'exclusive': 'multiple',
                                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.requisition', context=context),
                                'user_id': uid,
                                'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.requisition'),
                             }
                id_offre = obj_offre.create(cr, uid, offre, context=context)"""
            
            four = unique()
            for frs in  four:
                reference = self.pool.get('ir.sequence').get(cr, uid, 'purchase.order')
                order_data = {
                                       'name': reference,
                                       'date_order': time.strftime('%Y-%m-%d'),
                                       'state': 'draft',
                                       'partner_id': frs,
                                       #'partner_address_id': self.pool.get('res.partner').search(cr,uid,[('partner_id','=',frs)])[0],
                                       'pricelist_id': demande.pricelist_id.id,
                                       'location_id':demande.location_id.id,
                                       'invoice_method':'order',
                                       #'requisition_id':id_offre,
                                 }
                id = obj_purchase_order.create(cr, uid, order_data, context=context)
                line = ""
                for pdt in produits :
                    if pdt[2]==demande.id and pdt[7]==frs:
                        line_data = {
                                                'product_id': pdt[0],
                                                'product_qty': pdt[1],
                                                'product_uom': pdt[3],
                                                'name': pdt[6],
                                                'date_planned': time.strftime('%Y-%m-%d'),
                                                'price_unit': pdt[4],
                                                'order_id': id
                                            }
                        #line = line +  str(pdt[5]) + ' ' + str(pdt[6]) + "\n"
                        obj_purchase_order_line.create(cr, uid, line_data, context=context)
                        
        return self.write(cr,uid,ids,{'state':'cotation'})
    
    def action_done(self,cr,uid,ids,context=None):
        for demande in self.browse(cr,uid,ids):
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Demande d'achat terminée</p>", "Demande d'achat", demande.id, demande.user_id.id, demande, context)
        self.write(cr,uid,ids,{'state':'done'})
             
        return True
    
    
    def action_bon_sortie(self,cr,uid,ids,context=None):
        sortie_obj = self.pool.get('purchase.exp.sortie')
        det_sortie_obj = self.pool.get('purchase.exp.sortie.detail')
        bon_livr_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        
        for dmde in self.browse(cr,uid,ids):
            
            sortie = {
                      'name':self.pool.get('ir.sequence').get(cr, uid, 'purchase.exp.sortie'),
                      'datetime':time.strftime('%Y-%m-%d %H:%M:%S'),
                      'achat_id':dmde.id,
                      'receveur_id':dmde.demandeur_id.id,
                      } 
        id = sortie_obj.create(cr, uid, sortie, context=context)
            
        #try :
        address_id = self.pool.get('res.partner').search(cr,uid,[('id','=',dmde.demandeur_id.id)])[0]
        reference = self.pool.get('ir.sequence').get(cr, uid, 'stock.picking.out')
        livraison = {
                         'name': reference,
                         'origin': dmde.name,
                         'achat_id':dmde.id,
                         'min_date':dmde.date_prevue,
                         'max_date':time.strftime('%Y-%m-%d %H:%M:%S'),
                         'address_id':address_id,
                         'date':time.strftime('%Y-%m-%d %H:%M:%S'),
                         'date_done':time.strftime('%Y-%m-%d %H:%M:%S'),
                         'stock_journal_id':1,
                         'type': 'out',
                         'move_type':'one',
                         'state':'draft'
                    }
        
        livr_id = bon_livr_obj.create(cr, uid, livraison, context=context)
        
        for det_dmde in dmde.line_det_ids :
            
            det_sortie = {
                            'name':det_dmde.name,
                            'product_id':det_dmde.product_id.id,
                            'quantite':det_dmde.product_qty,
                            'qte_dispo':det_dmde.product_id.qty_available,
                            'besoin_id':dmde.demande_id.id,
                            'sortie_id':id
                        }
            
            move_line = {
                            'name': 'BSLine - %s' % (det_dmde.product_id.name),
                            'priority':'1',
                            #'create_date':time.strftime('%Y-%m-%d %H:%M:%S'),
                            'date':time.strftime('%Y-%m-%d %H:%M:%S'),
                            'date_expected':time.strftime('%Y-%m-%d %H:%M:%S'),
                            'product_id':det_dmde.product_id.id,
                            'product_qty':det_dmde.product_qty,
                            'product_uos_qty':det_dmde.product_qty,
                            'product_uom':self.pool.get('product.uom').search(cr,uid,[('id','=',det_dmde.product_id.uom_id.id)])[0],
                            'product_uos':self.pool.get('product.uom').search(cr,uid,[('id','=',det_dmde.product_id.uom_id.id)])[0],
                            'price_unit':det_dmde.price_unit,
                            'location_id':self.pool.get('stock.location').search(cr,uid,[('name','=','Stock')])[0],
                            'location_dest_id':self.pool.get('stock.location').search(cr,uid,[('name','=','Output')])[0],
                            'address_id':self.pool.get('res.partner').search(cr,uid,[('id','=',dmde.demandeur_id.id)])[0],
                            'picking_id':livr_id,
                            'state':'draft',
                         }
            
            det_sortie_obj.create(cr, uid, det_sortie, context=context)
            move_obj.create(cr, uid, move_line, context=context)
        """except :
            address_id = False"""
            
        for demande in self.browse(cr,uid,ids):
            self._get_notification(cr, uid, ids, 'purchase.exp.achat', demande.name,"<p>Emission de bon pour sortie</p>", "Bon pour sortie", demande.id, demande.user_id.id, demande, context)
            
            besoin_obj = self.pool.get('purchase.exp.besoin')
            message = """Bonjour M/Mme\n\nVeuillez trouver le bon pour sortie relatif à votre demande d'achat ci-dessous.\n\nCordialement \n\n"""
            emetteur = self._user_mail_get(cr,uid,ids,context)
            destinataire = besoin_obj._company_param_get(cr, uid, ids, 'mail_sce_achat', context)
            self.notif_mail(cr, uid, ids, emetteur, destinataire, "Bon pour sortie : Transmis par le responsable des achats", message, demande)
            
        return self.write(cr,uid,ids,{'state':'bon'})
    
    
    def print_requisition(self, cr, uid, ids, context=None):
        #assert len(ids) == 1, 'This option should only be used for a single id at a time'
        datas = self.read(cr, uid, [105], context=context)
        if datas :
            data = datas[0]
        
        self.write(cr,uid,ids,data,context)
        datas = {
             'ids': ids,
             'model': 'purchase.exp.achat',
             'form': data
        }

        return {
            'type': 'ir.actions.report.xml',
            'report_name': 'da.report',
            'datas': datas,
            'nodestroy':True
        }
    
    _defaults={
               'user_id':_user_get,
               'date':time.strftime('%Y-%m-%d'),
               #'state':'draft', 
               #'alerte_mail':True,
               'notes': "La présente demande s'inscrit dans le cadre de...",
               'location_dest_id':lambda obj, cr, uid, context: obj.pool.get('stock.location').search(cr, uid, [('name', '=', 'Output')], context=context)[0],
               }
    
    
demande_achat()


class detail_demande_achat(models.Model):
    _name="purchase.exp.achat.detail"
    _description="Détail demande d'achat"

    
    def _get_quantite(self,cr,uid,ids,field,arg,context=None):
        res={}
        var_tmp_ids=self.browse(cr,uid,ids,context)
        for s in var_tmp_ids:
            res[s.id]=s.product_id.qty_available
        return res

    
    def _get_quantite_cmde(self,cr,uid,ids,field,arg,context=None):
        res={}
        cr.execute("SELECT sum(product_qty),product_id,state FROM  purchase_order_line WHERE state='confirmed' GROUP BY product_id,state")
        produits = cr.fetchall()

        for det in self.browse(cr,uid,ids,context):
            qte = 0
            for prod in produits:
                if det.product_id.id==prod[1] :
                    qte=prod[0]
            res[det.id]=qte
        return res
    
    
    def quantite_livree(self,cr,uid,ids,field,arg,context=None):
        res={}
        
        cr.execute("""SELECT SUM(ds.quantite),ds.product_id,a.id FROM purchase_exp_sortie AS s,purchase_exp_sortie_detail AS ds, purchase_exp_achat a,purchase_exp_besoin b WHERE a.id=s.achat_id AND s.id=ds.sortie_id AND a.demande_id=b.id GROUP BY ds.product_id,a.id""")
        produits = cr.fetchall()
        
        for detail in self.browse(cr,uid,ids):
            qte = 0
            for prod in produits:
                if detail :
                    if detail.demande_id.id==prod[2] :
                        if detail.product_id.id==prod[1] :
                                qte=prod[0]
            res[detail.id]=qte

        return res
    
    
    def _check_qte_livree(self,cr,uid,ids,context=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            if s.product_qty < s.gave_qty :
                return False
        return True
    
    
    def _check_qte_null(self,cr,uid,ids,context=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            if s.product_qty ==0 :
                return False
        return True

    def _get_sub_total(self,cr,uid,ids,field,arg,context=None):
        res={}
        remise = 0.00
        subtotal = 0.00
        taxe = 0.00
        for i in self.browse(cr, uid, ids, context):
            if i.taxe_id :
                taxe = i.taxe_id.amount
            remise = i.discount
            subtotal= i.price_unit * (1 - remise/100) * i.product_qty
            res[i.id]=subtotal
        return res
    
    
    
    _columns={
                'name': fields.char('Désignation', size=256, required=True),
                'product_qty': fields.float('Qté dmdée', required=True),
                'available_qty':fields.function(_get_quantite,
                                                method=True,
                                                type='float',
                                                string='Qté dispo.', help='Quantité réelle du produit disponible en stock'),
                'ordered_qty':fields.function(_get_quantite_cmde,
                                                method=True,
                                                type='float', string='Qté cmdée.', help='Quantité commandée du produit demandé'),
                'gave_qty':fields.function(quantite_livree,
                                                method=True,
                                                type='float',
                                                string='Qté livrée', help='Quantité livrée du produit demandé'),
                'date_planned': fields.date('Date', required=True, select=True),
                'product_uom': fields.many2one('product.uom', 'Product UOM', required=True, help='Unité de mesure du produit'),
                'product_id': fields.many2one('product.product', 'Product', domain=[('purchase_ok','=',True)], change_default=True),
                'price_unit': fields.float('Prix unitaire', required=True),
                'taxe_id':fields.many2one('account.tax','Taxe', domain=[('type_tax_use','in',('purchase','all'))]),
                'partner_id':fields.many2one('res.partner', 'Fournisseur potentiel', required=False, domain=[('supplier','=',True)], help='Fournisseur potentiel de la demande'),
                'notes': fields.text('Notes'),
                'demande_id':fields.many2one('purchase.exp.achat', 'Demande', required=False, ondelete='cascade'),
                'discount':fields.float('Remise (%)'),
		        'subtotal':fields.function(_get_sub_total,method=True,type='float',string="Sous-Total"),
              }
    
    _defaults={
               'product_qty':1
               }
    _constraints=[(_check_qte_livree,"La quantité de produit à livrer ne peut être supérieure à la quantité initiale demandée",['product_qty'])]
    _constraints=[(_check_qte_null,"Les quantités nulles ne sont pas admises",['product_qty'])]

detail_demande_achat()


class bon_sortie(models.Model):
    _name="purchase.exp.sortie"
    _description="Bon de sortie"
    _order = 'name desc'
    
    def _receveur_get(self, cr, uid,ids, context=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            id_ach = 6
            
        cr.execute("""SELECT demandeur_id FROM purchase_exp_achat WHERE id=%s""",str(id_ach))
        demandeur = cr.fetchall()
        for s in self.browse(cr,uid,ids) :
            for d in demandeur :
                res[s.id]=d[0]
        return res

    
    def _check_state(self,cr,uid,ids,context=None):
        for s in self.browse(cr,uid,ids) :
            if s.achat_id.state == "confirmed" :
                return False
        return True
    
    
    def _check_produits(self,cr,uid,ids,context=None):
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
    
    
    def get_inputs(self, cr, uid,ids, context=None):
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

    
    _columns={
              'name':fields.char('Référence', size=64, required=True, readonly=False),
              'datetime': fields.datetime('Date',required=True),
              'achat_id':fields.many2one('purchase.exp.achat', "Demande d'achat", required=True, ondelete='cascade'),
              'receveur_id':fields.many2one('hr.employee', 'Destinataire', required=False),
              'det_sortie_ids':fields.one2many('purchase.exp.sortie.detail', 'sortie_id', 'Détail bon de sortie', required=False),
              'notes':fields.text('Notes')
              }
    
    _defaults={
               'name':lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'purchase.exp.sortie'),
               'datetime':time.strftime('%Y-%m-%d %H:%M:%S'),
               }
    
    #_constraints=[(_check_produits,"Veuillez selectionnez des produits de la demande d'achat confirmée pour la saisie du bon de sortie",['achat_id'])]
    _sql_constraints = [
        ('name_uniq', 'unique(name)', 'La reférence doit être unique !'),
    ]
bon_sortie()


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
    
    
    def _check_qte_produits(self,cr,uid,ids,context=None):
        res={}
        for s in self.browse(cr,uid,ids) :
            if s.quantite > s.qte_dispo or s.quantite == 0 or s.qte_dispo == 0:
                return False
        return True
    
    _columns={
              'name':fields.char('Reference', size=128, required=False),
              'product_id':fields.many2one('product.product', 'Désignation', required=True),
              'quantite':fields.integer('Quantité', required=True),
              'qte_dispo':fields.integer('Qté dispo', required=True),
              'besoin_id':fields.many2one('purchase.exp.besoin', 'Besoin', required=False, ondelete='cascade'),
              'sortie_id':fields.many2one('purchase.exp.sortie', 'Demande', required=False, ondelete='cascade'),
              }
    _defaults={
              'quantite':1,
              }
    _constraints=[(_check_qte_produits,"Vous ne pouvez générer de bon de sortie pour des produits en quantité insuffisante ou nulle",['product_id'])]
bon_sortie_detail()


class cotation_groupee(models.Model):
    _name="purchase.exp.cotation.groupee"
    _description="Demande de cotations groupées"
    _order  = "id desc"
    
    
    def _employee_get(self, cr, uid, context=None):
        ids = self.pool.get('hr.employee').search(cr, uid, [('user_id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False
    
    
    _columns={
              'name':fields.char('Libellé', size=128, required=True, readonly=False,states={'done':[('readonly',True)]}),
              'date':fields.date('Date', required=True,states={'done':[('readonly',True)]}),
              'pricelist_id':fields.many2one('product.pricelist', 'Liste de prix', required=True,states={'done':[('readonly',True)]}),
              'location_id':fields.many2one('stock.location', 'Emplacement', required=True,states={'done':[('readonly',True)]}),
              'employee_id':fields.many2one('hr.employee', 'Employé', required=False),
              'template_mail_id':fields.many2one('purchase.exp.achat.template.mail','Template mail achat', required=False),
              'appel_offre':fields.boolean("Appel d'offre", help="Si coché, permet de générer automatiquement un appel d'offre qui contiendra toutes les cotations groupées",states={'done':[('readonly',True)]}),
              'alerte_mail':fields.boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement des e-mails aux fournisseurs séléctionnés",states={'done':[('readonly',True)]}),
              'note':fields.text('Notes',states={'done':[('readonly',True)]}),
              'cotation_ids':fields.many2many('purchase.exp.achat', 'cotation_achat_rel', 'cotation_id', 'achat_id', "Demandes d'achat", domain=[('state','in',('cotation','confirmed'))],states={'done':[('readonly',True)]}),
              'fournisseur_ids':fields.many2many('res.partner', 'partner_quotation_rel', 'cotation_id', 'partner_id', 'Autres Fournisseurs', domain=[('supplier','=','True')], help="L'on donne la possibilité à l'utilisateur de choisir d'autres fournisseur pour les demande de cotation hors mis ceux ceux choisi dans les expressions de besoins"),
              'state':fields.selection([('draft','Brouillon'),
                                        ('confirmed','Confirmé'),
                                        ('done','Clôturé')],'Statut',readonly=True,required=True,states={'done':[('readonly',True)]}
                                       )
              }

    
    def _template_mail_get(self, cr, uid,ids, context=None):
        ids = self.pool.get('purchase.exp.achat.template.mail').search(cr, uid, [('name', '=', 'cotation')], context=context)
        if ids:
            return ids[0]
        return False
    
    def action_draft(self,cr,uid,ids,context=None):
        return self.write(cr,uid,ids,{'state':'draft'})
    
    def action_confirm(self,cr,uid,ids,context=None):
        return self.write(cr,uid,ids,{'state':'confirmed'})
    
    def action_done(self,cr,uid,ids,context=None):
        
        #obj_cotation = self.browse(cr,uid,ids,context)
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
        for cotation in self.browse(cr,uid,ids,context):
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
                                'company_id': self.pool.get('res.company')._company_default_get(cr, uid, 'purchase.requisition', context=context),
                                'user_id': uid,
                                'name': self.pool.get('ir.sequence').get(cr, uid, 'purchase.order.requisition'),
                             }
                id_offre = obj_offre.create(cr, uid, offre, context=context)
                 
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
                purchase_id = obj_purchase_order.create(cr, uid, order_data, context=context)
                #raise osv.except_osv('Warning test', purchase_id)  
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
                        obj_purchase_order_line.create(cr, uid, line_data, context=context)
                
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
                            obj_offre_line.create(cr, uid, produits_offre, context=context)
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
                                raise osv.except_osv('Error','Assurez-vous que chaque fournisseur possède une adresse mail')
                            
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
    
    _defaults={
                'employee_id': _employee_get,
                'template_mail_id':_template_mail_get,
                'state':'draft',
                'name':'Cotation groupée du %s' % time.strftime('%d/%m/%Y %H:%M:%S'),
                'date':time.strftime('%Y-%m-%d'),
                'pricelist_id':lambda obj, cr, uid, context: obj.pool.get('product.pricelist').search(cr, uid, [('type', '=', 'purchase')], context=context)[0],
                'location_id':lambda obj, cr, uid, context: obj.pool.get('stock.location').search(cr, uid, [('name', '=', 'Stock')], context=context)[0],

              }
    
cotation_groupee()

class purchase_order(models.Model):
    _inherit = "purchase.order"
    _name = "purchase.order"
    
    _columns={
              'achat_id':fields.many2one('purchase.exp.achat', "Demande d'achat", required=False),
              'besoin_id':fields.many2one('purchase.exp.besoin', "Expression de besoin", required=False),
              }
purchase_order()


class product_product(models.Model):
    _inherit = "product.product"
    _name = "product.product"
    
    _columns={
              'achat_id':fields.many2one('purchase.exp.achat', "Demande d'achat", required=False),
              }
    
product_product()

class stock_picking(models.Model):
    _inherit = "stock.picking"
    _name = "stock.picking"
    
    _columns={
              'achat_id':fields.many2one('purchase.exp.achat', "Demande d'achat", required=False),
              }
    
stock_picking()

class product_category_temp(models.Model):
    _name = "product.category.temp"
    
    _columns={
              'catogory_id':fields.many2one('product.category', "Category", required=False),
              }
    
product_category_temp()


class commentaire(models.Model):
    _name="purchase.exp.commentaire"
    _description="Commentaires des expressions de besoin"
    
          
    _columns={
              'name':fields.char('Name', size=64, required=False, readonly=False),
              'user_id':fields.many2one('res.users', 'Utilisateur', required=False, readonly=True),
              'date': fields.datetime('Date'),
              'commentaire':fields.text('Commentaire', required=True),
              'besoin_id':fields.many2one('purchase.exp.besoin', 'Besoin', required=False),
              'order_id':fields.many2one('purchase.exp.achat', 'Ordre achat', required=False),
              }
     
    
    def unlink(self, cr, uid, ids, context=None):
        for comment in self.browse(cr,uid,ids) :
            if comment.user_id.id != uid :
                raise osv.except_osv('Erreur', "Vous ne pouvez supprimer le commentaire d'un autre utilisateur !")
        
        return models.Model.unlink(self, cr, uid, ids, context=context)

    
    def _user_get(self, cr, uid, context=None):
        ids = self.pool.get('res.users').search(cr, uid, [('id', '=', uid)], context=context)
        if ids:
            return ids[0]
        return False
    
    
     
    _defaults={
               'user_id':_user_get,
               'date': lambda *a: str(datetime.now())
               }
commentaire()


class sale_order(models.Model):
    _inherit='sale.order'
    
    _columns={
              'delai_livraison':fields.date('Delai de livraison'),
              'da_ids':fields.one2many('purchase.exp.achat', 'sale_id', "Demande d'achat"),
              }
sale_order()

