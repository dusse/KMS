from markupsafe import Markup
from flask import url_for

def HeaderComponent(title, dropdowns):

    dropdown_html = ''
    for dropdown in dropdowns:
        items_html = ''.join(f'''
            <a class="dropdown-item" href="{item['href']}">{item['text']}</a>
        ''' for item in dropdown['items'])

        dropdown_html += f'''
            <div class="dropdown">
                <button class="btn btn-outline-light dropdown-toggle" type="button" id="{dropdown['id']}" style="border: none;">
                    {dropdown['button_text']}
                </button>
                <div class="dropdown-menu" aria-labelledby="{dropdown['id']}">
                    {items_html}
                </div>
            </div>
        '''

    header_html = f'''
        <div class="container-fluid bg-dark py-2" style="margin-top: 0; padding-top: 0; text-decoration: none;">
            <div class="d-flex justify-content-between align-items-center">
                <h4 class="text-light mb-0" style="width: 15rem;">{title}<br><div id="NameActiveTab"></div></h4>
                <div class="d-flex nav-link">
                    {dropdown_html}
                </div>
                <a class="btn btn-outline-light" href="{url_for('auth.logout')}" onclick="clearNavigationState()">logout</a>
            </div>
        </div>
    '''

    return Markup(header_html)



def AddButton(btn_class="btn btn-primary", data_target="#addSubscriptionModal", use_svg = True, text_content='добавить'):
    
    
    if use_svg:
            svg_content = '''<svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                    <path fill="currentColor" d="M19 13H13V19H11V13H5V11H11V5H13V11H19V13Z"/>
                </svg>'''
            button_html = f'''
                    <button type="button" class="btn {btn_class}" data-toggle="modal" data-target="{data_target}">
                        {svg_content}
                    </button>
                '''
    else:
        button_html = f'''
                <button type="button" class="btn {btn_class}" data-toggle="modal" data-target="{data_target}">
                    {text_content}
                </button>
            '''

    return Markup(button_html)



def TableActionButtons(download_class="btn btn-secondary", upload_class="btn btn-secondary", upload_text='загрузить из .xlsx'):
    button_html = f'''
        <div>
            <button class="{download_class}" onclick="downloadExcel()">скачать как .xlsx</button>
            <button class="{upload_class}" onclick="document.getElementById('uploadExcel').click()">{upload_text}</button>
            <input type="file" id="uploadExcel" style="display: none;" accept=".xlsx" onchange="uploadExcel(event)" />
        </div>
    '''
    return Markup(button_html)


def SearchForm(placeholder="search...", button_text="search"):
    searchForm_html = f'''
        <form id="searchForm">
            <div class="input-group">
                <input type="text" class="form-control" id="searchQuery" placeholder="{placeholder}">
                <div class="input-group-append">
                    <button class="btn btn-outline-secondary" type="submit">{button_text}</button>
                </div>
            </div>
        </form>
    '''
    return Markup(searchForm_html)


def SelectorModal(modal_id, modal_title, items, onclick_function_name, close_function_name):
    items_cards_html = ''.join(
        f'''
        <div class="col-md-4 mb-3">
            <div class="card h-100 d-flex flex-column">
                <div class="card-body d-flex flex-grow-1 flex-column">
                    <h5 class="card-title">{item.name}</h5>
                    <p class="card-text">{item.description}</p>
                    <div class="mt-auto">
                        <button class="btn btn-primary" onclick="{onclick_function_name}('{item.id}', '{item.name}')">select</button>
                    </div>
                </div>
            </div>
        </div>
        ''' for item in items
    )

    modal_html = f'''
    <div class="modal fade" id="{modal_id}" tabindex="-1" role="dialog" aria-labelledby="{modal_id}Label" aria-hidden="true">
        <div class="modal-dialog modal-lg modal-dialog-scrollable" role="document">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title" id="{modal_id}Label">{modal_title}</h5>
                    </button>
                </div>
                <div class="modal-body">
                    <div class="row">
                        {items_cards_html}
                    </div>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" onclick="{close_function_name}()">close</button>
                </div>
            </div>
        </div>
    </div>
    '''

    return Markup(modal_html)



