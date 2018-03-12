from django import forms
from . import models

POSITION_TYPE_CHOICES = (
    ('index', 'Порядковый номер'),
    ('offset', 'Позиция в файле'),
)

VIEW_CHOICES = (
    ('html', 'HTML'),
    ('text', 'Текст')
)


class SourceForm(forms.ModelForm):
    class Meta:
        model = models.Source
        exclude = []


class SourceFileForm(forms.ModelForm):
    class Meta:
        model = models.SourceRecordsFile
        exclude = ['source']


class IndexingRuleForm(forms.ModelForm):
    class Meta:
        model = models.IndexingRule
        exclude = []


class SourceFileTestingForm(forms.Form):
    position_type = forms.ChoiceField(
        label='Тип позиции',
        choices=POSITION_TYPE_CHOICES,
        initial=POSITION_TYPE_CHOICES[0][0],
        required=False
    )
    position = forms.IntegerField(
        label='Позиция',
        initial=0,
        required=False
    )
    view = forms.ChoiceField(
        label='Представление',
        choices=VIEW_CHOICES,
        initial=POSITION_TYPE_CHOICES[0][0],
        required=False
    )
