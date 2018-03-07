# -*- coding: utf-8 -*-
import json
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from . import forms
from . import models


@login_required
def index(request):
    return redirect('harvester:sources')


@login_required
def sources(request):
    sources = models.Source.objects.all()
    return render(request, 'harvester/sources.html', {
        'sources': sources,
    })


@login_required
def source(request, id):
    source = get_object_or_404(models.Source, id=id)
    source_records_files = models.SourceRecordsFile.objects.filter(source=source)
    return render(request, 'harvester/source.html', {
        'source': source,
        'source_records_files': source_records_files,
    })


@login_required
def source_file(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_records_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    return render(request, 'harvester/source_file.html', {
        'source': source,
        'source_records_file': source_records_file,
    })


@login_required
def calculate_records_count(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_records_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    records_count = source_records_file.calculate_records_count()
    return HttpResponse(json.dumps({
        'result': records_count,
    }, ensure_ascii=False), content_type='application/json')


@login_required
def source_file_testing(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_records_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)

    position_type = 'index'
    position = 0
    view = 'html'

    testing_form = forms.SourceFileTestingForm(request.GET)
    if testing_form.is_valid():
        position_type = testing_form.cleaned_data['position_type'] or position_type
        position = testing_form.cleaned_data['position'] or position
        view = testing_form.cleaned_data['view'] or view

    record_dump = source_records_file.record_content(
        position_type=position_type,
        position=position,
        view=view,
    )

    return render(request, 'harvester/source_file_testing.html', {
        'source': source,
        'source_records_file': source_records_file,
        'record_dump': record_dump,
        'testing_form': testing_form,
    })


