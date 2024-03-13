from odoo import models, fields, api


class EmployeeTransfer(models.Model):
    _inherit = 'misl.hr.transfer'

    requisition_id = fields.Many2one('requisition.master', string='Requisition No.')