# -*- encoding: utf-8 -*-

from odoo import fields, models, api
from odoo import exceptions


class company(models.Model):
    _inherit = 'res.company'

    @api.onchange('dg_id' , 'resp_finance_id' , 'res_support_id' , 'res_projet_id' , 'res_informatique_id' , 'res_achat_id' , 'res_caisse_id' , 'res_crh')
    def onchange_param_id(self, cr, uid, ids, param_id, param=False):
        if not param_id :
            return {}

        emp_obj = self.env['hr.employee']
        if self.dg_id:
            emp = self.browse(self.dg_id.id)
            if not emp.work_email :
                raise  exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")

            self.mail_direction_gle = emp.work_email
            self.signature_dg = emp.user_id.signature_numerique

        if self.resp_finance_id:
            emp = self.browse(self.resp_finance_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")

            self.mail_dep_finance = emp.work_email,
            self.signature_finance = emp.user_id.signature_numerique

        if self.res_support_id:
            emp = self.browse(self.res_support_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_support = emp.work_email

        if self.res_projet_id:
            emp = self.browse(self.res_projet_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_projet = emp.work_email

        if self.res_informatique_id:
            emp = self.browse(self.res_informatique_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_res_informatique = emp.work_email

        if self.res_achat_id:
            emp = self.browse(self.res_achat_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_sce_achat = emp.work_email

        if self.res_crh:
            emp = self.browse(self.res_crh.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_res_crh = emp.work_email


        elif self.res_caisse_id:
            emp = self.browse(self.res_caisse_id.id)
            if not emp.work_email:
                raise exceptions.except_orm('Erreur', "Veuillez renseigner l'adresse mail de l'employe")
            self.mail_sce_caisse = emp.work_email

    dg_id = fields.Many2one('hr.employee', 'Directeur Général', required=False)
    resp_finance_id = fields.Many2one('hr.employee', 'Responsable des Finances', required=False)
    res_support_id = fields.Many2one('hr.employee', 'Responsable Sce Support', required=False)
    res_projet_id = fields.Many2one('hr.employee', 'Responsable Sce Projet', required=False)
    res_informatique_id = fields.Many2one('hr.employee', 'Responsable Informatique', required=False)
    res_achat_id = fields.Many2one('hr.employee', 'Responsable des Achat', required=False)
    res_caisse_id = fields.Many2one('hr.employee', 'Chargé de caisse', required=False)
    res_crh = fields.Many2one("hr.employee","Responsable des RH",required=False)
    signature_dg = fields.Binary('Signature DG')
    signature_finance = fields.Binary('Signature Resp. Finances')
    mail_sce_achat = fields.Char('Email Chargé des Achat')
    mail_sce_caisse = fields.Char('Email Chargé de Caisse')
    mail_dep_finance = fields.Char('Email Département Finance')
    mail_direction_gle = fields.Char('Email Direction générale')
    mail_support = fields.Char('Email Support')
    mail_projet = fields.Char('Email Projet')
    mail_res_informatique = fields.Char('Email Département Informatique')
    mail_res_crh = fields.Char("Email Departement des RH")
    pied_page = fields.Binary('Pied de page')