def Modal(modal_id, modal_title, form_id, fields, submit_text='Save', button_text='Open', form_action=None, method='POST', modal_type='add', submit_function=None):

    form_fields_html = ''
    for field in fields:
        readonly = 'readonly' if modal_type == 'edit' and field.get('readonly', False) else ''
        required = 'required' if field.get('required', False) else ''
        
        # Generate IDs for the form fields
        field_id = f"{form_id}{field['name'].capitalize()}"

        if field['type'] == 'hidden':
            form_fields_html += f'''
                <input type="hidden" id="{field_id}" name="{field['name']}">
            '''
        elif field['type'] in ['text', 'date', 'time', 'email', 'number']:
            form_fields_html += f'''
                <div class="form-group">
                    <label for="{field_id}">{field['label']}</label>
                    <input type="{field['type']}" class="form-control" id="{field_id}" name="{field['name']}" {required} {readonly}>
                </div>
            '''
        elif field['type'] == 'select':
            options = field.get('options', [])
            options_html = ''.join(f'<option value="{option.id}">{option.name}</option>' for option in options)
            onchange = field.get('attributes', {}).get('onchange', '')
            form_fields_html += f'''
                <div class="form-group">
                    <label for="{field_id}">{field['label']}</label>
                    <select class="form-control" id="{field_id}" name="{field['name']}" {required} {readonly} onchange="{onchange}">
                        {options_html}
                    </select>
                </div>
            '''
        elif field['type'] == 'textarea':
            form_fields_html += f'''
                <div class="form-group">
                    <label for="{field_id}">{field['label']}</label>
                    <textarea class="form-control" id="{field_id}" name="{field['name']}" rows="3" {required} {readonly}></textarea>
                </div>
            '''
        elif field['type'] == 'file':
            form_fields_html += f'''
                <div class="form-group">
                    <label for="{field_id}">{field['label']}</label>
                    <input type="file" class="form-control-file" id="{field_id}" name="{field['name']}" {required}>
                </div>
            '''
        elif field['type'] == 'color':
            form_fields_html += f'''
                <div class="form-group">
                    <label for="{field_id}">{field['label']}</label>
                    <input type="text" class="form-control color-picker" id="{field_id}" name="{field['name']}" {required} {readonly} style="cursor: pointer;">
                </div>
            '''
    
    # Add a hidden input for field2substitute
    form_fields_html += '''
        <div id="field2substitute" name="field2substitute"></div>
    '''

    # Use the provided submit function or default to 'submitForm'
    submit_function_js = submit_function if submit_function else 'submitForm()'
    
    modal_html = f'''
        <div class="modal fade" id="{modal_id}" tabindex="-1" role="dialog" aria-labelledby="{modal_id}Label" aria-hidden="true">
            <div class="modal-dialog modal-dialog-scrollable" role="document">
                <div class="modal-content">
                    <form id="{form_id}" action="{form_action or '#'}" method="{method}" enctype="multipart/form-data">
                        <div class="modal-header">
                            <h5 class="modal-title" id="{modal_id}Label">{modal_title}</h5>
                            <button type="button" class="close" data-dismiss="modal" aria-label="Close" id="closeModalButton">
                                <span aria-hidden="true">&times;</span>
                            </button>
                        </div>
                        <div class="modal-body" style="max-height: 60vh; overflow-y: auto;">
                            {form_fields_html}
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-dismiss="modal" id="closeModalFooter">close</button>
                            <button type="button" class="btn btn-primary" onclick="{submit_function_js}">{submit_text}</button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    '''

    return Markup(modal_html)




from markupsafe import escape
from datetime import datetime, time

