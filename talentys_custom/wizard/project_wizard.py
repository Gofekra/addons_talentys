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
from odoo import exceptions

class create_task_template(models.TransientModel):
    _name="create.task.template"

    @api.model
    def _get_active_project(self):
        return self._context.get('active_id')

    project_id = fields.Many2one('project.project', required=True,string='Projet' , default=_get_active_project)
    
    @api.one
    def generate_task_template(self):
        task_obj = self.env['project.task']
        for task in self.project_id.type_ids :
            for t_temp in task.task_template_ids :
                task_obj.create({
                               'name': t_temp.name,
                               'planned_hours': t_temp.planned_hours,
                               'priority': t_temp.priority,
                               'alerte_mail': t_temp.alerte_mail,
                               'description': t_temp.description,
                               'stage_id': task.id,
                               'project_id': self.project_id.id,
                                           })


class create_task_notification(models.TransientModel):
    _name="create.task.notification"

    @api.model
    def _get_active_project(self):
        return self._context.get('active_id')

    project_id = fields.Many2one('project.project', required=True,string='Projet' , default=_get_active_project)
    
    @api.one
    def generate_task_notification(self):
        # wizard=self.browse(cr,uid,ids)
        task_obj = self.env['project.task']
        for task in self.project_id.tasks :

            if task.project_id.user_id.id != self._uid :
                raise exceptions.except_orm(_('Cette tâche est reservée au chef de projet'))

            if task.state != 'done' :
                user_from = 'openerp@talentys.ci'
                user_to = task.user_id.email
                subject = _('%s : Attribution de tâche') % (task.project_id.name)
                mail = _('Bonjour M/Mme,\n\nLa tâche ci-dessous vous a été attribuée :\nDescription : %s\nDate debut : %s \nDate fin : %s') % (task.name, task_obj.french_format(task.date_start), task_obj.french_format(task.date_end))
                task_obj.notif_mail(user_from, user_to, subject, mail, task)