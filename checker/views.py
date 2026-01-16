import json
from .forms import ProductListForm, MarkCodesForm, AggregateCodesForm, StatusChangeForm
from django import forms
from django.views import View
from django.http import HttpResponse
from django.shortcuts import render
import requests
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from .models import History
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, DetailView

class ProductListForm(forms.Form):
    products = forms.CharField(
        label='Product List (JSON)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '[{"gtin": "...", "price": 1, "total": 0, "productName": "...", "totalAmount": 0}]', 'rows': 6}),
        help_text='Вставьте JSON-массив продуктов с полями gtin, price, total, productName, totalAmount.'
    )
    mark_id = forms.CharField(label='Mark ID', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mark ID'}))
    innbin = forms.CharField(label='INN/БИН', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter INN/БИН'}))

@method_decorator(login_required, name='dispatch')
class MarkCheckerView(View):
    template_name = 'checker/mark_checker.html'

    def get(self, request):
        form = ProductListForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = ProductListForm(request.POST)
        result = None
        error = None
        gtin_counts = []
        updated_products = []
        products_json = ''
        if form.is_valid():
            mark_id = form.cleaned_data['mark_id']
            innbin = form.cleaned_data['innbin']
            products_json = form.cleaned_data['products']
            try:
                products = json.loads(products_json)
                url = f'https://edo.markirovka.kz/adm/camunda/api/v1/private/document/codesList/{mark_id}'
                headers = {
                    'Authorization': 'Basic Q2FtdW5kYUdvbGFuZzpwcygmY21fbHFB',
                    'Commoditygroup': 'pharma',
                    'Content-Type': 'application/json',
                    'Innbin': innbin,
                    'language': 'en',
                }
                response = requests.get(url, headers=headers, timeout=10)
                response.raise_for_status()
                data = response.json()
                marks = list(set(data.get('marks', [])))
                # Считаем количество марок для каждого gtin
                gtin_to_count = {}
                for product in products:
                    gtin = product.get('gtin')
                    count = sum(1 for mark in marks if gtin and gtin in mark)
                    gtin_to_count[gtin] = count
                # Обновляем продукты
                updated_products = []
                for product in products:
                    gtin = product.get('gtin')
                    price = product.get('price', 0)
                    count = gtin_to_count.get(gtin, 0)
                    product['total'] = count
                    product['totalAmount'] = price * count
                    updated_products.append(product)
                # Формируем список для отображения
                gtin_counts = [{'gtin': gtin, 'count': count} for gtin, count in gtin_to_count.items()]
                result = {
                    'total': len(marks),
                    'gtin_counts': gtin_counts,
                    'updated_products': updated_products,
                    'products_json': json.dumps(updated_products, ensure_ascii=False, indent=2)
                }
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='check_marks',
                    details={
                        'input': {
                            'mark_id': mark_id,
                            'innbin': innbin,
                            'products': products,
                        },
                        'result': {
                            'total': len(marks),
                            'gtin_counts': gtin_counts,
                            'updated_products': updated_products,
                        }
                    }
                )
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})

class HistoryListView(LoginRequiredMixin, ListView):
    model = History
    template_name = 'checker/history_list.html'
    context_object_name = 'history_list'
    ordering = ['-created_at']

    def get_queryset(self):
        return History.objects.filter(user=self.request.user).order_by('-created_at')

class HistoryDetailView(LoginRequiredMixin, DetailView):
    model = History
    template_name = 'checker/history_detail.html'
    context_object_name = 'history'

