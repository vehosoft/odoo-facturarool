# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.tools import remove_accents
import logging
import re

_logger = logging.getLogger(__name__)

class AccountJournal(models.Model):
    _inherit = "account.journal"

    def _create_document_from_attachment(self, attachment_ids=None):
        _logger.debug('===== _create_document_from_attachment attachment_ids = %r',attachment_ids)
        ###
        new_attachment_ids = []
        pdf_names = []
        pdf_attachments = []
        new_attachments = []
        attachments = self.env['ir.attachment'].browse(attachment_ids)
        if not attachments:
            raise UserError(_("No attachment was provided"))
        for attachment in attachments:
            if attachment.mimetype == 'text/xml':
                pdf_names.append(attachment.name.replace('.xml','.pdf'))
        for attachment in attachments:
            if attachment.name in pdf_names and attachment.mimetype == 'application/pdf':
                pdf_attachments.append(attachment)
            else:
                new_attachments.append(attachment)
                new_attachment_ids.append(attachment.id)
        ###
        invoices = super(AccountJournal, self)._create_document_from_attachment(new_attachment_ids)
        ###
        for attachment_pdf in pdf_attachments:
            xml_name = attachment_pdf.name.replace('.pdf','.xml')
            for attachment in new_attachments:
                if attachment.name == xml_name and attachment.res_model == 'account.move' and attachment.res_id != False:
                    invoice = self.env['account.move'].browse(int(attachment.res_id))
                    invoice.with_context(no_new_invoice=True).message_post(attachment_ids=[attachment_pdf.id])
                    attachment_pdf.write({'res_model': 'account.move', 'res_id': invoice.id})
        ##
        return invoices