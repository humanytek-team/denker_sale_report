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

                rec.delivery_days = (commitment_date - date_order).days
        return

    # @api.multi
    # def _compute_mail_date(self):
    #     #print '_compute_mail_date'
    #     for rec in self:
    #         message_last_post = rec.order_id.message_last_post
    #         rec.date_last_mail = message_last_post
    #     return


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


    delivery_days = fields.Float('Days',compute='_compute_delivery_days')

    date_last_mail = fields.Datetime('Date Last Mail',compute='_compute_mail_qty')
    mail_qty = fields.Integer('Mail Qty',compute='_compute_mail_qty')

    date_order = fields.Datetime('Date Order', related='order_id.date_order', readonly=True)
    #commitment_date = fields.Datetime('Commitment Date', related='order_id.commitment_date', readonly=True)
    commitment_date = fields.Datetime('Commitment Date', compute='_get_commitment_date')
    client_order_ref = fields.Char('Client order ref', related='order_id.client_order_ref', readonly=True)

    remaining_qty = fields.Float('Remaining Qty',compute='_compute_remaining_qty')