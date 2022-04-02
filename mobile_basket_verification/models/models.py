# -*- coding: utf-8 -*-

from odoo import models, fields, api
import logging

_logger = logging.getLogger(__name__)

class BasketVerification(models.TransientModel):
    _name = 'mobile.basket.verification'
    _description = 'Mobile basket verification'
    def basket_verify(self,barcode=None):
        result = {'status':False,'result':'Something wrong with basket code'}

        if barcode:
            basket_id = self.env['stock.basket'].search([('name','=',barcode),('status','=','occupy')])
            if not basket_id:
                return {'status':False,'result':'The basket either not allocated or not found.'}

            # basket_id = self.env['stock.basket'].search([('name','=',barcode)])
            move_line_ids = self.env['stock.move.line'].search([('basket_id','=',basket_id.id)])
            if move_line_ids:
                _logger.info('move_line_ids %s',move_line_ids)
                for moveline in move_line_ids:
                    moveline.write({'basket_verified':True})
                # move_line_ids.write({'basket_verified':True})
            # if basket_id:
                basket_id.write({'status':'vacant','picking_id':None})
                return  {'status':True,'result':'Basket Successfully Verified & Unallocated.'}
            else:
                return {'status':False,'result':'No product lines found against this basket.'}
            # picking_id = basket_id.picking_id
            # if basket_id:
            #     remove_basket = picking_id.write({'basket_ids':[(3,basket_id.id)]})
            #     basket_id.write({'status': 'vacant',
            #                         'picking_id':None})
            #     result = {'status':True,'result':'Basket Successfully Verified & Unallocated.'}
            # else:
            #     result = {'status':False,'result':'Basket not found'}
        return result
    def get_picking_details(self,barcode=None):
        vals = []
        picking_vals ={}
        picking_id = None
        if barcode:
            line_vals = []
            # basket_id = self.env['stock.basket'].search([('name','=',barcode),('status','=','occupy')])
            basket_id = self.env['stock.basket'].search([('name','=',barcode)])
            print('basket_id',basket_id)
            # if not basket_id:
            #     return {'status':False,'result':'There is no basket found for given barcode.'}

            # Get movelines against a basket
            if basket_id:
                moveline_ids = self.env['stock.move.line'].search([('basket_id','=',basket_id.id),('basket_verified','=',False)])
                if not moveline_ids:
                    _logger.info('move_line_ids %s',moveline_ids)

                    return {'status':False,'result':'There is no product lines found for given barcode.'}

                print('moveline_ids',moveline_ids)
                for move in moveline_ids:
                    picking_id = move.picking_id
                    break;
                # picking_id = basket_id.picking_id
                # picking_id = basket_id.picking_id
                print('picking_id',picking_id)
                partner_id = picking_id.partner_id
                if picking_id:
                    picking_vals = {'picking_id':picking_id.name,
                                    'sale_id':picking_id.sale_id.name,
                                    'partner_id':partner_id.name,
                                    'street':partner_id.street,
                                    'street1':partner_id.street2,
                                    'city':partner_id.city,
                                    'zip':partner_id.zip,
                                    'status':True}
                else:
                    result = {'status':False,'result':'There is no picking found for given barcode.'}
                print('picking vals',picking_vals)
                # val = {
                #         'picking_id':picking_id.name,
                #         'partner_id':picking_id.partner_id.name,
                #         'status':True
                #         }
                # for lines in picking_id.move_line_ids_without_package:
                #     line_vals.append({
                #         'lot_id':lines.lot_id.name,
                #         'product_id':lines.product_id.name,
                #         'qty_done':lines.qty_done,
                #         'product_mrp':lines.product_mrp.name,
                #         'product_uom':lines.product_uom_id.name,
                #         'customer_locations':lines.customer_locations.name,
                #         'expiration_date':lines.lot_id.expiration_date
                #     })
                for lines in moveline_ids:
                    line_vals.append({
                        'lot_id':lines.lot_id.name,
                        'product':lines.product_id.id,
                        'product_id':lines.product_id.name,
                        'qty_done':lines.qty_done,
                        'product_mrp':lines.product_mrp.name,
                        'product_uom':lines.product_uom_id.name,
                        'customer_locations':lines.customer_locations.name,
                        'expiration_date':lines.lot_id.expiration_date
                    })
                picking_vals['line_ids']=line_vals
                print('line vals',line_vals)
                print('picking_vals after append',picking_vals)
                vals.append(picking_vals)
                return picking_vals
            else:
                return {'status':False,'result':'There is no basket found for given barcode.'}

        result = {'status':False,'result':'There is no basket found for given barcode.'}
        print('result',result)
        return result
    def action_client_action(self):
        """ Open the mobile view specialized in handling barcodes on mobile devices.
        """
        return {
            'type': 'ir.actions.client',
            'tag': 'basket_verification_client_action',
            'target': 'fullscreen',
            'params': {
                # 'model': 'mobile.basket.verification',
                # 'inventory_id': self.id,
            }
        }
        return dict(action, target='fullscreen')
