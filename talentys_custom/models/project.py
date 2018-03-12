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
from odoo.tools.translate import _
from datetime import timedelta, datetime
from odoo.exceptions import AccessError, MissingError, ValidationError, UserError
from lxml import etree

import time
import logging

_logger = logging.getLogger(__name__)


class project_category(models.Model):
    _name = "project.category"
    _description = "Category of project's task, issue, ..."

    name = fields.Char('Name', size=64, required=True, translate=True)


class project_task(models.Model):
    _inherit = 'project.task'
    
    @api.model
    def _company_param_get(self,param):
        results = self.env['res.company'].browse(1)
        if results:
            return results[0][param]
        return False

    @api.one
    def send_notification(self, email_template,users_from,users_to=None,subject=None,msg=None,context=None):
        tmp_id = self.env['ir.model.data'].get_object_reference('talentys_custom', email_template)[1]

        try:
            mail_tmp = self.env['mail.template'].browse(tmp_id)

            if users_to:
                mail_tmp.email_to = users_to

            if subject:
                mail_tmp.subject = subject

            if msg:
                mail_tmp.body_html = """
                <![CDATA[
                
                      {}
            
                     <p>Cordialement.</p>

                ]]>
            
            """.format(msg)

            mail_tmp.send_mail(res_id=self.id, force_send=True)
            return True
        except:
            return False

    @api.one
    def send_alert(self):
        ids = []
        send_mail = False
        cr = self._cr
        cr.execute('select * from project_task where state <> %s',('done',))
        tasks = cr.fetchall()
        for task in tasks :
            ids.append(task[0])

        task_ids = self
        email_from = 'openerp@talentys.ci'

        if self.date_end :
            end_date = datetime.strptime(task_ids.date_end, '%Y-%m-%d %H:%M:%S')
            duration_delta = timedelta(0, task_ids.delai * 60 * 60)
            date_delay = end_date - duration_delta
            if time.strftime('%Y-%m-%d',time.localtime()) >= str(date_delay) :
                dest_projet = self._company_param_get('mail_projet')
                dest_departement = self._company_param_get('mail_res_informatique')

                email_to = self.project_id.user_id.email
                subject = _("%s - Alerte d'exécution de tâche") % (self.project_id.name)
                body = _("La tâche suivante pourrait être en retard d'exécution\n\nProjet : %s\nTâche : %s\nAssigné à : %s\nDélai : %s") % (self.project_id.name, self.name, self.user_id.name, self.date_end)
                print 'Tâche non exécutée dans le temps !'
                #self.notif_mail(cr, uid, email_from, email_to, subject, body)
                #raise osv.except_osv('warning', time.strftime('%Y-%m-%d %H:%M:%S',time.localtime()))
                ir_mail_server = self.env['ir.mail_server']
                msg = ir_mail_server.build_email(email_from, [email_to], subject, body)
                ir_mail_server.send_email(msg)
                msg = ir_mail_server.build_email(email_from, [dest_projet], subject, body)
                ir_mail_server.send_email(msg)
                msg = ir_mail_server.build_email(email_from, [dest_departement], subject, body)
                ir_mail_server.send_email(msg)

        return True
    
    @api.model
    def notif_mail(self, user_from, user_to, subject, mail, task):

        employee_id = False
        responsible_email = False
        if task.alerte_mail :

            if not task.user_id.email :
                raise UserError('Attention',"Veuiller renseigner l'adresse mail de l'utilisateur au niveau du formulaire utilisateur de ce dernier")
            resource_ids = self.env['resource.resource'].search([('user_id','=',task.user_id.id)])

            if resource_ids :
                employee_ids = self.env['hr.employee'].search([('resource_id','=',resource_ids[0].id)])
                if employee_ids :
                    employee_id = employee_ids[0].id
                    responsible_email = self.env['hr.employee'].browse(employee_id).parent_id.work_email

            if not responsible_email :
                raise UserError('Attention',_("Veuiller renseigner l'adresse mail du responsable de l'utilisateur sur sa fiche employé"))

            self.send_notification('alerte_execution_tache_notif',user_from,user_to,subject,mail)
                  
        return True
    
    @api.one
    def notif_task(self,objet):
        task = self
        ids = self._ids
        sujet = _('%s / %s : %s') % (task.project_id.name, task.name, objet)
        message = _('%s\nPar : %s') % (sujet, task.user_id.name)
        emetteur = 'openerp@talentys.ci'

        if task.project_id.user_id.email :
            mail_projet = self.env['purchase.exp.besoin']._company_param_get(ids, 'mail_projet')
            mail_departement_tech = self.env['purchase.exp.besoin']._company_param_get(ids, 'mail_res_informatique')
            destinataire = task.project_id.user_id.email
            self.send_notification('alerte_execution_tache_notif', emetteur, destinataire, sujet, message)
            self.send_notification('alerte_execution_tache_notif', emetteur, mail_projet, sujet, message)
            self.send_notification('alerte_execution_tache_notif', emetteur, mail_departement_tech, sujet, message)
        
        return True

    def french_format(self, english_date):
        if english_date :
            french_date = ('%s/%s/%s %s:%s:%s') % (english_date[8:10], english_date[5:7], english_date[0:4], english_date[11:13], english_date[14:16], english_date[17:19])
            return str(french_date)
        
        return 'N/A'
    

    @api.one
    def notif_user(self):
        task = self
        if task.project_id.user_id.id != self._uid :
            raise UserError('Warning', _('Cette tâche est reservée au chef de projet'))

        if task.state != 'done' :
            user_from = 'openerp@talentys.ci'
            user_to = task.user_id.email
            subject = _('%s : Attribution de tâche') % (task.project_id.name)
            mail = _('Bonjour M/Mme,\n\nLa tâche ci-dessous vous a été attribuée :\nDescription : %s\nDate debut : %s \nDate fin : %s') % (task.name, self.french_format(task.date_start), self.french_format(task.date_end))
            self.send_notification('alerte_execution_tache_notif', user_from, user_to, subject, mail)
        
        return True
    
    @api.one
    def action_close(self):
        res_id = super(project_task, self).action_close()
        self._cr.execute('select name, sequence, user_id from project_task where project_id=%s and sequence < %s and state <> %s order by sequence',(self.project_id.id, self.sequence, 'done'))
        tasks = self._cr.fetchall()
        task_seq = ''
        user_name = ''
        resource_id = False

        if not self.work_ids :
            raise UserError('Attention',_('Veuillez renseigner le résumé de vos tâches à l\'onglet << Description >>'))

        if tasks :
            for task in tasks :
                resource_ids = self.env['resource.resource'].search([('user_id','=',task[2])])
                if resource_ids :
                    resource_id = resource_ids[0].id
                    user_name = self.env['resource.resource'].browse(resource_id).name

                task_seq = task_seq + _(' %s, \t Séquence : %s, Assigné à : %s\n') % (task[0], task[1], user_name)

            task_seq = _('Les tâches ci-desous doivent être terminées avant la fermeture de cette tâche :\n %s') % (task_seq)
            raise UserError('Attention',task_seq)
            
        self.notif_task(_('Tâche terminée'))
        
        return res_id 
    
    @api.one
    def do_cancel(self):
        res_id = super(project_task, self).action_close()
        self.notif_task(_('Tâche annulée'))
        return res_id
    
    @api.model
    def create(self,vals):
        res_id = super(project_task, self).create(vals)

        if vals.get('alerte_mail') :
            self.send_notification('alerte_attribution_tache')
        return res_id 
    
    @api.one
    @api.depends('kanban_state')
    def _get_state(self):
        self.state = self.kanban_state


    def send_mail(self,user_from, user_to, subject, mail):
        ir_mail_server = self.env['ir.mail_server']
        msg = ir_mail_server.build_email(user_from, [user_to], subject, mail)
        return ir_mail_server.send_email(msg)

    alerte_mail = fields.Boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement des e-mails au responsable du projet", default=True)
    delai =  fields.Integer('Délai alerte (h)')
    name  = fields.Char('Task Summary', size=128, required=True)
    project_id =  fields.Many2one('project.project', 'Project', ondelete='set null', track_visibility='onchange')

    planned_hours = fields.Float('Initially Planned Hours', help='Estimated time to do the task, usually set by the project manager when the task is in draft state.')
    date_start =  fields.Datetime('Starting Date')
    date_end = fields.Datetime('Ending Date')
    date_deadline = fields.Date('Deadline')

    categ_ids = fields.Many2many('project.category', string='Tags')

    #Modele source inexistant
    # work_ids = fields.One2many('project.task.work', 'task_id', 'Work done', states={'done':[('readonly',True)]})
    parent_ids = fields.Many2many('project.task', 'project_task_parent_rel', 'task_id', 'parent_id', 'Parent Tasks')
    child_ids =  fields.Many2many('project.task', 'project_task_parent_rel', 'parent_id', 'task_id', 'Delegated Tasks')
    priority = fields.Selection([('4','Very Low'), ('3','Low'), ('2','Medium'), ('1','Important'), ('0','Very important')], 'Priority')
    sequence = fields.Integer('Sequence',help="Gives the sequence order when displaying a list of tasks.")
    partner_id = fields.Many2one('res.partner', 'Customer')
    sale_line_id = fields.Many2one('sale.order.line', 'Ligne de commande')

    state = fields.Selection([
        ('normal', 'In Progress'),
        ('done', 'Ready for next stage'),
        ('blocked', 'Blocked')
    ], string='State' , compute='_get_state'  , store=True)

