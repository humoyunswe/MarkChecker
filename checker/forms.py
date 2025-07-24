from django import forms

class ProductListForm(forms.Form):
    products = forms.CharField(
        label='Product List (JSON)',
        widget=forms.Textarea(attrs={'class': 'form-control', 'placeholder': '[{"gtin": "...", "price": 1, "total": 0, "productName": "...", "totalAmount": 0}]', 'rows': 6}),
        help_text='Вставьте JSON-массив продуктов с полями gtin, price, total, productName, totalAmount.'
    )
    mark_id = forms.CharField(label='Mark ID', max_length=100, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mark ID'}))
    innbin = forms.CharField(label='INN/БИН', max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter INN/БИН'})) 