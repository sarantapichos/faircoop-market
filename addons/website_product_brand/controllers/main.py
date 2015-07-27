import werkzeug
from openerp import http
from openerp.http import request
import openerp.addons.website_sale.controllers.main
from openerp import http, SUPERUSER_ID
import werkzeug
from openerp.tools.translate import _
from openerp.addons.website.models.website import slug
PPG = 20
PPR = 4

class table_compute(object):

    def __init__(self):
        self.table = {}

    def _check_place(self, posx, posy, sizex, sizey):
        res = True
        for y in range(sizey):
            for x in range(sizex):
                if posx + x >= PPR:
                    res = False
                    break
                row = self.table.setdefault(posy + y, {})
                if row.setdefault(posx + x) is not None:
                    res = False
                    break

            for x in range(PPR):
                self.table[posy + y].setdefault(x, None)

        return res

    def process(self, products):
        minpos = 0
        index = 0
        maxy = 0
        for p in products:
            x = min(max(p.website_size_x, 1), PPR)
            y = min(max(p.website_size_y, 1), PPR)
            if index > PPG:
                x = y = 1
            pos = minpos
            while not self._check_place(pos % PPR, pos / PPR, x, y):
                pos += 1

            if index > PPG and pos / PPR > maxy:
                break
            if x == 1 and y == 1:
                minpos = pos / PPR
            for y2 in range(y):
                for x2 in range(x):
                    self.table[pos / PPR + y2][pos % PPR + x2] = False

            self.table[pos / PPR][pos % PPR] = {'product': p,
             'x': x,
             'y': y,
             'class': ' '.join(map(lambda x: x.html_class or '', p.website_style_ids))}
            if index <= PPG:
                maxy = max(maxy, y + pos / PPR)
            index += 1

        rows = self.table.items()
        rows.sort()
        rows = map(lambda x: x[1], rows)
        for col in range(len(rows)):
            cols = rows[col].items()
            cols.sort()
            x += len(cols)
            rows[col] = [ c for c in map(lambda x: x[1], cols) if c != False ]

        return rows


class QueryURL(object):

    def __init__(self, path = '', **args):
        self.path = path
        self.args = args

    def __call__(self, path = None, **kw):
        if not path:
            path = self.path
        for k, v in self.args.items():
            kw.setdefault(k, v)

        l = []
        for k, v in kw.items():
            if v:
                if isinstance(v, list) or isinstance(v, set):
                    l.append(werkzeug.url_encode([ (k, i) for i in v ]))
                else:
                    l.append(werkzeug.url_encode([(k, v)]))

        if l:
            path += '?' + '&'.join(l)
        return path


