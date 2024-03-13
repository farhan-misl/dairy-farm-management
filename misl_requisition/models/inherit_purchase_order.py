from odoo import models, fields, api


class InheritPurchaseOrder(models.Model):
    _order = 'id desc'
    _inherit = 'purchase.order'

    custom_requisition_id = fields.Many2one('requisition.master', string="Requisition Reference")

    @api.onchange('custom_requisition_id')
    def onchange_custom_requisition_id(self):
        for rec in self:
            if not rec.requisition_id and rec.custom_requisition_id:
                rec.date_order = fields.Datetime.now()

                line_dict_list = []
                for line in rec.custom_requisition_id.prod_serv_requisition_id:
                    if line.remaining_qty > 0:
                        line_vals = {
                            'product_id': line.product_id.id,
                            'product_qty': line.remaining_qty,
                            'product_uom': line.product_uom_id.id,
                            'name': line.product_id.display_name,
                            'date_planned': rec.custom_requisition_id.date_required,
                            'custom_requisition_line_id': line.id
                        }
                        line_dict_list.append(line_vals)

                rec.order_line = [(6, 0, [])]

                rec.order_line = [(0, 0, dict_item) for dict_item in line_dict_list]
                rec.picking_type_id = rec.custom_requisition_id.warehouse_id.in_type_id.id

    @api.onchange('requisition_id')
    def _onchange_requisition_id(self):
        super(InheritPurchaseOrder, self)._onchange_requisition_id()
        if self.requisition_id and not self.custom_requisition_id:
            self.custom_requisition_id = self.requisition_id.custom_requisition_id


class InheritPurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    custom_requisition_line_id = fields.Many2one('requisition.product.service', string='Requisition Line ID')
