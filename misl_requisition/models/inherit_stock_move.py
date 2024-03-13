from odoo import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    requisition_line_id = fields.Many2one('requisition.product.service', string='Requisition Line No')
