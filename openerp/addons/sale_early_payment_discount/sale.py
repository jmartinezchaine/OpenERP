# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011 Pexego Sistemas Informáticos (<http://www.pexego.es>). All Rights Reserved
#    Copyright (c) 2012 Zikzakmedia S.L. (http://zikzakmedia.com) All Rights Reserved.
#    $Id$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

"""Inherit sale_order to add early payment discount"""
import time
from datetime import datetime
from dateutil.relativedelta import relativedelta
from osv import fields, osv
import decimal_precision as dp

class sale_order(osv.osv):
    """Inherit sale_order to add early payment discount"""

    _inherit = "sale.order"

    def _amount_all2(self, cr, uid, ids, field_name, arg, context):
        """calculates functions amount fields"""
        res = {}

        for order in self.browse(cr, uid, ids):
            res[order.id] = {
                'early_payment_disc_untaxed': 0.0,
                'early_payment_disc_tax': 0.0,
                'early_payment_disc_total': 0.0,
                'total_early_discount': 0.0
            }

            if not order.early_payment_discount:
                res[order.id]['early_payment_disc_total'] = order.amount_total
                res[order.id]['early_payment_disc_tax'] = order.amount_tax
                res[order.id]['early_payment_disc_untaxed'] = order.amount_untaxed
            else:
                res[order.id]['early_payment_disc_tax'] = order.amount_tax * (1.0 - (float(order.early_payment_discount or 0.0)) / 100.0)
                res[order.id]['early_payment_disc_untaxed'] = order.amount_untaxed * (1.0 - (float(order.early_payment_discount or 0.0)) / 100.0)
                res[order.id]['early_payment_disc_total'] = res[order.id]['early_payment_disc_untaxed'] + res[order.id]['early_payment_disc_tax']
                res[order.id]['total_early_discount'] = res[order.id]['early_payment_disc_untaxed'] - order.amount_untaxed

        return res
    
    def _pp_refresh(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for order in self.browse(cr, uid, ids, context=context):
            res[order.id] = {
                'leyenda_pp': '',
            }
            res[order.id]['leyenda_pp'] = str(self.calcular_pronto_pagos(cr, uid, ids, arg, context)['leyenda_pp'])
            
        return res

    def _get_order(self, cr, uid, ids, context={}):
        result = {}
        for line in self.pool.get('sale.order.line').browse(cr, uid, ids, context=context):
            result[line.order_id.id] = True
        return result.keys()

    _columns = {
        'early_payment_discount': fields.float('E.P. disc.(%)', digits=(16, 2), help="Early payment discount"),
        'early_payment_disc_total': fields.function(_amount_all2, method=True, digits_compute=dp.get_precision('Account'), string='With E.P.',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'early_payment_discount'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='epd'),
        'early_payment_disc_untaxed': fields.function(_amount_all2, method=True, digits_compute=dp.get_precision('Account'), string='Untaxed Amount E.P.',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'early_payment_discount'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='epd'),
        'early_payment_disc_tax': fields.function(_amount_all2, method=True, digits_compute=dp.get_precision('Account'), string='Taxes E.P.',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'early_payment_discount'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='epd'),
        'total_early_discount': fields.function(_amount_all2, method=True, digits_compute=dp.get_precision('Account'), string='E.P. amount',
            store={
                'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['order_line', 'early_payment_discount'], 10),
                'sale.order.line': (_get_order, ['price_unit', 'tax_id', 'discount', 'product_uom_qty'], 10),
            },
            multi='epd'),
        #'leyenda_pp': fields.function(_pp_refresh, method=True, type = 'char', string='Leyenda pagos', help="Leyenda para pronto pagos.", 
        #      store={
        #        'sale.order': (lambda self, cr, uid, ids, c={}: ids, ['leyenda_pp'], 10),
        #    },
        #    multi='epd'),
        'leyenda_pp': fields.text('Leyenda pagos'),
        #'miembros_list': fields.function(_get_miembros_del_proyecto, method=True, type='char', string='Miembros del Equipo', store=False),
        'journal_id': fields.many2one('account.journal', 'Journal', required=True, readonly=True, states={'draft':[('readonly', False)]}),
    }
    
    #def onchange_payment_term(self, cr, uid, ids, payment_term=False, context=None):
    #    result = {}
    #    if payment_term:
    #        # Preguntar si es contado y asignar el Diario Contado.
    #        diarios = self.pool.get('account.journal').search(cr, uid, [
    #                                ('code', '=', 'VCONTADO')])
    #        if diarios:
    #            journal_id = diarios[0]
    #            #journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
    #            result = {'value': {'journal_id': journal_id,}}
    #    return result

    def onchange_partner_id2(self, cr, uid, ids, part,
                             early_payment_discount=False, payment_term=False):
        """ Extend this event for delete early payment discount if it isn't
            valid to new partner or add new early payment discount
        """
        res = self.onchange_partner_id(cr, uid, ids, part)
        if not part:
            res['value']['payment_term'] = False
            res['value']['early_payment_discount'] = False
            return res

        if payment_term != res['value'].get('payment_term', False):
            payment_term = res['value']['payment_term']

        discount = self.onchange_payment_term(cr, uid, ids, payment_term, part)
        res['value']['early_payment_discount'] = discount['value']\
                                                    ['early_payment_discount']
        return res

    def onchange_payment_term(self, cr, uid, ids, payment_term, part=False):
        """ On change event to update early payment dicount when the payment 
            term changes
        """

        early_discount_obj = self.pool.get('account.partner.payment.term.'\
                                           'early.discount')
        early_discs = []
        res = {}
        if payment_term:
            
            
            # Preguntar si es contado y asignar el Diario Contado.
            if payment_term == 1:
                # es contado
                diarios = self.pool.get('account.journal').search(cr, uid, [
                                    ('code', '=', 'VCONT')])
                if diarios:
                    journal_id = diarios[0]
                    #journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
                    res['journal_id'] = journal_id
            if payment_term != 1:
                # NO es contado
                    res['journal_id'] = 0
            
            early_discs = early_discount_obj.search(cr, uid, [
                                    ('partner_id', '=', part),
                                    ('payment_term_id', '=', payment_term)])
            if early_discs:
                res['early_payment_discount'] = early_discount_obj.browse(cr,
                                  uid, early_discs[0]).early_payment_discount
            else:
                early_discs = early_discount_obj.search(cr, uid, [
                                      ('partner_id', '=', False),
                                      ('payment_term_id', '=', payment_term)])
                if early_discs:
                    res['early_payment_discount'] = early_discount_obj.browse(
                              cr, uid, early_discs[0]).early_payment_discount
        if not early_discs:
            early_discs = early_discount_obj.search(cr, uid, [
                                              ('partner_id', '=', part),
                                              ('payment_term_id', '=', False)])
            if early_discs:
                res['early_payment_discount'] = early_discount_obj.browse(cr,
                                  uid, early_discs[0]).early_payment_discount
            else: # Search default discount for everbody
                early_discs = early_discount_obj.search(cr, uid, [
                                              ('partner_id', '=', False),
                                              ('payment_term_id', '=', False)])
                if early_discs:
                    res['early_payment_discount'] = early_discount_obj.browse(
                              cr, uid, early_discs[0]).early_payment_discount
                else: # Delete early payment discount if there isn't early discount
                    res['early_payment_discount'] = False
        return {'value': res}

    def action_invoice_create(self, cr, uid, ids, grouped=False, states=['confirmed', 'done', 'exception'], date_inv=False, context=None):
        """
        Inherited method for writing early_payment_discount value in created invoice
        """
        invoice_id = super(sale_order, self).action_invoice_create(cr, uid, ids, grouped=grouped, states=states, date_inv=date_inv, context=context)
        invoice_facade = self.pool.get('account.invoice')
        current_sale = self.browse(cr, uid, ids, context=context)[0]
        if current_sale.early_payment_discount:
            invoice_facade.write(cr, uid, invoice_id, {'early_payment_discount': current_sale.early_payment_discount})
        return invoice_id
    
    def button_dummy(self, cr, uid, ids, context=None):
        super(sale_order, self).button_dummy(cr, uid, ids, context)
        #vals = {}
        #res = {}
        #up_leyenda = self.calcular_pronto_pagos(cr, uid, ids, vals, context)['leyenda_pp']
        #self.leyenda_pp = up_leyenda
        #cod = ids[0] 
        #res[cod]['leyenda_pp'] = up_leyenda
        return True
    
    def write(self, cr, uid, ids, vals, context=None):
        current_sale = self.browse(cr, uid, ids, context=context)[0]
        journal_id = current_sale.journal_id.id
        journal = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context)
        # Si eldiario es contado entonces no lleva la leyenda.
        if journal.code != 'VCONT':
            up_leyenda = self.calcular_pronto_pagos(cr, uid, ids, vals, context)
            vals.update(up_leyenda)
            prop_id = self.pool.get('ir.property').search(cr, uid, [('name', '=', 'property_leyenda_ventas')], context=context)
            prop_nota_venta = self.pool.get('ir.property').browse(cr, uid, prop_id, context=context)[0]
            if prop_nota_venta:
                vals.update({'note':prop_nota_venta.value_text})
        return super(sale_order, self).write(cr, uid, ids, vals, context)
    
    def calcular_pronto_pagos(self, cr, uid, ids, vals, context=None):
        # Buscar el los PP asociados al cliente o los generales
        early_discount_obj = self.pool.get('account.partner.payment.term.early.discount')
        apt_obj = self.pool.get('account.payment.term')
        
        leyendas = []
        texto = ''
        up_leyenda = ''
        
        cliente_id = False
        for order in self.browse(cr, uid, ids):
            cliente_id = order.partner_id.id
            
        early_discs = early_discount_obj.search(cr, uid, [('partner_id', '=', cliente_id)])
        if not early_discs:
            early_discs = early_discount_obj.search(cr, uid, [('partner_id', '=', False)])
            
        moneda = '$'
        for order in self.browse(cr, uid, ids):
            moneda = order.pricelist_id.currency_id.symbol
            if order.date_order:
                date_ref = order.date_order
            else:
                date_ref = datetime.now().strftime('%Y-%m-%d')
        
        if early_discs:            
            for descuento in early_discs:
                pp = early_discount_obj.browse(cr, uid, descuento, context=context)
                pt = apt_obj.browse(cr, uid, pp.payment_term_id.id, context=context)
                # @todo: Ver que si tiene mas de una linea en los terminos estos cambian las fechas.
                # recorre las lineas del termino de pago, si tiene mas de una no se inlcuye porahora 
                
                # Calcular las fechas para los pagos
                
                for linea_t in pt.line_ids:
                    dias = linea_t.days
                    fecha1 = datetime.strptime(date_ref, '%Y-%m-%d')
                    dias_sumar = relativedelta(days=dias)
                    next_date = fecha1 + dias_sumar
                    if linea_t.days2 < 0:
                        next_first_date = next_date + relativedelta(day=1, months=1) #Getting 1st of next month
                        next_date = next_first_date + relativedelta(days=linea_t.days2)
                    if linea_t.days2 > 0:
                        next_date += relativedelta(day=linea_t.days2, months=1)
                        
                porc_desc = pp.early_payment_discount
                # Calcular los montos ponumber)resr PP
                monto_descuento = self._get_monto_descuento(cr, uid, ids, pp, context)        
        
                # actualizar leyenda
                
                leyendas.append(['fecha', next_date.strftime("%d/%m/%Y"), 'monto', moneda + ' ' + str(monto_descuento)]) 
                
            cont = 0     
            for ly in leyendas: 
                cont = cont + 1
                if cont > 1:
                    texto += '\t \t \t \t \t %s %s' % (ly[1], ly[3])
                else:
                    texto += '  %s %s \n' % (ly[1], ly[3])    
            up_leyenda = {'leyenda_pp': 'Abonando antes de: ' + texto}
        return up_leyenda
    
    def _get_monto_descuento(self, cr, uid, ids, descuento, context):
        """Obtiene el monto con el descuento para la factura"""
        res = 0

        prod_early_payment_id = self.pool.get('product.product').search(cr, uid, [('default_code', '=', 'DPP')])
        prod_early_payment_id = prod_early_payment_id and prod_early_payment_id[0] or False
        
        for order in self.browse(cr, uid, ids):
            if not descuento:
                res[order.id] = 0.0
                continue
            #searches if DPP is applied
            found = False
            for line in order.order_line:
                if line.product_id and line.product_id.id == prod_early_payment_id:
                    found = True
                    break;

            if found:
                res[order.id] = 0.0
            else:
                total_net_price = 0.0
                for order_line in order.order_line:
                    total_net_price += order_line.price_subtotal

                #res[invoice.id] = float(total_net_price) - (float(total_net_price) * (1 - (descuento.early_payment_discount or 0.0) / 100.0))
                #res = float(total_net_price) * (1 - (descuento.early_payment_discount or 0.0) / 100.0)
                res = float(order.amount_total) * (1 - (descuento.early_payment_discount or 0.0) / 100.0)

        return round(res, 0)


sale_order()
