from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
import datetime



class RequisitionLine(models.Model):
    _name = 'requisition.line'
    _description = 'Requisition Line'
    _order = 'id desc'


    name = fields.Char(string='Item Reference', copy=False, default=lambda self: self.env['ir.sequence'].next_by_code('requisition.line'), readonly=True, store=True)
    requisition_id = fields.Many2one('requisition.master', string='Requisition', index=True, ondelete='cascade')
    requisition_reference = fields.Char(related="requisition_id.name")
    

    product_id = fields.Many2one('product.product', 'Item')
    
    requisition_type = fields.Selection([
        ('product', 'Product/Goods'),
        ('service', 'Service'),
        ('manpower', 'Manpower'),
        ('money', 'Money'),
    ], related='requisition_id.requisition_type', string='Requisition Type')


    product_qty = fields.Float('Quantity', digits='Product Unit of Measure', default=0.0)
    received_qty = fields.Float('Receive Qty', digits='Product Unit of Measure', default=0.0)
    product_uom_id = fields.Many2one('uom.uom', 'UoM')
    delivery_date = fields.Date(string='Receiving Date')
    reason = fields.Char(string='Reason')

    manpower_requisition_id = fields.Many2one('requisition.manpower', 'Manpower Requisition ID')
    money_requisition_id = fields.Many2one('requisition.money', 'Money Requisition ID')
    prod_serv_requisition_id = fields.Many2one('requisition.product.service', 'Prod/Serv Requisition ID')

    job_id = fields.Char(string="hr.job")
    no_of_employees = fields.Integer(string="No of Employees")
    deadline = fields.Date(string='Deadline')


    amount = fields.Integer(string="Amount")
    expense_type = fields.Many2one('expense.config', 'Expense Sector')
    line_state = fields.Selection([
        ('approved', 'Approved'),
        ('refused', 'Refused'),
    ], string='State')

    
    
    

    def unlink(self):
        for requi_line in self:
            if requi_line.state != 'draft':
                raise UserError(_('You can only delete requisition lines in draft state'))

        return super(RequisitionLine, self).unlink()


   
    @api.onchange('product_id')
    def _product_onchange(self):
        product = self.product_id
        self.product_uom_id = self.product_id.uom_id.id
        return {'domain': {'product_uom_id': [('category_id', '=', product.uom_id.category_id.id)]}}



