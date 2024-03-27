# Copyright VeHoSoft - Vertical & Horizontal Software (http://www.vehosoft.com)
# Code by: Francisco Rodriguez (frodriguez@vehosoft.com).

from odoo import api, fields, exceptions, models, _
from odoo.exceptions import AccessError, UserError, RedirectWarning, ValidationError
from lxml import etree
import json
import qrcode
import base64
import tempfile
import logging
_logger = logging.getLogger(__name__)

try:
    import zeep
except ImportError:  # pragma: no cover
    _logger.debug('Cannot import zeep')

class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    @api.depends('product_id')
    def _compute_name(self):
        for line in self:
            if line.move_id.move_type != 'in_invoice' or line.name == '' or line.name == False:
                super(AccountMoveLine,self)._compute_name()
    
    @api.depends('product_id', 'product_uom_id')
    def _compute_price_unit(self):
        for line in self:
            if line.move_id.move_type != 'in_invoice' or line.price_unit <= 0.00 or line.price_unit == False:
                super(AccountMoveLine,self)._compute_price_unit()


class AccountMove(models.Model):
    _inherit = 'account.move'

    def action_verificar_cfdi(self):
        for invoice in self:
            verificar_cfdi = self.verificar_cfdi(invoice.partner_id.vat, invoice.company_id.vat,invoice.amount_total, invoice.cfdi_uuid)
            _logger.debug('===== action_verificar_cfdi verificar_cfdi = %r',verificar_cfdi)
            if verificar_cfdi != False and verificar_cfdi['Estado'] == 'Vigente' and verificar_cfdi['EstatusCancelacion'] == None:
                invoice.write({
                    'cfdi_state':'done'
                })

    def verificar_cfdi(self, emisor, receptor,total, uuid):
        try:
            _logger.debug('===== verificar_cfdi emisor = %r',emisor)
            _logger.debug('===== verificar_cfdi receptor = %r',receptor)
            _logger.debug('===== verificar_cfdi total = %r',total)
            _logger.debug('===== verificar_cfdi uuid = %r',uuid)
            expresionImpresa = "?re="+str(emisor)+"&rr="+str(receptor)+"&tt="+str(total)+"&id="+str(uuid)
            _logger.debug('===== verificar_cfdi expresionImpresa = %r',expresionImpresa)
            client = zeep.Client('https://consultaqr.facturaelectronica.sat.gob.mx/ConsultaCFDIService.svc')
            result = client.service.Consulta(expresionImpresa=expresionImpresa)
            _logger.debug('===== verificar_cfdi result = %r',result)
            return result
        except:
            return False
    
    def is_utf8_code(self, texto):
        try:
            texto = texto.decode('utf-8')
            return True
        except:
            return False
    #Procesa el contenido de un xml y obtine los datos del CFDI
    def get_cfdi_data(self, cfdi):
        try:
            cfdi_data = {
                'emisor': {
                    'id': False,
                    'rfc': '',
                    'nombre': '',
                },
                'receptor': {
                    'id': False,
                    'rfc': '',
                },
                'uuid': False,
                'folio': '',
                'total': False,
                'fecha': False,
                'conceptos': []
            }
            _logger.debug('===== get_cfdi_data isinstance(cfdi, etree._Element) = %r',isinstance(cfdi, etree._Element) )
            if isinstance(cfdi, etree._Element) == False:
                parser = etree.XMLParser(ns_clean=True, recover=True)
                _logger.debug('===== get_cfdi_data self.is_utf8_code(cfdi) = %r',self.is_utf8_code(cfdi) )
                if self.is_utf8_code(cfdi) == False:
                    cfdi = cfdi.encode('utf-8')
                cfdi = etree.fromstring(cfdi, parser)
            _logger.debug('===== get_cfdi_data cfdi = %r',cfdi )
            ns = {'c':'http://www.sat.gob.mx/cfd/4','d':'http://www.sat.gob.mx/TimbreFiscalDigital'}
            nodoE=cfdi.xpath('c:Emisor ', namespaces=ns)
            nodoR=cfdi.xpath('c:Receptor ', namespaces=ns)
            nodoC=cfdi.xpath('c:Complemento ', namespaces=ns)
            total=cfdi.get('Total')
            fecha=cfdi.get('Fecha')
            serie=cfdi.get('Serie')
            folio=cfdi.get('Folio')
            for nodo in nodoE:
                emisor_rfc = nodo.get("Rfc")
                emisor_nombre = nodo.get("Nombre")
            for nodo in nodoR:
                receptor_rfc = nodo.get("Rfc")
            for nodo in nodoC:
                nodoAux=nodo.xpath('d:TimbreFiscalDigital', namespaces=ns)
                cfdi_uuid=nodoAux[0].get("UUID")
            
            if emisor_rfc != None and emisor_nombre != None and receptor_rfc != None and cfdi_uuid != None:
                #Se obtiene la compañia a la que pertenece la factura
                company_id = self.env['res.company'].search([('vat','=',receptor_rfc)])
                if len(company_id) > 0:
                    company_id = company_id[0].id
                else:
                    company_id = False
                #Se obtiene el id del proveedor, partner
                partner_id = self.env['res.partner'].search([('vat','=',emisor_rfc)])
                if len(partner_id) > 0:
                    partner_id = partner_id[0].id
                else:
                    partner_id = False
                
                cfdi_data['emisor'] = {
                    'id': partner_id,
                    'rfc': emisor_rfc,
                    'nombre': emisor_nombre,
                }
                cfdi_data['receptor'] = {
                    'id': company_id,
                    'rfc': receptor_rfc
                }
                cfdi_data['uuid'] = cfdi_uuid
                cfdi_data['total'] = total
                if fecha != None:
                    cfdi_data['fecha'] = fecha.split("T")[0]
                if serie != None:
                    cfdi_data['folio'] += serie
                if folio != None:
                    cfdi_data['folio'] += folio
                #Se obtienen los conceptos del xml cfdi
                nodoC=cfdi.xpath('c:Conceptos ', namespaces=ns)
                for nodo in nodoC:
                    conceptos=nodo.xpath('c:Concepto', namespaces=ns)
                    for concepto in conceptos:
                        conceptoData = {
                            'quantity': float(concepto.get("Cantidad")),
                            'price_unit': float(concepto.get("ValorUnitario")),
                            'name': concepto.get("Descripcion")
                        }
                        nodoImps=concepto.xpath('c:Impuestos', namespaces=ns)
                        for nodoI in nodoImps:
                            impuestos=nodoI.xpath('c:Traslados', namespaces=ns)
                            for impuesto in impuestos:
                                impTras=impuesto.xpath('c:Traslado', namespaces=ns)
                                tax_ids = []
                                for impT in impTras:
                                    TipoFactor = impT.get("TipoFactor")
                                    TasaOCuota = float(impT.get("TasaOCuota"))
                                    if TipoFactor == 'Tasa':
                                        TasaOCuota = TasaOCuota*100.00
                                    tax_id = self.env['account.tax'].search([('type_tax_use','=','purchase'),('amount','=',TasaOCuota)])
                                    if len(tax_id) > 0:
                                        tax_ids.append((4,tax_id[0].id))
                                if len(tax_ids) > 0:
                                    conceptoData['tax_ids']=tax_ids
                        cfdi_data['conceptos'].append(conceptoData)

            return cfdi_data
        except:
            return False
    
    def _get_create_document_from_attachment_decoders(self):
        res = super(AccountMove,self)._get_create_document_from_attachment_decoders()
        _logger.debug('===== _get_create_document_from_attachment_decoders res = %r',res)
        return res