@method_decorator(login_required, name='dispatch')
class MarkLimitView(View):
    template_name = 'checker/mark_limit.html'

    def get_token(self):
        """Получение токена для API"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/get-token"
        data = {
            "username": "arailym.sharipova@digitaleconomy.kz",
            "password": "Qwerty123"
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    return token
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def fetch_km_info(self, token, bin_code, codes):
        """Запрос информации о марках"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "bin": bin_code,
            "codes": codes
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

    def get(self, request):
        form = MarkCodesForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MarkCodesForm(request.POST)
        result = None
        error = None
        sql_queries = []
        api_response = None
        
        if form.is_valid():
            mark_codes_json = form.cleaned_data['mark_codes']
            bin_code = form.cleaned_data['bin']
            
            try:
                mark_codes = json.loads(mark_codes_json)
                
                if not isinstance(mark_codes, list):
                    error = 'Ошибка: Введите список марок в формате JSON-массива'
                    return render(request, self.template_name, {'form': form, 'result': result, 'error': error})
                
                # Получаем токен и информацию о марках
                token = self.get_token()
                if token:
                    api_response = self.fetch_km_info(token, bin_code, mark_codes)
                
                # Обработка каждой марки для SQL
                skipped_codes = 0
                for code in mark_codes:
                    if not isinstance(code, str):
                        skipped_codes += 1
                        continue
                        
                    if len(code) < 16:
                        skipped_codes += 1
                        continue

                    # Проверка, что код начинается с "01" (марки)
                    if not code.startswith("01"):
                        skipped_codes += 1
                        continue

                    # Извлечение GTIN (с 3 по 14 символ, индекс 2 до 15)
                    gtin = code[2:16]

                    # Формирование SQL-запроса
                    update_query = (
                        f"UPDATE docflow_go.marks_go SET temp_doc_id = 0 "
                        f"WHERE id = '{code}' and gtin = '{gtin}' "
                        f'AND "Type"=1 AND prod_group = \'pharma\';\n'
                    )
                    sql_queries.append(update_query)
                
                # Объединяем все запросы
                full_sql = ''.join(sql_queries)
                
                result = {
                    'total_codes': len(mark_codes),
                    'processed_codes': len(sql_queries),
                    'skipped_codes': skipped_codes,
                    'sql_content': full_sql,
                    'api_response': api_response,
                    'api_response_json': json.dumps(api_response, ensure_ascii=False, indent=2) if api_response else None
                }
                
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='process_mark_codes',
                    details={
                        'input': {
                            'mark_codes': mark_codes,
                            'bin': bin_code,
                        },
                        'result': {
                            'total_codes': len(mark_codes),
                            'processed_codes': len(sql_queries),
                            'api_response': api_response,
                        }
                    }
                )
                
            except json.JSONDecodeError:
                error = 'Ошибка: Неверный формат JSON'
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        else:
            error = 'Ошибка валидации формы'
            
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})

@method_decorator(login_required, name='dispatch')
class UpdateArchiveView(View):
    template_name = 'checker/update_archive.html'

    def get_token(self):
        """Получение токена для API"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/get-token"
        data = {
            "username": "arailym.sharipova@digitaleconomy.kz",
            "password": "Qwerty123"
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    return token
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def fetch_km_info(self, token, bin_code, codes):
        """Запрос информации о марках"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "bin": bin_code,
            "codes": codes
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

    def get(self, request):
        form = MarkCodesForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MarkCodesForm(request.POST)
        result = None
        error = None
        sql_queries = []
        api_response = None
        
        if form.is_valid():
            mark_codes_json = form.cleaned_data['mark_codes']
            bin_code = form.cleaned_data['bin']
            
            try:
                mark_codes = json.loads(mark_codes_json)
                
                if not isinstance(mark_codes, list):
                    error = 'Ошибка: Введите список марок в формате JSON-массива'
                    return render(request, self.template_name, {'form': form, 'result': result, 'error': error})
                
                # Получаем токен и информацию о марках
                token = self.get_token()
                if token:
                    api_response = self.fetch_km_info(token, bin_code, mark_codes)
                
                # Обработка каждой марки для SQL
                skipped_codes = 0
                for code in mark_codes:
                    if not isinstance(code, str):
                        skipped_codes += 1
                        continue
                        
                    if len(code) < 16:
                        skipped_codes += 1
                        continue

                    # Проверка, что код начинается с "01" (марки)
                    if not code.startswith("01"):
                        skipped_codes += 1
                        continue

                    # Формирование SQL-запроса для архива
                    update_arch_query = (
                        f"UPDATE docflow_go.marks_go_arch SET origin_category = 'СТАЦИОНАР' "
                        f"WHERE id = '{code}' AND prod_group = 'pharma';\n"
                    )
                    sql_queries.append(update_arch_query)
                
                # Объединяем все запросы
                full_sql = ''.join(sql_queries)
                
                result = {
                    'total_codes': len(mark_codes),
                    'processed_codes': len(sql_queries),
                    'skipped_codes': skipped_codes,
                    'sql_content': full_sql,
                    'api_response': api_response,
                    'api_response_json': json.dumps(api_response, ensure_ascii=False, indent=2) if api_response else None
                }
                
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='update_archive',
                    details={
                        'input': {
                            'mark_codes': mark_codes,
                            'bin': bin_code,
                        },
                        'result': {
                            'total_codes': len(mark_codes),
                            'processed_codes': len(sql_queries),
                            'api_response': api_response,
                        }
                    }
                )
                
            except json.JSONDecodeError:
                error = 'Ошибка: Неверный формат JSON'
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        else:
            error = 'Ошибка валидации формы'
            
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})

