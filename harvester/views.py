# -*- coding: utf-8 -*-
import json
from django.core.paginator import Paginator
from django.db.transaction import atomic
from django.contrib.auth.decorators import login_required

from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from . import forms
from . import models


@login_required
@atomic
def index(request):
    return render(request, 'harvester/index.html')


@login_required
@atomic
def sources(request):
    sources = models.Source.objects.all()

    return render(request, 'harvester/sources.html', {
        'sources': sources,
    })


@login_required
@atomic
def source(request, id):
    source = get_object_or_404(models.Source, id=id)
    source_records_files = models.SourceRecordsFile.objects.filter(source=source)
    return render(request, 'harvester/source.html', {
        'source': source,
        'source_records_files': source_records_files,
    })


@login_required
@atomic
def add_source(request):
    if request.method == 'POST':
        form = forms.SourceForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)
            source.save()
            return redirect('harvester:source', id=source.id)
    else:
        form = forms.SourceForm()
    return render(request, 'harvester/source_form.html', {
        'form': form,
    })


@login_required
@atomic
def change_source(request, id):
    source = get_object_or_404(models.Source, id=id)
    if request.method == 'POST':
        form = forms.SourceForm(request.POST, instance=source)
        if form.is_valid():
            form.save()
            return redirect('harvester:source', id=id)
    else:
        form = forms.SourceForm(instance=source)
    return render(request, 'harvester/source_form.html', {
        'form': form,
        'source': source
    })


@login_required
@atomic
def delete_source(request, id):
    source = get_object_or_404(models.Source, id=id)
    source.delete()
    return redirect('harvester:sources')


@login_required
@atomic
def source_file(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_records_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    return render(request, 'harvester/source_file.html', {
        'source': source,
        'source_records_file': source_records_file,
    })


@login_required
@atomic
def add_source_file(request, source_id):
    source = get_object_or_404(models.Source, id=source_id)
    if request.method == 'POST':
        form = forms.SourceFileForm(request.POST)
        if form.is_valid():
            source_file = form.save(commit=False)
            source_file.source = source
            source_file.save()
            return redirect('harvester:source', id=source.id)
    else:
        form = forms.SourceFileForm()
    return render(request, 'harvester/source_file_form.html', {
        'source': source,
        'form': form,
    })


@login_required
@atomic
def change_source_file(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    if request.method == 'POST':
        form = forms.SourceFileForm(request.POST, instance=source_file)
        if form.is_valid():
            source_file = form.save(commit=False)
            source_file.source = source
            source_file.save()
            return redirect('harvester:source_file', source_id=source.id, id=id)
    else:
        form = forms.SourceFileForm(instance=source_file)
    return render(request, 'harvester/source_file_form.html', {
        'source': source,
        'form': form,
        'source_file': source_file,
    })


@login_required
@atomic
def delete_source_file(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    source_file.delete()
    return redirect('harvester:source', id=source.id)


@login_required
@atomic
def records(request, source_id):
    source = get_object_or_404(models.Source, id=source_id)
    records_list = models.Record.objects.filter(source=source)
    paginator = Paginator(records_list, 25)  # Show 25 contacts per page

    page = request.GET.get('page')
    records = paginator.get_page(page)
    return render(request, 'harvester/records.html', {
        'records': records,
        'source': source,
    })


@login_required
@atomic
def collect_source(request, source_id):
    source = get_object_or_404(models.Source, id=source_id)
    models.collect_source(source)
    return redirect('harvester:records', source_id=source_id)


@login_required
@atomic
def harvesting_status(request, source_id):
    source = get_object_or_404(models.Source, id=source_id)
    harvesting_status_list = models.HarvestingStatus.objects.filter(source=source).order_by('-create_date')
    return render(request, 'harvester/harvesting_status_list.html', {
        'harvesting_status_list': harvesting_status_list,
        'source': source,
    })


@login_required
@atomic
def indexing_rules(request):
    indexing_rules = models.IndexingRule.objects.all()
    return render(request, 'harvester/indexing_rules.html', {
        'indexing_rules': indexing_rules
    })


@login_required
@atomic
def add_indexing_rules(request):
    if request.method == 'POST':
        form = forms.IndexingRuleForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('harvester:indexing_rules')
    else:
        form = forms.IndexingRuleForm()
    return render(request, 'harvester/indexing_rule_form.html', {
        'form': form
    })


@login_required
@atomic
def change_indexing_rules(request, id):
    indexing_rule = get_object_or_404(models.IndexingRule, id=id)
    if request.method == 'POST':
        form = forms.IndexingRuleForm(request.POST, instance=indexing_rule)
        if form.is_valid():
            form.save()
            return redirect('harvester:indexing_rules')
    else:
        form = forms.IndexingRuleForm(instance=indexing_rule)
    return render(request, 'harvester/indexing_rule_form.html', {
        'form': form
    })


@login_required
@atomic
def invoke_indexing_rule(request, id):
    indexing_rule = get_object_or_404(models.IndexingRule, id=id)
    indexing_document = {}
    # d = dict(locals(), **globals())
    c = compile(indexing_rule.content.strip(), 'My Code', 'exec')
    res = exec(c)
    print(indexing_document)
    return redirect('harvester:indexing_rules')


@login_required
@atomic
def calculate_records_count(request, source_id, id):
    source = get_object_or_404(models.Source, id=source_id)
    source_records_file = get_object_or_404(models.SourceRecordsFile, source=source, id=id)
    records_count = source_records_file.calculate_records_count()
    return HttpResponse(json.dumps({
        'result': records_count,
    }, ensure_ascii=False), content_type='application/json')


@login_required
@atomic
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
