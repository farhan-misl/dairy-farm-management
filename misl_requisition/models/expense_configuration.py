from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime


class ExpenseConfig(models.Model):
    """
    This model is responsible for the configuration of all Expense Types.

    """
    _name = 'expense.config'
    # _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'id desc'
    _description = 'This model is used for configuring expense types.'


    name = fields.Char(string = 'Name')
    expense_type = fields.Selection([
        ('periodic', 'Periodic'),
        ('required', 'Required'),
        ('exceptional', 'Exceptional'),
    ], default='periodic', string='Expense Type')

