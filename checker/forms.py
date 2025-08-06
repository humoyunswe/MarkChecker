from django import forms

class ProductListForm(forms.Form):
    products = forms.CharField(
        label='Product List (JSON)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '[{"gtin": "...", "price": 1, "total": 0, "productName": "...", "totalAmount": 0}]', 'rows': 6}),
        help_text='Вставьте JSON-массив продуктов с полями gtin, price, total, productName, totalAmount.'
    )
    mark_id = forms.CharField(label='Mark ID', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mark ID'}))
    innbin = forms.CharField(label='INN/БИН', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter INN/БИН'}))

class MarkCodesForm(forms.Form):
    mark_codes = forms.CharField(
        label='Список марок',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': '["00348700051500007798", "00348700051500007866"]', 
            'rows': 8
        }),
        help_text='Вставьте JSON-массив с кодами марок для обработки. Коды должны начинаться с "00".'
    )
    bin = forms.CharField(
        label='БИН',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '850702450693'
        }),
        help_text='Введите БИН для запроса информации о марках.'
    )

class AggregateCodesForm(forms.Form):
    aggregate_codes = forms.CharField(
        label='Список кодов агрегатов',
        widget=forms.Textarea(attrs={
            'class': 'form-control', 
            'placeholder': '["0104870050000413215915270434233", "0104870050003896217317113859047"]', 
            'rows': 8
        }),
        help_text='Вставьте JSON-массив с кодами агрегатов для обработки. Коды должны начинаться с "01".'
    )
    bin = forms.CharField(
        label='БИН',
        max_length=12,
        widget=forms.TextInput(attrs={
            'class': 'form-control', 
            'placeholder': '850702450693'
        }),
        help_text='Введите БИН для запроса информации о марках.'
    ) 