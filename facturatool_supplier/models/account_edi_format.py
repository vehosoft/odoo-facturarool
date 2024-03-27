# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from odoo.exceptions import UserError
from odoo.tools.pdf import OdooPdfFileReader
from odoo.osv import expression
from odoo.tools import html_escape
from odoo.exceptions import RedirectWarning
try:
    import PyPDF2
    from PyPDF2.errors import PdfReadError
except ImportError:
    from PyPDF2.utils import PdfReadError

from lxml import etree
from struct import error as StructError
import base64
import io
import logging
import pathlib
import re


_logger = logging.getLogger(__name__)

class AccountEdiFormat(models.Model):
    _inherit = 'account.edi.format'

    def TEST_create_document_from_attachment(self, attachment):
        for file_data in self._decode_attachment(attachment):
            for edi_format in self:
                res = False
                try:
                    if file_data['type'] == 'xml':
                        res = edi_format.with_company(self.env.company)._create_invoice_from_xml_tree(file_data['filename'], file_data['xml_tree'])
                        
                except RedirectWarning as rw:
                    raise rw
                except Exception as e:
                    raise UserError(str(e))
                if res:
                    return res._link_invoice_origin_to_purchase_orders(timeout=4)
                else:
                    return super(AccountEdiFormat,self)._create_document_from_attachment(attachment)
        return self.env['account.move']
    
    def _create_invoice_from_xml_tree(self, filename, tree, journal=None):
        _logger.debug('===== _create_invoice_from_xml_tree on facturatool_supplier')
        _logger.debug('===== _create_invoice_from_xml_tree filename = %r',filename)
        cfdi_data = self.env['account.move'].get_cfdi_data(tree)
        _logger.debug('===== _create_invoice_from_xml_tree cfdi_data = %r',cfdi_data)
        if cfdi_data != False and cfdi_data['receptor']['id'] != False and cfdi_data['emisor']['id'] != False:
            #Se valida si ya existe una factura con el mismo uuid
            invoice_exist = self.env['account.move'].search([('cfdi_uuid','=',cfdi_data['uuid'])])
            _logger.debug('===== _create_invoice_from_xml_tree invoice_exist = %r',invoice_exist)
            if len(invoice_exist) > 0:
                invoice = self.env['account.move'].create({})
                invoice.message_post(body="Error: Ya existe una factura con el UUID: "+cfdi_data['uuid'], message_type='comment')
                #raise UserError("Ya existe una factura con el UUID: "+cfdi_data['uuid'])
                return invoice
            #Se crea la factura con la fecha, el proveedor, uuid y los conceptos
            invoice_line_ids = []
            for concepto in cfdi_data['conceptos']:
                invoice_line_ids.append((0,0,concepto))
            invoice = self.env['account.move'].create({
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
            return invoice
        else:
            res_xml_tree = super(AccountEdiFormat,self)._create_invoice_from_xml_tree(filename, tree, journal=journal)
            _logger.debug('===== _create_invoice_from_xml_tree res_xml_tree = %r',res_xml_tree)
            return res_xml_tree
    
    def _create_invoice_from_pdf_reader(self, filename, reader):
        _logger.debug('===== _create_invoice_from_pdf_reader on facturatool_supplier')
        _logger.debug('===== _create_invoice_from_pdf_reader filename = %r',filename)
        _logger.debug('===== _create_invoice_from_pdf_reader reader = %r',reader)
        _logger.debug('===== _create_invoice_from_pdf_reader reader.documentInfo = %r',reader.documentInfo)
        _logger.debug('===== _create_invoice_from_pdf_reader reader.numPages = %r',reader.numPages)
        for i in range(reader.numPages):
            _logger.debug('===== _create_invoice_from_pdf_reader page = %r',str(i+1))
            _logger.debug('===== _create_invoice_from_pdf_reader content = %r',reader.getPage(i).extract_text())

        #pdfdoc = PyPDF2.PdfFileReader(sample_pdf)
        return super()._create_invoice_from_pdf_reader(filename, reader)

    
