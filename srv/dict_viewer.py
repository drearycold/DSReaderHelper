import os

from calibre.srv.routes import endpoint, json

from calibre.customize.ui import find_plugin

import bs4
from urllib.parse import (quote, unquote)
import html

import calibre_plugins.dsreader_helper.config as cfg
from polyglot.urllib import unquote

import traceback

@endpoint('/dshelper/dict_viewer/{req_type}', types={'req_type': str}, auth_required=False)
def dshelper_dict_viewer(ctx, rd, req_type):
    #traceback.print_stack()

    print('dshelper_dict_viewer ctx=%s rd=%s cookies=%s req_type=%s ' % (str(ctx), str(rd), str(rd.cookies), str(req_type)))

    if req_type == 'lookup':
        word = rd.query.get('word', None)
        if word is None:
            return b'missing word='

        dictresult = []
        result = ''
        print('dshelper_dict_viewer word %s' % word)
        print('dshelper_dict_viewer builders %s' % str(cfg.dict_builders))

        c = cfg.plugin_prefs[cfg.STORE_NAME]
        library_dict_ordered_list = c.get(cfg.KEY_DICT_VIEWER_ORDERED_LIST, {})
        dict_library_name = c.get(cfg.KEY_DICT_VIEWER_LIBRARY_NAME, '')
        dict_ordered_list = library_dict_ordered_list.get(dict_library_name, [])
        for dict_entry in dict_ordered_list:
            dicname = '%d#%s' % (dict_entry['id'], dict_entry['mdx'])
            if dicname not in cfg.dict_builders:
                continue
            dicname_quote = quote(dicname)
            builder = cfg.dict_builders[dicname].get('builder', None)
            if not builder:
                continue
            print('dshelper_dict_viewer builder %s' % str(builder))
            contents = builder.mdx_lookup(word, ignorecase=True)
            for content in contents:
                dict_soup = bs4.BeautifulSoup(content, 'html.parser')
                for link in dict_soup.find_all('link'):
                    if link.has_attr('href'):
                        link_href = link['href']
                        link_href_quote = quote(link_href)
                        link['href'] = 'resources?dic=%s&id=%s' % (dicname_quote, link_href_quote)
                for script in dict_soup.find_all('script'):
                    if script.has_attr('src'):
                        script_src = script['src']
                        script_src_quote = quote(script_src)
                        script['src'] = 'resources?dic=%s&id=%s' % (dicname_quote, script_src_quote)
                for img in dict_soup.find_all('img'):
                    if img.has_attr('src'):
                        img_src = img['src']
                        img_src_quote = quote(img_src)
                        img['src'] = 'resources?dic=%s&id=%s' % (dicname_quote, img_src_quote)
                for a in dict_soup.find_all('a'):
                    if a.has_attr('href'):
                        a_href = a['href']
                        a_href = a_href.replace('entry://#', '#')
                        a_href = a_href.replace('entry://', 'lookup?word=')
                        a['href'] = a_href
                if rd.cookies.get('textColor', '#') != '#':
                    textColor = rd.cookies["textColor"]
                    for f in dict_soup.find_all('font'):
                        if f.has_attr('color'):
                            f['color'] = textColor

                # print(dict_soup.prettify())

                segment = dict_soup.prettify()
                dictresult.append(
                    '<div class="mdictDefinition" id="mdictDefinition' + str(len(dictresult)) + '">' + 
                    '<h5>' + cfg.dict_builders[dicname]['title'] + "</h5>" +
                    segment +
                    '</div>'
                )

            words = list(filter(lambda w: w.lower() != word, builder.get_mdx_keys(word)))
            if words:
                if len(words) > 10:
                    words = words[0:10]
                links=list(map(lambda w: '<p><a href="lookup?word=%s">%s</a></p>' % (quote(w),html.escape(w)), words))
                dictresult.append(
                    '<div class="mdictSimilar" id="mdictSimilar' + str(len(dictresult)) + '">' + 
                    '<h6>Similar Words</h6>' +
                    '\n'.join(links) +
                    '</div>'
                )
        
        if not dictresult:
            dictresult.append('<p>Found no result</p>')

        try:
            header = '<html><head>\
                <meta name="viewport" content="width=device-width, initial-scale=1, shrink-to-fit=no">\
                <style>h5 { text-align: center; }</style>'
            if 'backgroundColor' in rd.cookies:
                header += '<style id="style_folio_background">html body { background-color: %s !important; }</style>' % rd.cookies['backgroundColor']
                header += '<style id="style_folio_fontsize">.mdictDefinition { font-size: 120%; line-height: 150%; }</style>'
            if rd.cookies.get('textColor', '#') != '#':
                header += '<style id="style_folio_text">html body { color: %s !important; }</style>' % rd.cookies['textColor']
            header += '</head><body>'
            dictresult.insert(0, header)
            # dictresult.insert(1, '<script src="resources?dic=static&id=mdict.js"></script>')

            dictresult.append('</body></html>')
            result = '<hr />\n'.join(dictresult)
            # print('dshelper_dict_viewer result %s' % str(result))
        except BaseException as e:
            print('dshelper_dict_viewer except %s' % str(e))

        rd.outheaders.set('Content-Type', 'text/html; charset=UTF-8', replace_all=True)

        return result

    if req_type == 'resources':
        req_dic = rd.query.get('dic', None)
        req_id = rd.query.get('id', None)
        if req_dic is None or req_id is None:   # illegal
            return 'nil'

        req_dic_unquote = unquote(req_dic)
        req_id_unquote = unquote(req_id)

        if req_dic_unquote == 'static':
            zip_path = os.path.dirname(cfg.__file__)
            res_path = 'static/' + req_id_unquote
            from zipfile import ZipFile
            print('dshelper_dict_viewer resources static %s' % res_path)
            with ZipFile(zip_path, 'r') as myzip:
                with myzip.open(res_path, 'r') as file:
                    data = file.read()
                    return dshelper_dict_resource_process(rd, data, res_path)

        print('dshelper_dict_viewer resources mdd dic=%s id=%s' % (req_dic_unquote, req_id_unquote))
    
        if req_dic_unquote in cfg.dict_builders:
            res_path = os.path.join(cfg.dict_builders[req_dic_unquote]['basepath'], req_id_unquote)
            print('dshelper_dict_viewer resources res_path=%s' % res_path)
        
            try:
                if os.path.exists(res_path):
                    with open(res_path, 'rb') as file:  #read data as bytes
                        data = file.read()
                        return dshelper_dict_resource_process(rd, data, res_path)
            except:
                pass

            print('dshelper_dict_viewer resources notexist res_path=%s' % res_path)
        
            builder = cfg.dict_builders[req_dic_unquote]['builder']
            print('dshelper_dict_viewer resources notexist builder=%s' % str(builder))

            try:
                if req_id_unquote.startswith("file://"):
                    req_id_unquote = req_id_unquote[7:]
                    print('dshelper_dict_viewer resources mdd req_id_unquote=%s' % (req_id_unquote))

                res_path = '\\%s' % '\\'.join(req_id_unquote.strip('/').split('/'))   # according to flask-mdict
                print('dshelper_dict_viewer resources mdd res_path=%s' % (res_path))
                datum = builder.mdd_lookup(res_path, ignorecase=True)
                for data in datum:      #data is bytes
                    return dshelper_dict_resource_process(rd, data, res_path)
            except Exception as e:
                print("dshelper_dict_viewer exception %s" % str(e))
                traceback.print_exc()

    if req_type == 'hint':
        rd.outheaders.set('Content-Type', 'application/json; charset=UTF-8', replace_all=True)
        word = rd.query.get('word', None)
        if word is None:
            return b'missing word='
        
        result = []
        print('dshelper_dict_viewer word %s' % word)
        print('dshelper_dict_viewer builders %s' % str(cfg.dict_builders))

        c = cfg.plugin_prefs[cfg.STORE_NAME]
        library_dict_ordered_list = c.get(cfg.KEY_DICT_VIEWER_ORDERED_LIST, {})
        dict_library_name = c.get(cfg.KEY_DICT_VIEWER_LIBRARY_NAME, '')
        dict_ordered_list = library_dict_ordered_list.get(dict_library_name, [])
        for dict_entry in dict_ordered_list:
            dicname = '%d#%s' % (dict_entry['id'], dict_entry['mdx'])
            if dicname not in cfg.dict_builders:
                continue
            dicname_quote = quote(dicname)
            builder = cfg.dict_builders[dicname].get('builder', None)
            if not builder:
                continue
            print('dshelper_dict_viewer builder %s' % str(builder))

            words = list(filter(lambda w: w.lower() != word, builder.get_mdx_keys(word)))
            result += list(map(lambda w: w.lower(), words))
        from calibre.utils.serialize import json_dumps
        return json_dumps({"prefixed": sorted(set(result))})