class project_task_reevaluate(models.TransientModel):
    _name="project.task.reevaluate"

    @api.one
    def compute_hours(self):
        super(project_task_reevaluate, self).compute_hours()
        if self._context is None:
            context = {}
        task_obj = self.env['project.task']
        task_id = self._context.get('active_id')
        task_obj.notif_task([task_id], _('Tâche réouverte'))
        
        return True

    @api.model
    def _get_remaining(self):
        if self._context is None:
            context = {}
        active_id = self._context.get('active_id', False)
        res = False
        if active_id:
            res = self.env['project.task'].browse(active_id).remaining_hours
        return res


    remaining_hours = fields.Float('Remaining Hours', digits=(16, 2),
                                            help="Put here the remaining hours required to close the task." , default=_get_remaining),

    def fields_view_get(self, cr, uid, view_id=None, view_type='form', context=None, toolbar=False, submenu=False):
        res = super(project_task_reevaluate, self).fields_view_get(cr, uid, view_id, view_type, context, toolbar,
                                                                   submenu=submenu)
        users_pool = self.pool.get('res.users')
        time_mode = users_pool.browse(cr, uid, uid, context).company_id.project_time_mode_id
        time_mode_name = time_mode and time_mode.name or 'Hours'
        if time_mode_name in ['Hours', 'Hour']:
            return res

        eview = etree.fromstring(res['arch'])

        def _check_rec(eview):
            if eview.attrib.get('widget', '') == 'float_time':
                eview.set('widget', 'float')
            for child in eview:
                _check_rec(child)
            return True

        _check_rec(eview)

        res['arch'] = etree.tostring(eview)

        for field in res['fields']:
            if 'Hours' in res['fields'][field]['string']:
                res['fields'][field]['string'] = res['fields'][field]['string'].replace('Hours', time_mode_name)
        return res


