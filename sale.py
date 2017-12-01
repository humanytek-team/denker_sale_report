# -*- coding: utf-8 -*-
from openerp import models, fields, api, _
from openerp.exceptions import UserError, RedirectWarning, ValidationError
from datetime import datetime, timedelta, date
import pytz


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"



    @api.multi
    def _compute_delivery_days(self):
        #print '_compute_delivery_days'
        for rec in self:
            #print '-----------'
            date_order = rec.order_id.date_order
            commitment_date = rec.order_id.commitment_date
            #print 'date_order: ',date_order
            #print 'commitment_date: ',commitment_date

            if date_order and commitment_date:
                date_order = datetime.strptime(str(date_order),"%Y-%m-%d %H:%M:%S")
                commitment_date = datetime.strptime(str(commitment_date),"%Y-%m-%d %H:%M:%S")

                days = int((commitment_date - date_order).days)

                rec.delivery_days = days
        return


    @api.multi
    def _compute_mail_qty(self):
        #print '_compute_mail_qty'
        for rec in self:
            qty = 0
            if rec.order_id.message_ids:
                for message in rec.order_id.message_ids:
                    if message.message_type in ('email','comment'):
                        qty += 1
                        rec.date_last_mail = message.date
                rec.mail_qty = qty
        return

    @api.multi
    def _get_commitment_date(self):
        #print '_get_commitment_date'
        for rec in self:
            if rec.order_id.commitment_date:
                #print 'entro'
                rec.commitment_date = rec.order_id.commitment_date
        return


    @api.multi
    def _compute_remaining_qty(self):
        #print '_compute_remaining_qty'
        for rec in self:
            remaining_qty = 0
            remaining_qty = rec.product_uom_qty - rec.qty_delivered
            rec.remaining_qty = remaining_qty
        return

    @api.multi
    def _compute_manufacturing_order(self):
        #print '_compute_manufacturing_order'
        MrpProduction = self.env['mrp.production']
        data = MrpProduction.search([('origin', 'in', [x.order_id.name for x in self])] )
        mapped_data = dict([(m.origin, m) for m in data])
        for rec in self:
            mo = mapped_data.get(rec.order_id.name, False)
            if mo:
                rec.manufacturing_order = mo.id
                rec.mo_date_start = mo.date_start
                rec.mo_date_finished = mo.date_finished
                rec.mo_source = mo.location_src_id and mo.location_src_id.id or False
                rec.mo_dest = mo.location_dest_id and mo.location_dest_id.id or False

                if rec.mo_source:
                    res = rec.product_id.with_context(location=rec.mo_source.id)._compute_quantities_dict\
                    (self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),\
                     self._context.get('from_date'), self._context.get('to_date'))
                    rec.mo_source_stock = res[rec.product_id.id]['qty_available']

                if rec.mo_dest:
                    res = rec.product_id.with_context(location=rec.mo_dest.id)._compute_quantities_dict\
                    (self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),\
                     self._context.get('from_date'), self._context.get('to_date'))
                    rec.mo_dest_stock = res[rec.product_id.id]['qty_available']

                #CALCULATE TOTAL STOCK
                res = rec.product_id._compute_quantities_dict\
                    (self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),\
                     self._context.get('from_date'), self._context.get('to_date'))
                rec.mo_stock_diff = res[rec.product_id.id]['qty_available'] - rec.product_uom_qty

        return




    @api.multi
    def _compute_mo_stock_diff(self):
        #print '_compute_mo_stock_diff'
        for rec in self:
            #CALCULATE TOTAL STOCK
            res = rec.product_id._compute_quantities_dict\
                (self._context.get('lot_id'), self._context.get('owner_id'), self._context.get('package_id'),\
                 self._context.get('from_date'), self._context.get('to_date'))
            rec.mo_stock_diff = res[rec.product_id.id]['qty_available'] - rec.product_uom_qty

        return


    @api.multi
    def _compute_days_to_date(self):
        #print '_compute_days_to_date'
        for rec in self:
            now = str(datetime.now())
            now = now.split('.')[0]
            now = datetime.strptime(str(now),"%Y-%m-%d %H:%M:%S")
            days_to_date = 0

            if rec.date_order:
                date_order = datetime.strptime(str(rec.date_order),"%Y-%m-%d %H:%M:%S")

                days = int((now - date_order).days)

                days_to_date = days
            rec.days_to_date = days_to_date
            if days_to_date > rec.delivery_days:
                rec.late = True
        return


    @api.multi
    def _compute_int_product_qty(self):
        #print '_compute_int_product_qty'
        for rec in self:
            rec.int_product_qty = rec.product_uom_qty
        return

    #delivery_days = fields.Float('Days',compute='_compute_delivery_days')
    delivery_days = fields.Integer('Days',compute='_compute_delivery_days')

    date_last_mail = fields.Datetime('Date Last Mail',compute='_compute_mail_qty')
    mail_qty = fields.Integer('Mail Qty',compute='_compute_mail_qty')

    date_order = fields.Datetime('Date Order', related='order_id.date_order', readonly=True)
    #date_order = fields.Date('Date Order', compute='_compute_date_order', readonly=True)

    commitment_date = fields.Datetime('Commitment Date', compute='_get_commitment_date')
    client_order_ref = fields.Char('Client order ref', related='order_id.client_order_ref', readonly=True)
    #remaining_qty = fields.Float('Remaining Qty',compute='_compute_remaining_qty')
    remaining_qty = fields.Integer('Remaining Qty',compute='_compute_remaining_qty')

    manufacturing_order = fields.Many2one('mrp.production','Manufacturing Order',compute='_compute_manufacturing_order',readonly=True)
    mo_date_start = fields.Date('MO Date Start',compute='_compute_manufacturing_order',readonly=True)
    mo_date_end = fields.Date('MO Date Finished',compute='_compute_manufacturing_order',readonly=True)
    mo_source = fields.Many2one('stock.location','MO Src',compute='_compute_manufacturing_order',readonly=True)
    mo_dest = fields.Many2one('stock.location','MO Dest',compute='_compute_manufacturing_order',readonly=True)
    #mo_source_stock = fields.Float('Src Stock',compute='_compute_manufacturing_order',readonly=True)
    mo_source_stock = fields.Integer('Src Stock',compute='_compute_manufacturing_order',readonly=True)
    #mo_dest_stock = fields.Float('Dest Stock',compute='_compute_manufacturing_order',readonly=True)
    mo_dest_stock = fields.Integer('Dest Stock',compute='_compute_manufacturing_order',readonly=True)
    #mo_stock_diff = fields.Float('Stock Difference',compute='_compute_mo_stock_diff',readonly=True)
    mo_stock_diff = fields.Integer('Stock Difference',compute='_compute_mo_stock_diff',readonly=True)

    #days_to_date = fields.Float('Days to Date',compute='_compute_days_to_date')
    days_to_date = fields.Integer('Days to Date',compute='_compute_days_to_date')
    late = fields.Boolean('Late',compute='_compute_days_to_date')
    int_product_qty = fields.Integer('Product qty',compute='_compute_int_product_qty')