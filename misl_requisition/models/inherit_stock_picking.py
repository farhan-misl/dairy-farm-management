from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    custom_requisition_id = fields.Many2one('requisition.master', 'Requisition', copy=False)

    # noinspection PyUnresolvedReferences
    @api.onchange('custom_requisition_id', 'picking_type_code')
    def onchange_requisition_id(self):
        for rec in self:
            if rec.custom_requisition_id and self.env.context.get('is_internal'):
                requisition = rec.custom_requisition_id
                rec.origin = requisition.name
                rec.picking_type_id = requisition.warehouse_src_id.int_type_id.id
                self.location_id = requisition.warehouse_src_id.int_type_id.default_location_dest_id.id
                self.location_dest_id = requisition.warehouse_id.int_type_id.default_location_dest_id.id
                stock_moves = []
                for prod_line in requisition.prod_serv_requisition_id:
                    rem_qty = prod_line.product_qty - prod_line.received_qty
                    if rem_qty > 0:
                        line_vals = self.get_stock_move_values(prod_line, requisition)
                        stock_moves.append(line_vals)

                rec.move_ids_without_package = [(6, 0, [])]

                rec.move_ids_without_package = [(0, 0, dict_item) for dict_item in stock_moves]

            else:
                rec.custom_requisition_id = False
                rec.move_ids_without_package = [(6, 0, [])]

    def get_stock_move_values(self, prod_line, requisition):
        return {
            'product_id': prod_line.product_id.id,
            'product_uom_qty': prod_line.product_qty - prod_line.received_qty,
            'product_uom': prod_line.product_uom_id.id,
            'date': requisition.date_required,
            'name': prod_line.product_id.name,
            'company_id': requisition.company_id,
            'requisition_line_id': prod_line.id,
            'location_dest_id': requisition.warehouse_id.int_type_id.default_location_dest_id.id,
            'location_id': requisition.warehouse_src_id.int_type_id.default_location_dest_id.id,
        }


