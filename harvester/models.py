# -*- coding: utf-8 -*-
import datetime as dt
import gzip
import hashlib
import time
import os

from django.db import models, transaction
from django.utils import timezone
from django.core.exceptions import ValidationError

from junimarc.iso2709.reader import Reader
from junimarc.json.junimarc import record_to_json
from junimarc.record import ControlField

FORMATS = {
    'iso2709': 'iso2709',
}

SCHEMAS = {
    'rusmarc': 'rusmarc',
}


class Source(models.Model):
    code = models.CharField(max_length=32, unique=True)
    name = models.CharField(max_length=128)
    reset = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    create_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code


FORMAT_CHOICES = [(k, v) for k, v in FORMATS.items()]
SCHEMA_CHOICES = [(k, v) for k, v in SCHEMAS.items()]


class SourceRecordsFile(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    file_uri = models.TextField(max_length=2048)
    format = models.CharField(max_length=64, default=FORMAT_CHOICES[0][0], choices=FORMAT_CHOICES)
    schema = models.CharField(max_length=64, default=SCHEMA_CHOICES[0][0], choices=SCHEMA_CHOICES)
    encoding = models.CharField(max_length=64, default='utf-8')

    def __str__(self):
        return str(self.source)

    def clean(self):
        if not os.path.isfile(self.file_uri):
            raise ValidationError('File does not exist')

    def status(self):
        if not os.path.exists(self.file_uri):
            return 'not exists'

        if not os.path.isfile(self.file_uri):
            return 'not file'

        if not os.access(self.file_uri, os.R_OK):
            return 'access denied'

        return 'ok'

    def get_size(self):
        if self.status() != 'ok':
            return 0
        return round(os.path.getsize(self.file_uri) / (1024 * 1024), 3)

    def get_update_date(self):
        return dt.datetime.fromtimestamp(os.path.getmtime(self.file_uri))

    def calculate_records_count(self):
        status = self.status()
        if status != 'ok':
            return status
        return Reader(self.file_uri).get_total_records()

    def record_content(self, position_type='index', position=0, view='text'):
        format = FORMATS.get(self.format)
        schema = SCHEMAS.get(self.schema)

        if not format:
            return 'No handler for format ' + self.format

        if not schema:
            return 'No handler for schema ' + self.schema

        target_record = None

        if format == FORMATS['iso2709']:
            extended_subfield_code = ''
            if schema == SCHEMAS['rusmarc']:
                extended_subfield_code = '1'

            reader = Reader(
                self.file_uri,
                encoding=self.encoding,
                extended_subfield_code=extended_subfield_code
            )

            for record in reader.read():
                if position_type == 'index':
                    if reader.index == position:
                        target_record = record
                        break
                    if reader.index > position:
                        break

                if position_type == 'offset':
                    if reader.offset == position:
                        target_record = record
                        break
                    if reader.offset > position:
                        break
        else:
            return 'No handler for format ' + self.format

        if target_record is None:
            return 'record unavaible or contain errors'

        if view == 'html':
            return target_record.to_html()

        return '<plaintext>%s</plaintext>' % (str(target_record),)


class HarvestingStatus(models.Model):
    source = models.ForeignKey(Source, on_delete=models.CASCADE)
    create_date = models.DateTimeField(db_index=True, auto_now_add=True)
    created = models.IntegerField(default=0)
    updated = models.IntegerField(default=0)
    deleted = models.IntegerField(default=0)
    processed = models.IntegerField(default=0)
    total_records = models.IntegerField(default=0)
    session_id = models.IntegerField(default=0)
    error = models.BooleanField(default=False)
    message = models.TextField(max_length=2018)


class Record(models.Model):
    id = models.CharField(primary_key=True, max_length=32)
    original_id = models.CharField(max_length=255, blank=True)
    hash = models.CharField(max_length=32)
    source = models.CharField(max_length=32, db_index=True)
    schema = models.CharField(max_length=32)
    session_id = models.BigIntegerField(default=0)
    create_date = models.DateTimeField(db_index=True)
    update_date = models.DateTimeField(db_index=True)
    deleted = models.BooleanField(default=False, db_index=True)


class GZipField(models.BinaryField):

    def get_db_prep_value(self, value, connection, prepared=False):
        cleaned_value = value
        if cleaned_value is not None:
            cleaned_value = gzip.compress(cleaned_value, compresslevel=7)
        return super().get_db_prep_value(cleaned_value, connection, prepared)

    def to_python(self, value):
        cleaned_value = value
        if cleaned_value is not None:
            cleaned_value = gzip.decompress(cleaned_value)
        return super().to_python(cleaned_value)


class RecordContent(models.Model):
    record = models.OneToOneField(Record, primary_key=True, on_delete=models.CASCADE)
    content = GZipField(max_length=100 * 1024)


def _get_record_id(jrecord, dump):
    fields_001 = jrecord.get_fields('001')
    record_id = ''
    hash = hashlib.md5(dump).hexdigest()
    for field_001 in fields_001:
        if not isinstance(field_001, ControlField):
            continue
        data = field_001.get_data()
        if data:
            record_id = data
            break

    if record_id:
        return hashlib.md5(record_id.encode('utf-8')).hexdigest(), record_id, hash

    return hash, record_id, hash


def create_records(record_containers):
    for record_container in record_containers:
        Record.objects.bulk_create([record_container['record']])
        RecordContent.objects.bulk_create([record_container['content']])


def update_records(record_containers):
    for record_container in record_containers:
        record_container['record'].save()
        record_content = record_container['content']
        RecordContent.objects.filter(record_id=record_content.record_id).update(content=record_content.content)


def reset_records(records):
    ids = set()
    session_id = None
    for record in records:
        ids.add(record.id)
        if not session_id:
            session_id = record.session_id

    if session_id:
        Record.objects.filter(id__in=ids).update(session_id=session_id)


def process_records(record_containers, reset=True):
    processed_record_containers_index = {}

    for record_container in record_containers:
        record = record_container['record']
        processed_record_containers_index[record.id] = record_container

    record_containers_for_create = []
    record_containers_for_update = []
    records_for_reset = []
    record_for_update_ids = set()

    records = Record.objects.filter(id__in=processed_record_containers_index.keys())

    for record in records:
        record_container = processed_record_containers_index.get(record.id)
        if record_container is not None:
            record_for_update_ids.add(record.id)
            precessed_record = record_container['record']

            if reset:
                record.session_id = precessed_record.session_id

            need_update = False

            if record.hash != precessed_record.hash or record.deleted != precessed_record.deleted:
                need_update = True

            if need_update:
                record.hash = precessed_record.hash
                record.update_date = precessed_record.update_date
                record.deleted = precessed_record.deleted
                record_containers_for_update.append({
                    'record': record,
                    'content': record_container['content']
                })
            elif reset:
                records_for_reset.append(record)

    for processed_record_id in processed_record_containers_index.keys():
        if processed_record_id not in record_for_update_ids:
            record_containers_for_create.append(processed_record_containers_index[processed_record_id])

    create_records(record_containers_for_create)
    update_records(record_containers_for_update)
    reset_records(records_for_reset)
    return len(record_containers_for_create), len(record_containers_for_update)


def get_percent(current, total):
    if total == 0:
        return 0
    return round(current * 100 / total)


def collect_file(source: Source, records_file: SourceRecordsFile, now, session_id):
    batch_size = 20
    processed = 0
    created = 0
    updated = 0
    deleted = 0

    extended_subfield_code = ''
    if records_file.schema == SCHEMAS['rusmarc']:
        extended_subfield_code = '1'

    print('Start collecting source', source, 'file', records_file.file_uri)
    print('Calculate total records...')
    reader = Reader(records_file.file_uri, extended_subfield_code=extended_subfield_code)
    total_records = reader.get_total_records()
    print('Total records', total_records)

    record_containers = []
    for rec in reader.read():
        errors = rec.get_errors()
        if errors:
            print(errors)

        processed += 1
        record_json = record_to_json(rec, dump=True)
        dump = record_json.encode('utf-8')
        record_id, original_id, record_hash = _get_record_id(rec, dump)
        record_containers.append({
            'record': Record(
                id=record_id,
                original_id=original_id,
                hash=record_hash,
                source=source,
                schema='junimarc',
                session_id=session_id,
                create_date=now,
                update_date=now,
            ),
            'content': RecordContent(record_id=record_id, content=dump)
        })

        if len(record_containers) >= batch_size:
            created_amount, updated_amount = process_records(record_containers, reset=source.reset)
            created += created_amount
            updated += updated_amount
            record_containers = []

        if processed % 100 == 0:
            print('processed', processed, get_percent(processed, total_records), '%')

    if record_containers:
        process_records(record_containers, reset=source.reset)

    if source.reset:
        deleted = Record.objects.filter(
            deleted=False
        ).exclude(
            session_id=session_id
        ).update(
            deleted=True,
            update_date=now
        )

    return {
        'processed': processed,
        'created': created,
        'updated': updated,
        'deleted': deleted,
        'total_records': total_records,
    }


def collect_source(source: Source):
    now = timezone.now()
    session_id = int(time.time())

    created = 0
    updated = 0
    deleted = 0
    processed = 0
    total_records = 0

    for source_file in SourceRecordsFile.objects.filter(source=source):
        stats = collect_file(source, source_file, session_id=session_id, now=now)
        created += stats['created']
        updated += stats['updated']
        deleted += stats['deleted']
        processed += stats['processed']
        total_records += stats['total_records']

    HarvestingStatus(
        source=source,
        create_date=now,
        created=created,
        updated=updated,
        deleted=deleted,
        processed=processed,
        total_records=total_records,
        session_id=session_id,
    ).save()

    print('processed', processed, get_percent(processed, total_records), '%')
    print('session id', session_id)
    print('total records', total_records)
    print('processed', processed)
    print('created', created)
    print('updated', updated)
    print('for delete', deleted)


@transaction.atomic()
def collect():
    for source in Source.objects.filter(active=True):
        collect_source(source)
