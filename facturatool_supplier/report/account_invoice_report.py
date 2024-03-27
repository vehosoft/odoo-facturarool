# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.addons.account.models.account_move import PAYMENT_STATE_SELECTION

from functools import lru_cache


class AccountInvoiceReport(models.Model):
    _inherit = "account.invoice.report"

    date = fields.Date(readonly=True, string="Fecha contable")
    ref = fields.Char(readonly=True, string="Referencia")

    @api.model
    def _select(self):
        resp = super(AccountInvoiceReport,self)._select()
        return resp+', move.date, move.ref'