#data in bytes
def dshelper_dict_resource_process(rd, data, res_path):
    print("dshelper_dict_resource_process %s %s %s" % (res_path, type(data), len(data)))
    if res_path.endswith('.js'):
        rd.outheaders.set('Content-Type', 'text/javascript; charset=UTF-8', replace_all=True)
        return data
    elif res_path.endswith('.css'):
        rd.outheaders.set('Content-Type', 'text/css; charset=UTF-8', replace_all=True)
        if rd.cookies.get('textColor', '#') != '#':     #indicating dark theme
            import re
            textColor = rd.cookies["textColor"]
            css_str = data.decode("UTF-8")
            css_str = re.sub(r'(?!-)color\s*:[^;}]+', r'color:%s' % textColor, css_str)
            css_str = re.sub(r'(?!-)background\s*:[^;}]+', r'background:#2F2F2F', css_str)
            css_str = re.sub(r'(?!-)background-color\s*:[^;}]+', r'background-color:#2F2F2F', css_str)
            
            print("textColor css %s %s %s" % (res_path, type(data), css_str))
            return css_str.encode('utf-8')
        else:
            return data
    else:
        if res_path.endswith('.jpg') or res_path.endswith('.jpeg'):
            rd.outheaders.set('Content-Type', 'image/jpeg', replace_all=True)
        else:
            rd.outheaders.set('Content-Type', 'image/png', replace_all=True)
        print('dshelper_dict_viewer resources data from mdd %s %d' % (res_path, len(str(data))))
        #print('dshelper_dict_viewer resources data from mdd %s %s' % (res_path, str(data)))
        return data

# @endpoint('/dshelper/dict_viewer/{req_type1}/{req_type2}/{req_type3}',
#     types={'req_type1': str, 'req_type2': str, 'req_type3': str},
#     auth_required=True)
# def dshelper_dict_viewer_level3(ctx, rd, req_type1, req_type2, req_type3):
#     return ''
    