def DynamicTable(table_id, columns, items, actions=None, toggle_column=None):
    
    def get_nested_value(obj, field):
        if '.' in field:
            parent, child = field.split('.')
            parent_obj = getattr(obj, parent, None)
            return getattr(parent_obj, child, "") if parent_obj else ""
        return getattr(obj, field, "")

    def format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        return value

    def format_time(value):
        if isinstance(value,  time):
            return value.strftime('%H:%M')
            
        return value

    def sanitize_input(value):
        if value is None:
            return ""
        return escape(value).replace('\n', '\\n').replace('\r', '')
    
    # Create table headers
    headers_html = ''.join(f'<th class="text-left">{escape(col["header"])}</th>' for col in columns if col.get('type') != 'hidden')
    
    if toggle_column:
        headers_html += '<th>activated</th>'
    
    # Create table rows from items
    rows_html = ''
    for item in items:
        # Extract values for the row based on columns
        row_values = []
        for col in columns:
            value = get_nested_value(item, col["field"])

            if col.get('type') == 'humandate':
                value = format_datetime(value)
            if col.get('type') == 'humantime':
                value = format_time(value)
            if col.get('type') == 'hidden':
                row_values.append(f'<input type="hidden" name="{escape(col["field"])}" value="{escape(value)}">')
            elif col.get('type') == 'color' :
                row_values.append(f'<span style="display:inline-block;width:20px;height:20px;background-color:{escape(value)};border:1px solid #000;"></span> {escape(value)}')
            elif col.get('type') == 'msg' :
                row_values.append(Markup(value))
            elif col.get('type') == 'link' :
                value = f"<a href='#' onclick=\"loadTabContent('{col.get('tabname')}', 1, '{value}', '');\">{value}</a>"
                row_values.append(Markup(value))
            else:
                row_values.append(escape(value) if value is not None else "")


        
        row_html = ''.join(f'<td class="text-left">{value}</td>' for value in row_values if not '<input type="hidden"' in value)
        row_html += ''.join(value for value in row_values if '<input type="hidden"' in value)

        
        # Add toggle checkbox if applicable
        if toggle_column:
            toggle_value = get_nested_value(item, toggle_column['field'])
            toggle_checked = 'checked' if toggle_value else ''
            toggle_id = f'toggle_{get_nested_value(item, "id")}'
            row_html += f'''
                <td>
                    <input type="checkbox" id="{toggle_id}" {toggle_checked} 
                           onclick="toggleStatus({get_nested_value(item, 'id')}, '{toggle_column['url']}')" style="width: 20px; height: 20px;">
                </td>
            '''
        
        # Add action buttons if any
        if actions:
            actions_html = ''
            for action in actions:
                params = [f'\'{sanitize_input(get_nested_value(item, field)) if get_nested_value(item, field) is not None else ""}\'' 
                          for field in action.get("params", [])]
                action_function = f'{action["function"]}({", ".join(params)})'
                actions_html += f'<a href="#" onclick="{action_function}" style="text-decoration: none;"><i class="fas fa-{action["icon"]}"></i>&nbsp&nbsp;</a> '
            
            if actions_html:
                row_html += f'<td>{actions_html}</td>'
        
        rows_html += f'<tr>{row_html}</tr>'
    
    # Create the final table HTML
    table_html = f'''
        <table class="table" id="{escape(table_id)}">
            <thead>
                <tr>
                    {headers_html}
                    {'<th>actions</th>' if actions else ''}
                </tr>
            </thead>
            <tbody>
                {rows_html}
            </tbody>
        </table>
    '''

    return Markup(table_html)