class website_sale(openerp.addons.website_sale.controllers.main.website_sale):
    _references_per_page = 20

    @http.route(['/shop',
                 '/shop/page/<int:page>',
                 '/shop/category/<model("product.public.category"):category>',
                 '/shop/category/<model("product.public.category"):category>/page/<int:page>',
                 '/shop/brands',
                 '/shop/<country_defined>/country/<model("res.country"):country>/brands',
                 '/shop/country/<model("res.country"):country>',
                 '/shop/country/<model("res.country"):country>/<country_defined>',
                 '/shop/country/<model("res.country"):country>/page/<int:page>',
                 '/shop/country/<model("res.country"):country>/page/<int:page>/<country_defined>',
                 '/shop/country/<model("res.country"):country>/category/<model("product.public.category"):category>',
                 '/shop/country/<model("res.country"):country>/category/<model("product.public.category"):category>/<country_defined>',
                 '/shop/country/<model("res.country"):country>/category/<model("product.public.category"):category>/page/<int:page>',
                 '/shop/country/<model("res.country"):country>/category/<model("product.public.category"):category>/page/<int:page>/<country_defined>',
                 ], type='http', auth='public', website=True)

    def shop(self, page=0, category=None, country=None, search='', brand=None, country_defined='', **post):
        cr, uid, context, pool = request.cr, request.uid, request.context, request.registry

        #utilities
        values = {}
        domain = request.website.sale_product_domain()
        country_obj = pool['res.country']
        partner_obj = pool['res.partner']
        product_obj = pool.get('product.template')
        domain_list=[]
        empty_domain=[]
        check=""
        country_group_domain = [('is_company', '=', True), ('grade_id.website_published', '=', True), ('website_published', '=', True)]
        country_all = post.pop('country_all', False)
        total_products = 0
        if country_defined:
            check="/country_defined"
            domain += [('product_brand_id.company_id.partner_id.country_id', '=', country.id )]
        if search:
            domain += ['|', '|', '|',
                       ('name', 'ilike', search),
                       ('description', 'ilike', search),
                       ('description_sale', 'ilike', search),
                       ('product_variant_ids.default_code', 'ilike', search)]
        if category:
            domain += [('public_categ_ids', 'child_of', int(category))]
        if country:
            domain += [('product_brand_id.company_id.partner_id.country_id', '=', country.id)]
        if not country:
                    country_code = request.session['geoip'].get('country_code')
                    if country_code:
                        country_ids = country_obj.search(request.cr, request.uid, [('code', '=', country_code)], context=request.context)
                        if country_ids:
                            country = country_obj.browse(request.cr, request.uid, country_ids[0], context=request.context)
        countries = partner_obj.read_group(
                    request.cr, SUPERUSER_ID, country_group_domain, ["country_id", "company_id", "id"],
                    groupby="country_id", orderby="country_id", context=request.context)
        countries2=[]


        product_ids2 = product_obj.search(request.cr, SUPERUSER_ID, empty_domain,context=request.context)

        # flag active country and select only countries with products
        for country_dict in countries:
            country_dict['active'] = country and country_dict['country_id'] and country_dict['country_id'][0] == country.id
            for b in product_obj.browse(cr, SUPERUSER_ID, product_ids2, context=context):
                if b.product_brand_id.company_id.country_id.id == country_dict['country_id'][0]:
                    total_products+=1
            if total_products!=0:
                countries2.append(country_dict)
            total_products = 0
        countries2.insert(0, {
            'country_id': (0, ("All Countries")),
            'active': bool(country is None),
        })

        # format pager
        url_args = {}
        if search:
            url_args['search'] = search
            post['search'] = search
        if category:
            category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
        if country_all:
            url_args['country_all'] = True
        if category and not country:
            url = '/shop/category/' + slug(category)
        elif country and not category:
            url = '/shop/country/' + slug(country)
        elif country and category:
            url = '/shop/category/' + slug(category) + '/country/' + slug(country)
        else:
            url = '/shop'

        domain2 = list(domain_list)
        attrib_list = request.httprequest.args.getlist('attrib')
        attrib_values = [ map(int, v.split('-')) for v in attrib_list if v ]
        attrib_set = set([ v[1] for v in attrib_values ])
        if attrib_values:
            attrib = None
            ids = []
            for value in attrib_values:
                if not attrib:
                    attrib = value[0]
                    ids.append(value[1])
                elif value[0] == attrib:
                    ids.append(value[1])
                else:
                    domain += [('attribute_line_ids.value_ids', 'in', ids)]
                    attrib = value[0]
                    ids = [value[1]]
            if attrib:
                domain += [('attribute_line_ids.value_ids', 'in', ids)]
        keep = QueryURL('/shop', category=category and int(category),  country=country and int(country), search=search, attrib=attrib_list)
        if not context.get('pricelist'):
            pricelist = self.get_pricelist()
            context['pricelist'] = int(pricelist)
        else:
            pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)

        # Brand's product search
        if brand:
          values.update({'brand': brand})
          product_designer_obj = pool.get('product.brand')
          brand_ids = product_designer_obj.search(cr, SUPERUSER_ID, [('id', '=', int(brand))])
          domain += [('product_brand_id', 'in', brand_ids)]

        product_count = product_obj.search_count(cr, uid, domain, context=context)

        pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)

        product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order='website_published desc, website_sequence desc', context=context)
        products = product_obj.browse(cr, uid, product_ids, context=context)

        style_obj = pool['product.style']
        style_ids = style_obj.search(cr, uid, [], context=context)
        styles = style_obj.browse(cr, uid, style_ids, context=context)

        category_obj = pool['product.public.category']
        category_ids = category_obj.search(cr, uid, [], context=context)
        categories = category_obj.browse(cr, uid, category_ids, context=context)
        categs = filter(lambda x: not x.parent_id, categories)
        if category:
            selected_id = int(category)
            child_prod_ids = category_obj.search(cr, uid, [('parent_id', '=', selected_id)], context=context)
            children_ids = category_obj.browse(cr, uid, child_prod_ids)
            values.update({'child_list': children_ids})

        attributes_obj = request.registry['product.attribute']
        attributes_ids = attributes_obj.search(cr, uid, [], context=context)
        attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)

        from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
        to_currency = pricelist.currency_id
        compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

        values.update({'search': search,
         'category': category,
         'countries': countries2,
         'check' : check,
         'current_country': country,
         'attrib_values': attrib_values,
         'attrib_set': attrib_set,
         'pager': pager,
         'pricelist': pricelist,
         'products': products,
         'bins': table_compute().process(products),
         'rows': PPR,
         'styles': styles,
         'categories': categs,
         'attributes': attributes,
         'compute_currency': compute_currency,
         'keep': keep,
         'style_in_product': lambda style, product: style.id in [ s.id for s in product.website_style_ids ],
         'attrib_encode': lambda attribs: werkzeug.url_encode([ ('attrib', i) for i in attribs ])})
        return request.website.render('website_sale.products', values)

    #Method to get the brands.
    @http.route(['/shops',
				'/shops/country/<model("res.country"):country>',
				'/shops/country/<model("res.country"):country>/<country_defined>',
				'/shops/country/<model("res.country"):country>/page/<int:page>/<country_defined>',
				'/shops/country/<model("res.country"):country>/page/<int:page>',
				'/shops/page/<int:page>',
				], type='http', auth='public', website=True)
    def shops(self, country=None,country_defined='', page=0, **post):
          cr, context, pool = (request.cr, request.context, request.registry)
          country_all = post.pop('country_all', False)
          brand_obj = pool['product.brand']
          partner_obj = pool['res.partner']
          country_obj = request.registry['res.country']
          country_all = post.pop('country_all', False)
          company_obj = pool['res.company']
          domain1 = [('company_id.partner_id.is_company', '=', True), ('company_id.partner_id.grade_id.website_published', '=', True), ('company_id.partner_id.website_published', '=', True)]
          country_group_domain = [('is_company', '=', True), ('grade_id.website_published', '=', True), ('website_published', '=', True)]
          domain=[]
          domain_list=[]
          empty_domain=[]
          brand_values = []
          company_values = []
          total_brands_country=0
          check=""
          search = post.get('search', '')
          if country_defined:
               check="/country_defined"
          if search:
                       domain += ['|', ('name', 'ilike', search), ('website_description', 'ilike', search)]
          countries2=[]
          if not country:
            country_code = request.session['geoip'].get('country_code')
            if country_code:
                country_ids = country_obj.search(request.cr, request.uid, [('code', '=', country_code)], context=request.context)
                if country_ids:
                    country = country_obj.browse(request.cr, request.uid, country_ids[0], context=request.context)
          if country:
			  domain_list += [('company_id.partner_id.country_id', '=', country.id)]

          domain2 = list(domain_list)
          country_domain = list(domain1)

		  # group partners by country and search brands
          brand_ids = brand_obj.search(cr, SUPERUSER_ID, domain2)
          countries = partner_obj.read_group(
                               request.cr, SUPERUSER_ID, country_group_domain, ["country_id", "company_id","grade_id", "id"],
                               groupby="country_id", orderby="country_id", context=request.context)



          # format pager
          if country:
              url = '/shops/country/' + slug(country)
          else:
              url = '/shops'
          url_args = {}
          if search:
              url_args['search'] = search
          if country_all:
              url_args['country_all'] = True

          countries_partners = brand_obj.search(
              request.cr, SUPERUSER_ID, empty_domain,
              context=request.context, count=True)

          brand_count = brand_obj.search_count(
                      request.cr, SUPERUSER_ID, domain2,
                      context=request.context)

          pager = request.website.pager(
                      url=url, total=brand_count, page=page, step=self._references_per_page, scope=4,
                      url_args=url_args)

          # search partners matching current search parameters
          partner_ids = brand_obj.search(
              request.cr, SUPERUSER_ID, country_domain,
              context=request.context)
          brand_ids2 = brand_obj.search(cr, SUPERUSER_ID, empty_domain)
          partners = brand_obj.browse(request.cr, SUPERUSER_ID, brand_ids2, request.context)
          # remove me in trunk
          partners = sorted(partners, key=lambda x: (x.company_id.partner_id.grade_id.sequence if x.company_id.partner_id.grade_id else 0, len([i for i in x.company_id.partner_id.implemented_partner_ids if i.company_id.partner_id.website_published])), reverse=True)
          # partners = partners[pager['offset']:pager['offset'] + self._references_per_page]

          google_map_partner_ids = ','.join(map(str, [p.company_id.partner_id.id for p in partners]))

          # flag active country and update sum of brands in each country
          for country_dict in countries:
              country_dict['active'] = country and country_dict['country_id'] and country_dict['country_id'][0] == country.id
              for b in brand_obj.browse(cr, SUPERUSER_ID, brand_ids2, context=context):
                  if b.company_id.partner_id.country_id.id == country_dict['country_id'][0]:
                      total_brands_country+=1
                  country_dict['country_id_count']=(total_brands_country)
              if total_brands_country!=0:
                  countries2.append(country_dict)
              total_brands_country = 0
          countries2.insert(0, {
              'country_id_count': countries_partners,
              'country_id': (0, ("All Countries")),
              'active': bool(country is None),
          })

          #get brands and make pagination
          brands_by_page=brand_obj.browse(cr,SUPERUSER_ID, brand_ids, context=context)
          brands_by_page = brands_by_page[pager['offset']:pager['offset'] + self._references_per_page]
          for brand_rec in brands_by_page:
              brand_values.append(brand_rec)

          keep = QueryURL('/shops', brand_id=[])

          values = {'brand_rec': brand_values,
          'keep': keep,
          'countries': countries2,
          'check' : check,
          'current_country': country,
          'pager': pager,
          'google_map_shop_ids': google_map_partner_ids,
           }
          if post.get('search'):
              values.update({'search': post.get('search')})
          return request.website.render('website_product_brand.product_brands', values)

    # vim:expandtab:tabstop=4:softtabstop=4:shiftwidth=4:

    @http.route(['/<names>',
				], type='http', auth='public', website=True)
    def countries_link(self, names, page=0, **post):
		  cr, context, pool = (request.cr, request.context, request.registry)
		  country_obj=pool('res.country')
		  name2= names.title()
		  domain = [('name', '=', name2)]
		  country = country_obj.search(cr, SUPERUSER_ID, domain)
		  country2 = country_obj.browse(cr, SUPERUSER_ID, country, context=context)
          # format pager
		  values={ 'country' : country2,
		  }
		  return request.website.render('website_product_brand.countries_link', values)

    @http.route([   '/products/<names>',
                ], type='http', auth='public', website=True)
    def products_country(self, names, category=None, search='', brand=None, page=0, **post):
          cr, uid, context, pool = request.cr, request.uid, request.context, request.registry
          values = {}
          country_obj=pool('res.country')
          product_obj = pool.get('product.template')
          name2= names.title()
          domain = [('name', '=', name2)]
          country = country_obj.search(cr, SUPERUSER_ID, domain)
          country2 = country_obj.browse(cr, SUPERUSER_ID, country, context=context)
          product_domain = [('product_brand_id.company_id.partner_id.country_id', '=', country2.id)]
          if search:
              product_domain += ['|', '|', '|',
                         ('name', 'ilike', search),
                         ('description', 'ilike', search),
                         ('description_sale', 'ilike', search),
                         ('product_variant_ids.default_code', 'ilike', search)]
          if category:
              product_domain += [('public_categ_ids', 'child_of', int(category))]


          attrib_list = request.httprequest.args.getlist('attrib')
          attrib_values = [ map(int, v.split('-')) for v in attrib_list if v ]
          attrib_set = set([ v[1] for v in attrib_values ])
          if attrib_values:
              attrib = None
              ids = []
              for value in attrib_values:
                  if not attrib:
                      attrib = value[0]
                      ids.append(value[1])
                  elif value[0] == attrib:
                      ids.append(value[1])
                  else:
                      product_domain += [('attribute_line_ids.value_ids', 'in', ids)]
                      attrib = value[0]
                      ids = [value[1]]
              if attrib:
                  product_domain += [('attribute_line_ids.value_ids', 'in', ids)]
          keep = QueryURL('/products', category=category and int(category), search=search, names=country2.name, attrib=attrib_list)
          if not context.get('pricelist'):
              pricelist = self.get_pricelist()
              context['pricelist'] = int(pricelist)
          else:
              pricelist = pool.get('product.pricelist').browse(cr, uid, context['pricelist'], context)


          # Brand's product search
          if brand:
                values.update({'brand': brand})
                product_designer_obj = pool.get('product.brand')
                brand_ids = product_designer_obj.search(cr, SUPERUSER_ID, [('id', '=', int(brand))])
                product_domain += [('product_brand_id', 'in', brand_ids)]
          # format pager
          url_args = {}
          if search:
                url_args['search'] = search
                post['search'] = search
          if category:
                category = pool['product.public.category'].browse(cr, uid, int(category), context=context)
          else:
                url = '/shop'
          product_all = product_obj.search(request.cr, SUPERUSER_ID, product_domain,context=request.context)
          product_count = product_obj.search_count(cr, uid, domain, context=context)

          pager = request.website.pager(url=url, total=product_count, page=page, step=PPG, scope=7, url_args=post)

          product_ids = product_obj.search(cr, uid, domain, limit=PPG, offset=pager['offset'], order='website_published desc, website_sequence desc', context=context)
          products = product_obj.browse(cr, uid, product_ids, context=context)

          style_obj = pool['product.style']
          style_ids = style_obj.search(cr, uid, [], context=context)
          styles = style_obj.browse(cr, uid, style_ids, context=context)

          category_obj = pool['product.public.category']
          category_ids = category_obj.search(cr, uid, [], context=context)
          categories = category_obj.browse(cr, uid, category_ids, context=context)
          categs = filter(lambda x: not x.parent_id, categories)
          if category:
                selected_id = int(category)
                child_prod_ids = category_obj.search(cr, uid, [('parent_id', '=', selected_id)], context=context)
                children_ids = category_obj.browse(cr, uid, child_prod_ids)
                values.update({'child_list': children_ids})

          attributes_obj = request.registry['product.attribute']
          attributes_ids = attributes_obj.search(cr, uid, [], context=context)
          attributes = attributes_obj.browse(cr, uid, attributes_ids, context=context)

          from_currency = pool.get('product.price.type')._get_field_currency(cr, uid, 'list_price', context)
          to_currency = pricelist.currency_id
          compute_currency = lambda price: pool['res.currency']._compute(cr, uid, from_currency, to_currency, price, context=context)

          values.update({'search': search,
           'category': category,
           'country': country2,
           'current_country': country2,
           'attrib_values': attrib_values,
           'attrib_set': attrib_set,
           'pager': pager,
           'pricelist': pricelist,
           'products': product_all,
           'bins': table_compute().process(products),
           'rows': PPR,
           'styles': styles,
           'categories': categs,
           'attributes': attributes,
           'compute_currency': compute_currency,
           'keep': keep,
           'style_in_product': lambda style, product: style.id in [ s.id for s in product.website_style_ids ],
           'attrib_encode': lambda attribs: werkzeug.url_encode([ ('attrib', i) for i in attribs ])})
          return request.website.render('website_sale.products', values)



    @http.route([   '/companies/<names>',
                ], type='http', auth='public', website=True)
    def companies_country(self, names, page=0, **post):
          cr, context, pool = (request.cr, request.context, request.registry)
          country_obj=pool('res.country')
          name2= names.title()
          domain = [('name', '=', name2)]
          country = country_obj.search(cr, SUPERUSER_ID, domain)
          country2 = country_obj.browse(cr, SUPERUSER_ID, country, context=context)
          prova="adios"
          values={ 'country' : country2,
                   'prova' : prova
          }
          return request.website.render('website_product_brand.countries_link', values)
    @http.route(['/regionalsmarket',
    				], type='http', auth='public', website=True)
    def countriesmarket(self, country="", **post):
          cr, context, pool = (request.cr, request.context, request.registry)
          country_obj=pool['res.country']
          partner_obj = pool['res.partner']
          brand_obj = pool['product.brand']
          product_obj = pool.get('product.template')
          country_group_domain = [('is_company', '=', True), ('grade_id.website_published', '=', True), ('website_published', '=', True)]
          empty_domain=[]
          countries2=[]
          TotalCountries=[]
          total_brands_country = 0

          if not country:
              country_code = request.session['geoip'].get('country_code')
              if country_code:
                  country_ids = country_obj.search(request.cr, request.uid, [('code', '=', country_code)], context=request.context)
                  if country_ids:
                      country = country_obj.browse(request.cr, request.uid, country_ids[0], context=request.context)
          if country:
              domain += [('product_brand_id.company_id.partner_id.country_id', '=', country.id)]

          countries = partner_obj.read_group(
                               request.cr, SUPERUSER_ID, country_group_domain, ["country_id", "company_id","grade_id", "id"],
                               groupby="country_id", orderby="country_id", context=request.context)
          brand_ids2 = brand_obj.search(cr, SUPERUSER_ID, empty_domain)

          for country_dict in countries:
              country_dict['active'] = country and country_dict['country_id'] and country_dict['country_id'][0] == country.id
              for b in brand_obj.browse(cr, SUPERUSER_ID, brand_ids2, context=context):
                  if b.company_id.partner_id.country_id.id == country_dict['country_id'][0]:
                      total_brands_country+=1
                  country_dict['country_id_count']=(total_brands_country)
              if total_brands_country!=0:
                  countries2.append(country_dict)
              total_brands_country = 0
          # format pager
          values={ 'countries_total' : countries2,
          }
          return request.website.render('website_product_brand.countries_market', values)