@method_decorator(login_required, name='dispatch')
class DeleteMarkView(View):
    template_name = 'checker/delete_mark.html'

    def get_token(self):
        """Получение токена для API"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/get-token"
        data = {
            "username": "arailym.sharipova@digitaleconomy.kz",
            "password": "Qwerty123"
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    return token
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def fetch_km_info(self, token, bin_code, codes):
        """Запрос информации о марках"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "bin": bin_code,
            "codes": codes
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

    def get(self, request):
        form = MarkCodesForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = MarkCodesForm(request.POST)
        result = None
        error = None
        sql_queries = []
        api_response = None
        
        if form.is_valid():
            mark_codes_json = form.cleaned_data['mark_codes']
            bin_code = form.cleaned_data['bin']
            
            try:
                mark_codes = json.loads(mark_codes_json)
                
                if not isinstance(mark_codes, list):
                    error = 'Ошибка: Введите список марок в формате JSON-массива'
                    return render(request, self.template_name, {'form': form, 'result': result, 'error': error})
                
                # Получаем токен и информацию о марках
                token = self.get_token()
                if token:
                    api_response = self.fetch_km_info(token, bin_code, mark_codes)
                
                # Обработка каждой марки для SQL
                skipped_codes = 0
                for code in mark_codes:
                    if not isinstance(code, str):
                        skipped_codes += 1
                        continue
                        
                    if len(code) < 16:
                        skipped_codes += 1
                        continue

                    # Проверка, что код начинается с "01" (марки)
                    if not code.startswith("01"):
                        skipped_codes += 1
                        continue

                    # Извлечение GTIN (с 3 по 14 символ, индекс 2 до 15)
                    gtin = code[2:16]

                    # Формирование SQL-запроса для удаления марки
                    delete_query = (
                        f"DELETE FROM docflow_go.marks_go "
                        f"WHERE id = '{code}' AND gtin = '{gtin}' "
                        f'AND "Type" = 1 AND prod_group = \'pharma\';\n'
                    )
                    sql_queries.append(delete_query)
                
                # Объединяем все запросы
                full_sql = ''.join(sql_queries)
                
                result = {
                    'total_codes': len(mark_codes),
                    'processed_codes': len(sql_queries),
                    'skipped_codes': skipped_codes,
                    'sql_content': full_sql,
                    'api_response': api_response,
                    'api_response_json': json.dumps(api_response, ensure_ascii=False, indent=2) if api_response else None
                }
                
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='delete_marks',
                    details={
                        'input': {
                            'mark_codes': mark_codes,
                            'bin': bin_code,
                        },
                        'result': {
                            'total_codes': len(mark_codes),
                            'processed_codes': len(sql_queries),
                            'api_response': api_response,
                        }
                    }
                )
                
            except json.JSONDecodeError:
                error = 'Ошибка: Неверный формат JSON'
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        else:
            error = 'Ошибка валидации формы'
            
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})