def DynamicCard(card_id, columns, items, actions=None, toggle_column=None):
    
    def get_nested_value(obj, field):
        if '.' in field:
            parent, child = field.split('.')
            parent_obj = getattr(obj, parent, None)
            return getattr(parent_obj, child, "") if parent_obj else ""
        return getattr(obj, field, "")

    def format_datetime(value):
        if isinstance(value, datetime):
            return value.strftime('%Y-%m-%d %H:%M')
        return value

    def format_time(value):
        if isinstance(value, time):
            return value.strftime('%H:%M')
            
        return value

    # Create card content from items
    cards_html = ''
    for item in items:

        # background_image_url = item.background_image if item and item.background_image else ''

        background_image_url = '/static/uploads/0ce1438e-74cd-488f-b347-22770183f16b_fig3.png'        
        # Extract values for the card based on columns
        card_values = []
        for col in columns:
            value = get_nested_value(item, col["field"])
            if col.get('type') == 'humandate':
                value = format_datetime(value)
            if col.get('type') == 'humantime':
                value = format_time(value)
            
            if col.get('type') == 'hidden':
                card_values.append(f'<input type="hidden" name="{escape(col["field"])}" value="{escape(value)}">')
            elif col.get('type') == 'color':
                card_values.append(f'<span style="display:inline-block;width:20px;height:20px;background-color:{escape(value)};border:1px solid #000;"></span> {escape(value)}')
            elif col.get('type') == 'link' :
                linevalue = f'<p><strong>{escape(col["header"])}: </strong>'
                linevalue += f"<a href='#' onclick=\"loadTabContent('{col.get('tabname')}', 1, '{value}', '');\">{value}</a>"
                card_values.append(Markup(linevalue))
            else:
                card_values.append(f'<p><strong>{escape(col["header"])}:</strong> {escape(value) if value is not None else ""}</p>')

        # Concatenate all card values
        main_content_html = ''.join(card_values)
        
        # Add toggle checkbox if applicable
        if toggle_column:
            toggle_value = get_nested_value(item, toggle_column['field'])
            toggle_checked = 'checked' if toggle_value else ''
            toggle_id = f'toggle_{get_nested_value(item, "id")}'
            main_content_html += f'''
                <div style="display: flex; justify-content: center; align-items: center;">
                    <label>Activated:</label>
                    <input type="checkbox" id="{toggle_id}" {toggle_checked} 
                           onclick="toggleStatus({get_nested_value(item, 'id')}, '{toggle_column['url']}')">
                </div>
            '''
        
        # Create action icons column
        actions_html = ''
        if actions:
            for action in actions:
                params = [f'\'{escape(get_nested_value(item, field)) if get_nested_value(item, field) is not None else ""}\'' 
                          for field in action.get("params", [])]
                action_function = f'{action["function"]}({", ".join(params)})'
                actions_html += f'<a href="#" onclick="{action_function}" style="text-decoration: none;"><i class="fas fa-{action["icon"]}"></i></a><br>'

        # Combine main content and actions side by side
        card_html = f'''
            <div style="display: flex; align-items: flex-start; justify-content: space-between;">
                <div style="flex: 1; align-items: flex-start;">{main_content_html}</div>
                <div style="display: flex; flex-direction: column; align-items: center; margin-left: 1rem;">
                    {actions_html}
                </div>
            </div>
        '''
        
        # Wrap the card content in a card structure
        cards_html += f'''
            <div class="card" style="width: 20rem; margin: 0.3rem; display: inline-block; background-color: #f0f0f0; position: relative;">
                <!-- Background image element -->
                <div class="card-background" style="position: absolute; top: 0; left: 0; right: 0; bottom: 0;
                background-size: cover;
                background-position: center;
                opacity: 0.7; z-index: -1; min-height: 200px; height: 100%;"></div>
                <!-- Card content -->
                <div class="card-body">
                    {card_html}
                </div>
            </div>
        '''
    # Create the final card HTML
    card_container_html = f'''
        <div class="card-container" id="{escape(card_id)}" style="display: flex; flex-wrap: wrap; justify-content: space-around;">
            {cards_html}
        </div>
    '''

    return Markup(card_container_html)
    

def Pagination(pagination_data):
    pagination_html = '<ul class="pagination">'
    
    # Handle previous page link
    if pagination_data.has_prev:
        prev_page = pagination_data.prev_num
        pagination_html += f'''
            <li class="page-item">
                <a class="page-link" href="#" data-page="{prev_page}">back</a>
            </li>
        '''
    
    # Handle next page link
    if pagination_data.has_next:
        next_page = pagination_data.next_num
        pagination_html += f'''
            <li class="page-item">
                <a class="page-link" href="#" data-page="{next_page}">to</a>
            </li>
        '''
    
    pagination_html += '</ul>'
    return Markup(pagination_html)
