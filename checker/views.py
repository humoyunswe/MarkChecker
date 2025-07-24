import json
from .forms import ProductListForm
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
