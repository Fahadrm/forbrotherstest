import datetime
from odoo.exceptions import UserError
from datetime import datetime, date
import time
from odoo import api, models, _
from odoo.exceptions import UserError
from xlsxwriter.utility import xl_range, xl_rowcol_to_cell


class stockflowreportXls(models.AbstractModel):
    _name = 'report.stock_flow_report.action_stock_flow_report_xls'
    _inherit = 'report.report_xlsx.abstract'

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
                date_from, date_to, product_id, category_id, company_id,brand_id,
                date_from, product_id, category_id, company_id,brand_id,
                date_from, date_to, product_id, category_id, company_id,brand_id,
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
                date_from, date_to, product_id, company_id,brand_id,
                date_from, product_id, company_id,brand_id,
                date_from, date_to, product_id, company_id,brand_id
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
                date_from, date_to, category_id, company_id,brand_id,
                date_from, category_id, company_id,brand_id,
                date_from, date_to, category_id, company_id,brand_id
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
                    'mrp_value':mrp_value if mrp_value else 0.0

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
                date_from, date_to, category_id, company_id,brand_id,
                date_from, category_id, company_id,brand_id,
                date_from, date_to, category_id, company_id,brand_id
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
                    'mrp_value':mrp_value if mrp_value else 0.0

                }

                lines.append(res)

            if lines:
                return lines
            else:
                return []

    def generate_xlsx_report(self, workbook, data, lines):

        if not data.get('form') or not self.env.context.get('active_model'):
            raise UserError(_("Form content is missing, this report cannot be printed."))

        sheet = workbook.add_worksheet(_('Stock Flow Report'))
        sheet.set_landscape()
        sheet.set_default_row(25)
        sheet.fit_to_pages(1, 0)
        sheet.set_zoom(80)
        # sheet.set_column(0, 0, 14)
        # sheet.set_column(1, 1, 45)
        # sheet.set_column(2, 2, 22)
        # sheet.set_column(3, 5, 18)
        # sheet.set_column(4, 5, 20)


        # sheet.set_column(1, 1, 20)
        # sheet.set_column(2, 2, 25)
        # sheet.set_column(3, 3, 25)
        # sheet.set_column(4, 4, 20)
        # sheet.set_column(5, 5, 25)
        # sheet.set_column(6, 6, 20)
        # sheet.set_column(7, 7, 20)
        # sheet.set_column(8, 8, 20)
        # sheet.set_column(9, 9, 20)
        # sheet.set_column(10, 10, 20)
        # sheet.set_column(11, 11, 20)
        # sheet.set_column(12, 12, 20)
        # sheet.set_column(13, 13, 20)
        # sheet.set_column(14, 14, 20)
        # sheet.set_column(15, 15, 20)
        # sheet.set_column(16, 16, 20)
        # sheet.set_column(17, 17, 20)
        # sheet.set_column(18, 18, 20)
        # sheet.set_column(19, 19, 20)
        # sheet.set_column(20, 20, 20)
        # sheet.set_column(21, 21, 30)
        # sheet.set_column(22, 22, 20)
        # sheet.set_column(23, 23, 20)
        # sheet.set_column(24, 24, 20)

        company = self.env['res.company'].browse(data['form']['company_id'])

        date_from = data['form']['date_from']
        date_to = data['form']['date_to']
        company_id = data['form']['company_id']
        brand_id = data['form']['brand_id']
        # target_move = data['form']['target_move']
        if company.street:
            res = company.street
        else:
            res=""
        if company.street2:
            res2 = company.street2
        else:
            res2 = ""


        date_start = data['form']['date_from']
        date_end = data['form']['date_to']
        if date_start:

            date_object_date_start = datetime.strptime(date_start, '%Y-%m-%d').date()
        if date_end:
            date_object_date_end = datetime.strptime(date_end, '%Y-%m-%d').date()


        font_size_8 = workbook.add_format({'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14})
        font_size_8_center = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'center'})
        font_size_8_right = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'right'})
        font_size_8_left = workbook.add_format(
            {'bottom': True, 'top': True, 'left': True, 'font_size': 14, 'align': 'left'})

        formattotal = workbook.add_format(
            {'bg_color': 'e2e8e8', 'font_size': 14, 'bottom': True, 'right': True, 'left': True, 'top': True,
             'align': 'right', 'bold': True})


        blue_mark2 = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14, 'bold': True,
             'color': 'ffffff', 'bg_color': '7b0b5b', 'align': 'center'})
        font_size_8blod = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 14, 'bold': True, })

        blue_mark3 = workbook.add_format(
            {'bottom': True, 'top': True, 'right': True, 'left': True, 'font_size': 18, 'bold': True,
             'color': 'ffffff', 'bg_color': '7b0b5b', 'align': 'center'})

        title_style = workbook.add_format({'font_size': 14, 'bold': True,
                                           'bg_color': '000000', 'color': 'ffffff',
                                           'bottom': 1, 'align': 'center'})
        account_style = workbook.add_format({'font_size': 14, 'bold': True,
                                           'bg_color': '929393', 'color': 'ffffff',
                                           'bottom': 1, 'align': 'left'})

        sheet.set_column(1, 1, 20)
        sheet.set_column(2, 2, 25)
        sheet.set_column(3, 3, 25)
        sheet.set_column(4, 4, 20)
        sheet.set_column(5, 5, 25)
        sheet.set_column(6, 6, 20)
        sheet.set_column(7, 7, 20)
        sheet.set_column(8, 8, 20)
        sheet.set_column(9, 9, 20)
        sheet.set_column(10, 10, 20)
        sheet.set_column(11, 11, 20)
        sheet.set_column(12, 12, 20)
        sheet.set_column(13, 13, 20)
        sheet.set_column(14, 14, 20)
        sheet.set_column(15, 15, 20)
        sheet.set_column(16, 16, 20)
        sheet.set_column(17, 17, 20)
        sheet.set_column(18, 18, 20)
        sheet.set_column(19, 19, 20)
        sheet.set_column(20, 20, 20)
        sheet.set_column(21, 21, 30)
        sheet.set_column(22, 22, 20)
        sheet.set_column(23, 23, 20)
        sheet.set_column(24, 24, 20)

        sheet.merge_range('A1:K1', company.name, blue_mark3)
        sheet.merge_range('A2:K2', res + " ," + res2, blue_mark2)
        sheet.merge_range('A3:K3', "Stock Flow Report", blue_mark2)

        model = self.env.context.get('active_model')
        docs = self.env[model].browse(self.env.context.get('active_ids', []))

        if date_start and date_end:

            sheet.merge_range('A5:H5',
                              "Date : " + date_object_date_start.strftime('%d-%m-%Y') + " to " + date_object_date_end.strftime(
                                  '%d-%m-%Y'), font_size_8blod)
        elif date_start:
            sheet.merge_range('A5:H5', "Date : " + date_object_date_start.strftime('%d-%m-%Y'),
                              font_size_8blod)

        sheet.write('A6', "Sl No.", title_style)

        sheet.write('B6', "ItemName", title_style)
        sheet.write('C6', "Last MRP", title_style)
        sheet.write('D6', "Opening Qty", title_style)
        sheet.write('E6', "Opening Value", title_style)
        sheet.write('F6', "Inwards Qty", title_style)
        sheet.write('G6', "Inwards Value", title_style)
        sheet.write('H6', "Outwards Qty", title_style)
        sheet.write('I6', "Outwards Value", title_style)
        sheet.write('J6', "Closing Qty", title_style)
        sheet.write('K6', "Closing Value", title_style)

        linw_row = 6
        line_column = 0

        for line in self.get_sale(data):
            sheet.write(linw_row, line_column, line['sl_no'], font_size_8_center)
            sheet.write(linw_row, line_column + 1, line['product_name'], font_size_8_left)
            sheet.write(linw_row, line_column + 2, '{0:,.2f}'.format(float(line['mrp_value'])), font_size_8_center)


            sheet.write(linw_row, line_column + 3, '{0:,.2f}'.format(float(line['opening_qty'])), font_size_8_center)
            sheet.write(linw_row, line_column + 4, '{0:,.2f}'.format(float(line['opening_value'])), font_size_8_center)
            sheet.write(linw_row, line_column + 5, '{0:,.2f}'.format(float(line['inward_qty'])), font_size_8_center)
            sheet.write(linw_row, line_column + 6, '{0:,.2f}'.format(float(line['inward_value'])), font_size_8_center)

            sheet.write(linw_row, line_column + 7, '{0:,.2f}'.format(float(line['outward_qty'])), font_size_8_center)
            sheet.write(linw_row, line_column + 8, '{0:,.2f}'.format(float(line['outward_value'])), font_size_8_center)
            sheet.write(linw_row, line_column + 9, '{0:,.2f}'.format(float(line['closing_qty'])), font_size_8_center)
            sheet.write(linw_row, line_column + 10, '{0:,.2f}'.format(float(line['closing_value'])), font_size_8_center)

            linw_row = linw_row + 1
            line_column = 0

        line_column = 0

        sheet.merge_range(linw_row, 0, linw_row, 2, "TOTAL", font_size_8_left)

        # total_cell_range2 = xl_range(8, 2, linw_row - 1, 2)
        total_cell_range3 = xl_range(6, 3, linw_row - 1, 3)
        total_cell_range = xl_range(6, 4, linw_row - 1, 4)
        total_cell_range11 = xl_range(6, 5, linw_row - 1, 5)
        total_cell_range6 = xl_range(6, 6, linw_row - 1, 6)
        total_cell_range7 = xl_range(6, 7, linw_row - 1, 7)
        total_cell_range8 = xl_range(6, 8, linw_row - 1, 8)
        total_cell_range9 = xl_range(6, 9, linw_row - 1, 9)
        total_cell_range10 = xl_range(6, 10, linw_row - 1, 10)

        # sheet.write_formula(linw_row, 2, '=SUM(' + total_cell_range2 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 3, '=SUM(' + total_cell_range3 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 4, '=SUM(' + total_cell_range + ')', font_size_8_center)
        sheet.write_formula(linw_row, 5, '=SUM(' + total_cell_range11 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 6, '=SUM(' + total_cell_range6 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 7, '=SUM(' + total_cell_range7 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 8, '=SUM(' + total_cell_range8 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 9, '=SUM(' + total_cell_range9 + ')', font_size_8_center)
        sheet.write_formula(linw_row, 10, '=SUM(' + total_cell_range10 + ')', font_size_8_center)



