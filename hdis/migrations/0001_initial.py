# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'HowDoISpeakUser'
        db.create_table(u'hdis_howdoispeakuser', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('email', self.gf('django.db.models.fields.CharField')(max_length=500)),
            ('enqueued', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('processed', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created_when', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('user_pin', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal(u'hdis', ['HowDoISpeakUser'])


    def backwards(self, orm):
        # Deleting model 'HowDoISpeakUser'
        db.delete_table(u'hdis_howdoispeakuser')


    models = {
        u'hdis.howdoispeakuser': {
            'Meta': {'object_name': 'HowDoISpeakUser'},
            'created_when': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.CharField', [], {'max_length': '500'}),
            'enqueued': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'processed': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'user_pin': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        }
    }

    complete_apps = ['hdis']