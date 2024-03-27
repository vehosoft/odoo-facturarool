# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, _, Command, tools
import base64
from datetime import timedelta


class AccountTourUploadBill(models.TransientModel):
    _inherit = 'account.tour.upload.bill'

    selection = fields.Selection(
        selection=lambda self: self._selection_values(),
        default="upload"
    )