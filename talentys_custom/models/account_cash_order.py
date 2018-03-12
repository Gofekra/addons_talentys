#-*- coding:utf-8 -*-

import time
from odoo import api, fields, models

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

