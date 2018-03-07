from django import forms

POSITION_TYPE_CHOICES = (
    ('index', 'Порядковый номер'),
    ('offset', 'Позиция в файле'),
)

VIEW_CHOICES = (
    ('html', 'HTML'),
    ('text', 'Текст')
)


class SourceFileTestingForm(forms.Form):
    position_type = forms.ChoiceField(label='Тип позиции', choices=POSITION_TYPE_CHOICES, initial=POSITION_TYPE_CHOICES[0][0], required=False)
    position = forms.IntegerField(label='Позиция', initial=0, required=False)
    view = forms.ChoiceField(label='Представление', choices=VIEW_CHOICES, initial=POSITION_TYPE_CHOICES[0][0], required=False)
