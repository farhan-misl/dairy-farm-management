# -*- coding: utf-8 -*-
# from odoo import http


# class DairyFarm(http.Controller):
#     @http.route('/dairy_farm/dairy_farm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dairy_farm/dairy_farm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('dairy_farm.listing', {
#             'root': '/dairy_farm/dairy_farm',
#             'objects': http.request.env['dairy_farm.dairy_farm'].search([]),
#         })

#     @http.route('/dairy_farm/dairy_farm/objects/<model("dairy_farm.dairy_farm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dairy_farm.object', {
#             'object': obj
#         })
