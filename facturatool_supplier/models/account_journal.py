# -*- coding: utf-8 -*-
from odoo import api, Command, fields, models, _
from odoo.exceptions import UserError, ValidationError
from odoo.addons.base.models.res_bank import sanitize_account_number
from odoo.tools import remove_accents
import logging
import re
import base64

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
        #Se adjuntan los documentos PDF a las facturas donde coincide con el adjunto XML
        for attachment_pdf in pdf_attachments:
            xml_name = attachment_pdf.name.replace('.pdf','.xml')
            for attachment in new_attachments:
                if attachment.name == xml_name and attachment.res_model == 'account.move' and attachment.res_id != False:
                    invoice = self.env['account.move'].browse(int(attachment.res_id))
                    invoice.with_context(no_new_invoice=True).message_post(attachment_ids=[attachment_pdf.id])
                    attachment_pdf.write({'res_model': 'account.move', 'res_id': invoice.id})
        ##
        #Se obtiene la informacion de adjuntos xml
        for attachment in new_attachments:
            if attachment.mimetype == 'text/xml' and attachment.res_model == 'account.move' and attachment.res_id != False:
                invoice = self.env['account.move'].browse(int(attachment.res_id))
                cfdi_data = invoice.get_cfdi_data( base64.b64decode(attachment.datas))
                _logger.debug('===== _create_document_from_attachment cfdi_data = %r',cfdi_data)
                if cfdi_data != False and cfdi_data['receptor']['id'] != False and cfdi_data['emisor']['id'] != False:
                    #Se valida si ya existe una factura con el mismo uuid
                    invoice_exist = self.env['account.move'].search([('cfdi_uuid','=',cfdi_data['uuid'])])
                    _logger.debug('===== _create_document_from_attachment invoice_exist = %r',invoice_exist)
                    if len(invoice_exist) > 0:
                        invoice.message_post(body="Error: Ya existe una factura con el UUID: "+cfdi_data['uuid'], message_type='comment')
                    else:
                        #Se crea la factura con la fecha, el proveedor, uuid y los conceptos
                        invoice_line_ids = []
                        for concepto in cfdi_data['conceptos']:
                            invoice_line_ids.append((0,0,concepto))
                        invoice.write({
                            'invoice_date':cfdi_data['fecha'],
                            'date':cfdi_data['fecha'],
                            'partner_id':cfdi_data['emisor']['id'],
                            'cfdi_uuid':cfdi_data['uuid'],
                            'cfdi_folio':cfdi_data['folio'],
                            'invoice_line_ids':invoice_line_ids
                        })
                        #Se Verifica el estado del cfdi
                        verificar_cfdi = invoice.verificar_cfdi(cfdi_data['emisor']['rfc'],cfdi_data['receptor']['rfc'],cfdi_data['total'],cfdi_data['uuid'])
                        if verificar_cfdi != False and verificar_cfdi['Estado'] == 'Vigente' and verificar_cfdi['EstatusCancelacion'] == None:
                            invoice.write({
                                'cfdi_state':'done'
                            })
        return invoices