@method_decorator(login_required, name='dispatch')
class AggregateLimitView(View):
    template_name = 'checker/aggregate_limit.html'

    def get_token(self):
        """Получение токена для API"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/get-token"
        data = {
            "username": "arailym.sharipova@digitaleconomy.kz",
            "password": "Qwerty123"
        }
        
        try:
            response = requests.post(url, data=data, timeout=10)
            if response.status_code == 200:
                token = response.json().get("access_token")
                if token:
                    return token
                else:
                    return None
            else:
                return None
        except Exception:
            return None

    def fetch_km_info(self, token, bin_code, codes):
        """Запрос информации о марках"""
        url = "https://api.edo.markirovka.kz/apiUot/api/v1/private/info-km"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json"
        }
        payload = {
            "bin": bin_code,
            "codes": codes
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                return None
        except Exception:
            return None

    def get(self, request):
        form = AggregateCodesForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = AggregateCodesForm(request.POST)
        result = None
        error = None
        sql_queries = []
        api_response = None
        
        if form.is_valid():
            aggregate_codes_json = form.cleaned_data['aggregate_codes']
            bin_code = form.cleaned_data['bin']
            
            try:
                aggregate_codes = json.loads(aggregate_codes_json)
                
                if not isinstance(aggregate_codes, list):
                    error = 'Ошибка: Введите список кодов агрегатов в формате JSON-массива'
                    return render(request, self.template_name, {'form': form, 'result': result, 'error': error})
                
                # Получаем токен и информацию о марках
                token = self.get_token()
                if token:
                    api_response = self.fetch_km_info(token, bin_code, aggregate_codes)
                
                # Обработка каждой марки для SQL
                skipped_codes = 0
                for code in aggregate_codes:
                    if not isinstance(code, str):
                        skipped_codes += 1
                        continue
                        
                    if len(code) < 16:
                        skipped_codes += 1
                        continue

                    # Проверка, что код начинается с "00" (агрегаты)
                    if not code.startswith("00"):
                        skipped_codes += 1
                        continue

                    # Формирование SQL-запроса для агрегатов (Type=2)
                    update_query = (
                        f"UPDATE docflow_go.marks_go SET temp_doc_id = 0 "
                        f"WHERE id = '{code}' AND gtin = '' AND \"Type\"=2 AND prod_group = 'pharma';\n"
                    )
                    sql_queries.append(update_query)
                
                # Объединяем все запросы
                full_sql = ''.join(sql_queries)
                
                result = {
                    'total_codes': len(aggregate_codes),
                    'processed_codes': len(sql_queries),
                    'skipped_codes': skipped_codes,
                    'sql_content': full_sql,
                    'api_response': api_response,
                    'api_response_json': json.dumps(api_response, ensure_ascii=False, indent=2) if api_response else None
                }
                
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='process_aggregate_codes',
                    details={
                        'input': {
                            'aggregate_codes': aggregate_codes,
                            'bin': bin_code,
                        },
                        'result': {
                            'total_codes': len(aggregate_codes),
                            'processed_codes': len(sql_queries),
                            'api_response': api_response,
                        }
                    }
                )
                
            except json.JSONDecodeError:
                error = 'Ошибка: Неверный формат JSON'
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        else:
            error = 'Ошибка валидации формы'
            
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})


@method_decorator(login_required, name='dispatch')
class StatusChangeView(View):
    template_name = 'checker/status_change.html'

    def get(self, request):
        form = StatusChangeForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = StatusChangeForm(request.POST)
        result = None
        error = None

        if form.is_valid():
            id_list_json = form.cleaned_data['id_list']
            type_value = form.cleaned_data.get('type_value') or 2
            prod_group = form.cleaned_data.get('prod_group') or 'pharma'
            
            try:
                id_list = json.loads(id_list_json)
                
                if not isinstance(id_list, list):
                    error = 'Ошибка: ID список должен быть массивом JSON'
                    return render(request, self.template_name, {'form': form, 'error': error})

                sql_queries = []
                processed_count = 0
                skipped_count = 0
                
                for id_code in id_list:
                    if not isinstance(id_code, str):
                        skipped_count += 1
                        continue
                        
                    if len(id_code) < 16:
                        skipped_count += 1
                        continue

                    # Извлекаем GTIN из ID (символы с 2 по 16, всего 14 символов)
                
                    
                    # Формирование SQL-запроса для смены статуса
                    update_query = (
                        f"UPDATE docflow_go.marks_go SET in_circulation = false "
                        f"WHERE id = '{id_code}' AND \"Type\" = {type_value} "
                        f"AND gtin = ' ' AND prod_group = '{prod_group}';\n"
                    )
                    sql_queries.append(update_query)
                    processed_count += 1
                
                # Объединяем все запросы
                full_sql = ''.join(sql_queries)
                
                result = {
                    'total_codes': len(id_list),
                    'processed_codes': processed_count,
                    'skipped_codes': skipped_count,
                    'sql_content': full_sql,
                    'type_value': type_value,
                    'prod_group': prod_group
                }
                
                # Сохраняем историю
                History.objects.create(
                    user=request.user,
                    action='status_change',
                    details={
                        'input': {
                            'id_list': id_list,
                            'type_value': type_value,
                            'prod_group': prod_group,
                        },
                        'result': {
                            'total_codes': len(id_list),
                            'processed_codes': processed_count,
                            'skipped_codes': skipped_count,
                        }
                    }
                )
                
            except json.JSONDecodeError:
                error = 'Ошибка: Неверный формат JSON'
            except Exception as e:
                error = f'Ошибка: {str(e)}'
        else:
            error = 'Ошибка валидации формы'
            
        return render(request, self.template_name, {'form': form, 'result': result, 'error': error})
