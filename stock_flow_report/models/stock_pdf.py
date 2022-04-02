# -*- coding: utf-8 -*-

import time
from odoo import api, models, _
from odoo.exceptions import UserError
import datetime
from datetime import datetime


class stockflowreportPDF(models.AbstractModel):
    _name = 'report.stock_flow_report.report_stock_flow_report'

    def get_sale(self, data):

        lines = []

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        product_id = data['form']['product_id']
        category_id = data['form']['category_id']
        brand_id = data['form']['brand_id']

        sl = 0

        if category_id and product_id and brand_id:

            query = '''



                                          select a.product_name,a.product_id,
                                          		  a.inward_qty,
                                       		  a.inward_value,
                                       		  b.opening_qty,
                                       		  b.opening_value,
                                       		  c.outward_qty,
                                       		  c.outward_value,
                                       		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                                       		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                                       		  from
                                           (
                                           SELECT pt.name as product_name,
                                                   sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                                   m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                                           from stock_move m
                                                  JOIN stock_move_line ml
                                                    ON m.id = ml.move_id
                                                  JOIN purchase_order_line pol
                                                    ON pol.id = m.purchase_line_id
                                                  JOIN purchase_order po
                                                    ON po.id = pol.order_id
                                                  JOIN product_product p
                                                    ON p.id = m.product_id
                                                  JOIN product_template pt
                                                    ON pt.id = p.product_tmpl_id
                                                  JOIN product_category pc
                                                    ON pc.id = pt.categ_id
                                           WHERE  m.state = 'done'
                                           and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                                           AND pol.product_id=%s and pc.id=%s and po.company_id = %s
                                           and pt.product_brand_id = %s
                                           group by m.product_id,pt.id

                                                      )a 

                                       	    left join 

                                       	   (SELECT 
                               sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                                      m.product_id AS product_id,       
                                      Sum(pol.product_uom_qty) AS opening_qty
                               from stock_move m
                                      JOIN stock_move_line ml
                                        ON m.id = ml.move_id
                                      JOIN purchase_order_line pol
                                        ON pol.id = m.purchase_line_id
                                      JOIN purchase_order po
                                        ON po.id = pol.order_id
                                      JOIN product_product p
                                        ON p.id = m.product_id
                                      JOIN product_template pt
                                        ON pt.id = p.product_tmpl_id
                                      JOIN product_category pc
                                        ON pc.id = pt.categ_id
                               WHERE  m.state = 'done'
                               and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                               AND pol.product_id=%s and pc.id=%s and po.company_id = %s
                               and pt.product_brand_id = %s
                               group by m.product_id)b on a.product_id=b.product_id

                                       		   left join 
                                       		   (
                                       		     SELECT 
                               sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                                      m.product_id AS product_id,       
                                      Sum(sol.product_uom_qty) AS outward_qty
                               from stock_move m
                                      JOIN stock_move_line ml
                                        ON m.id = ml.move_id
                                      JOIN sale_order_line sol
                                        ON sol.id = m.purchase_line_id
                                      JOIN sale_order so
                                        ON so.id = sol.order_id
                                      JOIN product_product p
                                        ON p.id = m.product_id
                                      JOIN product_template pt
                                        ON pt.id = p.product_tmpl_id
                                      JOIN product_category pc
                                        ON pc.id = pt.categ_id
                               WHERE  m.state = 'done'
                               and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                               AND sol.product_id=%s and pc.id=%s and so.company_id = %s
                               and pt.product_brand_id = %s
                               group by m.product_id)c on c.product_id=a.product_id

                                                                  '''

            self.env.cr.execute(query, (
                date_from, date_to, product_id, category_id, company_id, brand_id,
                date_from, product_id, category_id, company_id, brand_id,
                date_from, date_to, product_id, category_id, company_id, brand_id,
            ))
            for row in self.env.cr.dictfetchall():

                mrp_value = 0

                query1 = '''
                                               SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
        							 FROM stock_move_line as sm
        							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                    left join product_product as pp on(pp.id=sr.product_id)
                                    left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                              WHERE sr.product_id = %s
                                            and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                            '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)
            if lines:
                return lines
            else:
                return []
        elif product_id and not category_id and brand_id:

            query = '''



                               select a.product_name,a.product_id,
                               		  a.inward_qty,
                            		  a.inward_value,
                            		  b.opening_qty,
                            		  b.opening_value,
                            		  c.outward_qty,
                            		  c.outward_value,
                            		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                            		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                            		  from
                                (
                                SELECT pt.name as product_name,
                                        sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                        m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                                from stock_move m
                                       JOIN stock_move_line ml
                                         ON m.id = ml.move_id
                                       JOIN purchase_order_line pol
                                         ON pol.id = m.purchase_line_id
                                       JOIN purchase_order po
                                         ON po.id = pol.order_id
                                       JOIN product_product p
                                         ON p.id = m.product_id
                                       JOIN product_template pt
                                         ON pt.id = p.product_tmpl_id
                                       JOIN product_category pc
                                         ON pc.id = pt.categ_id
                                WHERE  m.state = 'done'
                                and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                                AND pol.product_id=%s and po.company_id = %s
                                and pt.product_brand_id = %s
                                group by m.product_id,pt.id

                                           )a 

                            	    left join 

                            	   (SELECT 
                    sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                           m.product_id AS product_id,       
                           Sum(pol.product_uom_qty) AS opening_qty
                    from stock_move m
                           JOIN stock_move_line ml
                             ON m.id = ml.move_id
                           JOIN purchase_order_line pol
                             ON pol.id = m.purchase_line_id
                           JOIN purchase_order po
                             ON po.id = pol.order_id
                           JOIN product_product p
                             ON p.id = m.product_id
                           JOIN product_template pt
                             ON pt.id = p.product_tmpl_id
                           JOIN product_category pc
                             ON pc.id = pt.categ_id
                    WHERE  m.state = 'done'
                    and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                    AND pol.product_id=%s and po.company_id = %s
                    and pt.product_brand_id = %s
                    group by m.product_id)b on a.product_id=b.product_id

                            		   left join 
                            		   (
                            		     SELECT 
                    sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                           m.product_id AS product_id,       
                           Sum(sol.product_uom_qty) AS outward_qty
                    from stock_move m
                           JOIN stock_move_line ml
                             ON m.id = ml.move_id
                           JOIN sale_order_line sol
                             ON sol.id = m.purchase_line_id
                           JOIN sale_order so
                             ON so.id = sol.order_id
                           JOIN product_product p
                             ON p.id = m.product_id
                           JOIN product_template pt
                             ON pt.id = p.product_tmpl_id
                           JOIN product_category pc
                             ON pc.id = pt.categ_id
                    WHERE  m.state = 'done'
                    and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                    AND sol.product_id=%s and so.company_id = %s
                    and pt.product_brand_id = %s
                    group by m.product_id)c on c.product_id=a.product_id

                                                       '''

            self.env.cr.execute(query, (
                date_from, date_to, product_id, company_id, brand_id,
                date_from, product_id, company_id, brand_id,
                date_from, date_to, product_id, company_id, brand_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                               SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                        							 FROM stock_move_line as sm
                        							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                    left join product_product as pp on(pp.id=sr.product_id)
                                                    left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                              WHERE sr.product_id = %s
                                                            and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                            '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)
            if lines:
                return lines
            else:
                return []
        elif category_id and not product_id and brand_id:

            query = '''



                   select a.product_name,a.product_id,
                   		  a.inward_qty,
                		  a.inward_value,
                		  b.opening_qty,
                		  b.opening_value,
                		  c.outward_qty,
                		  c.outward_value,
                		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                		  from
                    (
                    SELECT pt.name as product_name,
                            sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                            m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                   from stock_move m
                           JOIN stock_move_line ml
                             ON m.id = ml.move_id
                           JOIN purchase_order_line pol
                             ON pol.id = m.purchase_line_id
                           JOIN purchase_order po
                             ON po.id = pol.order_id
                           JOIN product_product p
                             ON p.id = m.product_id
                           JOIN product_template pt
                             ON pt.id = p.product_tmpl_id
                           JOIN product_category pc
                             ON pc.id = pt.categ_id
                    WHERE  m.state = 'done'
                    and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                    AND pc.id=%s and po.company_id = %s
                    and pt.product_brand_id = %s
                    group by m.product_id,pt.id

                               )a 

                	    left join 

                	   (SELECT 
        sum(pol.product_uom_qty*pol.price_unit) as opening_value,
               m.product_id AS product_id,       
               Sum(pol.product_uom_qty) AS opening_qty
        from stock_move m
               JOIN stock_move_line ml
                 ON m.id = ml.move_id
               JOIN purchase_order_line pol
                 ON pol.id = m.purchase_line_id
               JOIN purchase_order po
                 ON po.id = pol.order_id
               JOIN product_product p
                 ON p.id = m.product_id
               JOIN product_template pt
                 ON pt.id = p.product_tmpl_id
               JOIN product_category pc
                 ON pc.id = pt.categ_id
        WHERE  m.state = 'done'
        and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
        AND pc.id=%s and po.company_id = %s
        and pt.product_brand_id = %s
        group by m.product_id)b on a.product_id=b.product_id

                		   left join 
                		   (
                		     SELECT 
        sum(sol.product_uom_qty*sol.price_unit) as outward_value,
               m.product_id AS product_id,       
               Sum(sol.product_uom_qty) AS outward_qty
        from stock_move m
               JOIN stock_move_line ml
                 ON m.id = ml.move_id
               JOIN sale_order_line sol
                 ON sol.id = m.purchase_line_id
               JOIN sale_order so
                 ON so.id = sol.order_id
               JOIN product_product p
                 ON p.id = m.product_id
               JOIN product_template pt
                 ON pt.id = p.product_tmpl_id
               JOIN product_category pc
                 ON pc.id = pt.categ_id
        WHERE  m.state = 'done'
        and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
        AND pc.id=%s and so.company_id = %s
        and pt.product_brand_id = %s
        group by m.product_id)c on c.product_id=a.product_id

                                           '''

            self.env.cr.execute(query, (
                date_from, date_to, category_id, company_id, brand_id,
                date_from, category_id, company_id, brand_id,
                date_from, date_to, category_id, company_id, brand_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                               SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                        							 FROM stock_move_line as sm
                                        							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                                    left join product_product as pp on(pp.id=sr.product_id)
                                                                    left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                              WHERE sr.product_id = %s
                                                                            and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                            '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []
        elif brand_id and not category_id and not product_id:

            query = '''



                           select a.product_name,a.product_id,
                           		  a.inward_qty,
                        		  a.inward_value,
                        		  b.opening_qty,
                        		  b.opening_value,
                        		  c.outward_qty,
                        		  c.outward_value,
                        		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                        		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                        		  from
                            (
                            SELECT pt.name as product_name,
                                    sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                    m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                           from stock_move m
                                   JOIN stock_move_line ml
                                     ON m.id = ml.move_id
                                   JOIN purchase_order_line pol
                                     ON pol.id = m.purchase_line_id
                                   JOIN purchase_order po
                                     ON po.id = pol.order_id
                                   JOIN product_product p
                                     ON p.id = m.product_id
                                   JOIN product_template pt
                                     ON pt.id = p.product_tmpl_id
                                   JOIN product_category pc
                                     ON pc.id = pt.categ_id
                            WHERE  m.state = 'done'
                            and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                            AND pc.id=%s and po.company_id = %s
                            and pt.product_brand_id = %s
                            group by m.product_id,pt.id

                                       )a 

                        	    left join 

                        	   (SELECT 
                sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                       m.product_id AS product_id,       
                       Sum(pol.product_uom_qty) AS opening_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN purchase_order_line pol
                         ON pol.id = m.purchase_line_id
                       JOIN purchase_order po
                         ON po.id = pol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                AND pc.id=%s and po.company_id = %s
                and pt.product_brand_id = %s
                group by m.product_id)b on a.product_id=b.product_id

                        		   left join 
                        		   (
                        		     SELECT 
                sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                       m.product_id AS product_id,       
                       Sum(sol.product_uom_qty) AS outward_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN sale_order_line sol
                         ON sol.id = m.purchase_line_id
                       JOIN sale_order so
                         ON so.id = sol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                AND pc.id=%s and so.company_id = %s
                and pt.product_brand_id = %s
                group by m.product_id)c on c.product_id=a.product_id

                                                   '''

            self.env.cr.execute(query, (
                date_from, date_to, category_id, company_id, brand_id,
                date_from, category_id, company_id, brand_id,
                date_from, date_to, category_id, company_id, brand_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                                       SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                                							 FROM stock_move_line as sm
                                                							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                                            left join product_product as pp on(pp.id=sr.product_id)
                                                                            left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                                      WHERE sr.product_id = %s
                                                                                    and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                                    '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []
        elif category_id and not product_id and not brand_id:

            query = '''



                           select a.product_name,a.product_id,
                           		  a.inward_qty,
                        		  a.inward_value,
                        		  b.opening_qty,
                        		  b.opening_value,
                        		  c.outward_qty,
                        		  c.outward_value,
                        		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                        		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                        		  from
                            (
                            SELECT pt.name as product_name,
                                    sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                    m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                           from stock_move m
                                   JOIN stock_move_line ml
                                     ON m.id = ml.move_id
                                   JOIN purchase_order_line pol
                                     ON pol.id = m.purchase_line_id
                                   JOIN purchase_order po
                                     ON po.id = pol.order_id
                                   JOIN product_product p
                                     ON p.id = m.product_id
                                   JOIN product_template pt
                                     ON pt.id = p.product_tmpl_id
                                   JOIN product_category pc
                                     ON pc.id = pt.categ_id
                            WHERE  m.state = 'done'
                            and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                            AND pc.id=%s and po.company_id = %s
                            group by m.product_id,pt.id

                                       )a 

                        	    left join 

                        	   (SELECT 
                sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                       m.product_id AS product_id,       
                       Sum(pol.product_uom_qty) AS opening_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN purchase_order_line pol
                         ON pol.id = m.purchase_line_id
                       JOIN purchase_order po
                         ON po.id = pol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                AND pc.id=%s and po.company_id = %s
                group by m.product_id)b on a.product_id=b.product_id

                        		   left join 
                        		   (
                        		     SELECT 
                sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                       m.product_id AS product_id,       
                       Sum(sol.product_uom_qty) AS outward_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN sale_order_line sol
                         ON sol.id = m.purchase_line_id
                       JOIN sale_order so
                         ON so.id = sol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                AND pc.id=%s and so.company_id = %s
                group by m.product_id)c on c.product_id=a.product_id

                                                   '''

            self.env.cr.execute(query, (
                date_from, date_to, category_id, company_id,
                date_from, category_id, company_id,
                date_from, date_to, category_id, company_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                                       SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                                							 FROM stock_move_line as sm
                                                							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                                            left join product_product as pp on(pp.id=sr.product_id)
                                                                            left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                                      WHERE sr.product_id = %s
                                                                                    and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                                    '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []
        elif product_id and category_id and not brand_id:

            query = '''



                                       select a.product_name,a.product_id,
                                       		  a.inward_qty,
                                    		  a.inward_value,
                                    		  b.opening_qty,
                                    		  b.opening_value,
                                    		  c.outward_qty,
                                    		  c.outward_value,
                                    		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                                    		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                                    		  from
                                        (
                                        SELECT pt.name as product_name,
                                                sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                                m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                                        from stock_move m
                                               JOIN stock_move_line ml
                                                 ON m.id = ml.move_id
                                               JOIN purchase_order_line pol
                                                 ON pol.id = m.purchase_line_id
                                               JOIN purchase_order po
                                                 ON po.id = pol.order_id
                                               JOIN product_product p
                                                 ON p.id = m.product_id
                                               JOIN product_template pt
                                                 ON pt.id = p.product_tmpl_id
                                               JOIN product_category pc
                                                 ON pc.id = pt.categ_id
                                        WHERE  m.state = 'done'
                                        and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                                        AND pol.product_id=%s and po.company_id = %s
                                        group by m.product_id,pt.id

                                                   )a 

                                    	    left join 

                                    	   (SELECT 
                            sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                                   m.product_id AS product_id,       
                                   Sum(pol.product_uom_qty) AS opening_qty
                            from stock_move m
                                   JOIN stock_move_line ml
                                     ON m.id = ml.move_id
                                   JOIN purchase_order_line pol
                                     ON pol.id = m.purchase_line_id
                                   JOIN purchase_order po
                                     ON po.id = pol.order_id
                                   JOIN product_product p
                                     ON p.id = m.product_id
                                   JOIN product_template pt
                                     ON pt.id = p.product_tmpl_id
                                   JOIN product_category pc
                                     ON pc.id = pt.categ_id
                            WHERE  m.state = 'done'
                            and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                            AND pol.product_id=%s and po.company_id = %s
                            group by m.product_id)b on a.product_id=b.product_id

                                    		   left join 
                                    		   (
                                    		     SELECT 
                            sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                                   m.product_id AS product_id,       
                                   Sum(sol.product_uom_qty) AS outward_qty
                            from stock_move m
                                   JOIN stock_move_line ml
                                     ON m.id = ml.move_id
                                   JOIN sale_order_line sol
                                     ON sol.id = m.purchase_line_id
                                   JOIN sale_order so
                                     ON so.id = sol.order_id
                                   JOIN product_product p
                                     ON p.id = m.product_id
                                   JOIN product_template pt
                                     ON pt.id = p.product_tmpl_id
                                   JOIN product_category pc
                                     ON pc.id = pt.categ_id
                            WHERE  m.state = 'done'
                            and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                            AND sol.product_id=%s and so.company_id = %s
                            group by m.product_id)c on c.product_id=a.product_id

                                                               '''

            self.env.cr.execute(query, (
                date_from, date_to, product_id, company_id,
                date_from, product_id, company_id,
                date_from, date_to, product_id, company_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                       SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                							 FROM stock_move_line as sm
                                							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                            left join product_product as pp on(pp.id=sr.product_id)
                                                            left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                      WHERE sr.product_id = %s
                                                                    and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                    '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)
            if lines:
                return lines
            else:
                return []
        elif product_id and not category_id and not brand_id:

            query = '''



                           select a.product_name,a.product_id,
                           		  a.inward_qty,
                        		  a.inward_value,
                        		  b.opening_qty,
                        		  b.opening_value,
                        		  c.outward_qty,
                        		  c.outward_value,
                        		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                        		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                        		  from
                            (
                            SELECT pt.name as product_name,
                                    sum(pol.product_uom_qty*pol.price_unit) as inward_value,
                                    m.product_id AS product_id,sum(pol.product_uom_qty) AS inward_qty
                           from stock_move m
                                   JOIN stock_move_line ml
                                     ON m.id = ml.move_id
                                   JOIN purchase_order_line pol
                                     ON pol.id = m.purchase_line_id
                                   JOIN purchase_order po
                                     ON po.id = pol.order_id
                                   JOIN product_product p
                                     ON p.id = m.product_id
                                   JOIN product_template pt
                                     ON pt.id = p.product_tmpl_id
                                   JOIN product_category pc
                                     ON pc.id = pt.categ_id
                            WHERE  m.state = 'done'
                            and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                            AND pc.id=%s and po.company_id = %s
                            group by m.product_id,pt.id

                                       )a 

                        	    left join 

                        	   (SELECT 
                sum(pol.product_uom_qty*pol.price_unit) as opening_value,
                       m.product_id AS product_id,       
                       Sum(pol.product_uom_qty) AS opening_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN purchase_order_line pol
                         ON pol.id = m.purchase_line_id
                       JOIN purchase_order po
                         ON po.id = pol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                AND pc.id=%s and po.company_id = %s
                group by m.product_id)b on a.product_id=b.product_id

                        		   left join 
                        		   (
                        		     SELECT 
                sum(sol.product_uom_qty*sol.price_unit) as outward_value,
                       m.product_id AS product_id,       
                       Sum(sol.product_uom_qty) AS outward_qty
                from stock_move m
                       JOIN stock_move_line ml
                         ON m.id = ml.move_id
                       JOIN sale_order_line sol
                         ON sol.id = m.purchase_line_id
                       JOIN sale_order so
                         ON so.id = sol.order_id
                       JOIN product_product p
                         ON p.id = m.product_id
                       JOIN product_template pt
                         ON pt.id = p.product_tmpl_id
                       JOIN product_category pc
                         ON pc.id = pt.categ_id
                WHERE  m.state = 'done'
                and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                AND pc.id=%s and so.company_id = %s
                group by m.product_id)c on c.product_id=a.product_id

                                                   '''

            self.env.cr.execute(query, (
                date_from, date_to, category_id, company_id,
                date_from, category_id, company_id,
                date_from, date_to, category_id, company_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                                       SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                                							 FROM stock_move_line as sm
                                                							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                                            left join product_product as pp on(pp.id=sr.product_id)
                                                                            left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                                      WHERE sr.product_id = %s
                                                                                    and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                                    '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []
        else:

            query = '''



                   select a.product_name,a.product_id,
                   		  a.inward_qty,
                		  a.inward_value,
                		  b.opening_qty,
                		  b.opening_value,
                		  c.outward_qty,
                		  c.outward_value,
                		  ((b.opening_qty+a.inward_qty)-c.outward_qty) as closing_qty,
                		  ((b.opening_value+a.inward_value)-c.outward_value) as closing_value

                		  from
                    (SELECT pt.name as product_name,sum(pl.product_qty) AS inward_qty,
                  		 sum(pl.product_qty*pl.price_unit) AS inward_value,
                		 pl.product_id FROM purchase_order_line AS pl
                      JOIN purchase_order AS po ON pl.order_id = po.id
                      left join product_product as p on (pl.product_id=p.id)
                	  left join product_template as pt on (pt.id=p.product_tmpl_id)
                	 left join product_category as pc on pc.id =pt.categ_id
                           WHERE po.state IN ('purchase','done')
                           and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date between %s and %s
                           AND po.company_id = %s group by pl.product_id,pt.id

                   )a 

                	    left join 

                	   (SELECT sum(pl.product_qty) AS opening_qty, 
                  		 sum(pl.product_qty*pl.price_unit) AS opening_value,
                		 pl.product_id FROM purchase_order_line AS pl
                      JOIN purchase_order AS po ON pl.order_id = po.id
                     left join product_product as p on (pl.product_id=p.id)
                	  left join product_template as pt on (pt.id=p.product_tmpl_id)
                	 left join product_category as pc on pc.id =pt.categ_id
                           WHERE po.state IN ('purchase','done')
                		   and  to_char(date_trunc('day',po.date_order),'YYYY-MM-DD')::date < %s
                           AND po.company_id = %s group by pl.product_id)b on a.product_id=b.product_id

                		   left join 
                		   (
                		     SELECT sum(sl.product_uom_qty) AS outward_qty,
                			   sum(sl.product_uom_qty*sl.price_unit) AS outward_value,sl.product_id FROM sale_order_line AS sl
                               JOIN sale_order AS so ON sl.order_id = so.id
                			   left join product_product as p on (sl.product_id=p.id)
                			  left join product_template as pt on (pt.id=p.product_tmpl_id)
                			 left join product_category as pc on pc.id =pt.categ_id
                               WHERE so.state IN ('sale','done')
                			   and  to_char(date_trunc('day',so.date_order),'YYYY-MM-DD')::date between %s and %s
                               AND so.company_id = %s group by sl.product_id)c on c.product_id=a.product_id

                                           '''

            self.env.cr.execute(query, (
                date_from, date_to, company_id,
                date_from, company_id,
                date_from, date_to, company_id
            ))
            for row in self.env.cr.dictfetchall():
                mrp_value = 0

                query1 = '''
                                                                               SELECT sr.product_id as product_id ,sr.name as mrp_value,sr.id as id
                                        							 FROM stock_move_line as sm
                                        							left join stock_mrp_product_report as sr on sr.id=sm.product_mrp
                                                                    left join product_product as pp on(pp.id=sr.product_id)
                                                                    left join product_template as pt on(pt.id=pp.product_tmpl_id)
                                                                              WHERE sr.product_id = %s
                                                                            and sm.company_id = %s ORDER BY sr.id DESC LIMIT 1
                                                                                            '''
                # query1 = '''
                # SELECT product_id,cost,id FROM product_price_history  WHERE product_id = %s and company_id = %s ORDER BY id DESC LIMIT 1
                # '''
                self.env.cr.execute(query1, (row['product_id'], company_id

                                             ))
                for ans in self.env.cr.dictfetchall():
                    mrp_value = ans['mrp_value'] if ans['mrp_value'] else 0
                sl += 1

                product_name = row['product_name'] if row['product_name'] else " "
                inward_qty = row['inward_qty'] if row['inward_qty'] else 0.0
                inward_value = row['inward_value'] if row['inward_value'] else 0.0
                opening_qty = row['opening_qty'] if row['opening_qty'] else 0.0
                opening_value = row['opening_value'] if row['opening_value'] else 0.0
                outward_qty = row['outward_qty'] if row['outward_qty'] else 0
                outward_value = row['outward_value'] if row['outward_value'] else 0

                closing_value = ((opening_value + inward_value) - outward_value)
                closing_qty = ((opening_qty + inward_qty) - outward_qty)

                # closing_qty = row['closing_qty'] if row['closing_qty'] else 0
                # closing_value = row['closing_value'] if row['closing_value'] else 0

                res = {
                    'sl_no': sl,
                    'product_name': product_name,
                    'inward_qty': inward_qty if inward_qty else 0.0,
                    'inward_value': inward_value if inward_value else 0.0,
                    'opening_qty': opening_qty if opening_qty else 0.0,
                    'opening_value': opening_value if opening_value else 0.0,
                    'outward_qty': outward_qty if outward_qty else 0.0,
                    'outward_value': outward_value if outward_value else 0.0,
                    'closing_qty': closing_qty if closing_qty else 0.0,
                    'closing_value': closing_value if closing_value else 0.0,
                    'mrp_value': mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []




    def _get_report_values(self, docids, data=None):
        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        product_id = data['form']['product_id']
        category_id = data['form']['category_id']


        get_sale = self.get_sale(data)

        date_object_startdate = datetime.strptime(date_from, '%Y-%m-%d').date()
        date_object_enddate = datetime.strptime(date_to, '%Y-%m-%d').date()

        docargs = {
            'doc_ids': docids,
            'doc_model': model,
            'data': data['form'],
            'date_start': date_object_startdate.strftime('%d-%m-%Y'),
            'date_end': date_object_enddate.strftime('%d-%m-%Y'),
            'docs': docs,
            'time': time,
            'get_sale': get_sale,

        }
        return docargs