class project_task_template(models.Model):
    _name='project.task.template'

    name = fields.Char('Résumé de la tâche', size=64, required=True, readonly=False)
    planned_hours = fields.Float('Heures prévues initialement')
    categ_ids = fields.Many2many('project.category', string='Catégorie')
    priority = fields.Selection([('4','Très basse'), ('3','Basse'), ('2','Moyenne'), ('1','Important'), ('0','Très important')], 'Priorité', index=True)
    delai = fields.Integer('Délai alerte (h)' , default=4)
    alerte_mail = fields.Boolean("Envoi de mail", help="Si coché, permet d'envoyer automatiquement des e-mails au responsable du projet")
    task_type_id =fields.Many2one('project.task.type', 'Etape du projet')
    sequence = fields.Integer('Sequence')
    description = fields.Text('Description')


class project_task_type(models.Model):
    _inherit='project.task.type'

    use_template = fields.Boolean('Utiliser un modèle de tâche')
    task_template_ids = fields.One2many('project.task.template', 'task_type_id', 'Templates de tâche')


class project_task_alert(models.Model):
    _name='project.task.alert'

    name = fields.Char('Libellé', size=64, required=False, readonly=False)
    hours = fields.Integer("Nombre d'heure(s)")


class project_configuration(models.TransientModel):
    _inherit = 'project.config.settings'

    hours_alert = fields.Boolean("Délai d'alerte des tâches en heure(s)",
                                 help="Alerte pour une tâche non exécutée dans le délai"),
    nb_hours =  fields.Integer("Nombre d'heure",
                               help="Nombre d'heures limites avant émission d'une alerte pour une tâche non exécutée dans le délai")
    

    @api.one
    def execute(self):
        res_id = super(project_configuration, self).execute()
        self.write({'hours_alert': self.hours_alert, 'nb_hours': self.nb_hours, })
        return res_id


# class project_task_delegate(models.Model):
#     _inherit='project.task.delegate'
#
#     @api.one
#     def delegate(self):
#         res_id = super(project_task_delegate, self).delegate()
#         task_obj = self.env['project.task']
#         user_actu = False
#
#         if self._context is None:
#             context = {}
#         task_id = self._context.get('active_id', False)
#         task = task_obj.browse(task_id)
#
#         user_actu = self.user_id.name
#
#         if task.alerte_mail:
#             emetteur = 'openerp@talentys.ci'
#             subject = _('%s : Délégation de tâche') % (task.project_id.name)
#             mail = _('Bonjour M/Mme,\n\nLa tâche ci-dessous vous a été déléguée à %s :\nDescription : %s\nDate debut : %s \nDate fin : %s') % (user_actu, task.name, task_obj.french_format(task.date_start), task_obj.french_format(task.date_end))
#             destinataire_task_prec = task.user_id.email
#             destinataire_chef_projet = task.project_id.user_id.email
#             task_obj.send_mail(emetteur, destinataire_task_prec, subject, mail)
#             task_obj.send_mail(emetteur, destinataire_chef_projet, subject, mail)
#
#         return res_id