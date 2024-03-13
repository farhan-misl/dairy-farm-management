from odoo import models, fields, api, _


class ApprovalHistory(models.Model):
    _name = 'approval.history'

    date = fields.Datetime('Date')
    from_stage = fields.Many2one('approval.config', string="From Stage")
    to_stage = fields.Many2one('approval.config', string='To Stage')
    user_id = fields.Many2one('res.users', 'User')
    action_type = fields.Selection(
        [
            ('create', 'Create'),
            ('approval', 'Approval'),
            ('cancel', 'Cancel'),
            ('reset', 'Reset')
        ]
    )
    requisition_id = fields.Many2one('requisition.master', string='Requisition')

