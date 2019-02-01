#!flask/bin/python
# -*- coding: utf-8 -*-

import os
import unittest

from config import basedir
from app import app, db

from app.models import JobAd
from app.text import Text, de_hyphen_non_coded_words, clean_up_text, clean_up_word_list
from app import views

from unittest.mock import patch, Mock
from flask_testing import TestCase

class DecoderTest(TestCase):
    def create_app(self):
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir, 'test.db')
        app.config['PRESERVE_CONTEXT_ON_EXCEPTION'] = False

        return app

    def setUp(self):
        db.create_all()

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_clean_up_word_list(self):
        caps = clean_up_text("Sharing is as important as ambition")
        self.assertEqual(clean_up_word_list(caps),
            ['sharing', 'is', 'as', 'important', 'as', 'ambition'])
        tab = clean_up_text("Qualities: sharing\tambition")
        self.assertEqual(clean_up_word_list(tab),
            ['qualities', 'sharing', 'ambition'])
        semicolon = clean_up_text("Sharing;ambitious")
        self.assertEqual(clean_up_word_list(semicolon),
            ['sharing', 'ambitious'])
        slash = clean_up_text(u"Sharing/ambitious")
        self.assertEqual(clean_up_word_list(slash), ['sharing', 'ambitious'])
        hyphen = clean_up_text(u"Sharing, co-operative, 'servant-leader'")
        self.assertEqual(clean_up_word_list(hyphen),
            ['sharing', 'co-operative', 'servant', 'leader'])
        mdash = clean_up_text(u"Sharing—ambitious")
        self.assertEqual(clean_up_word_list(mdash), ['sharing', 'ambitious'])
        bracket = clean_up_text(u"Sharing(ambitious) and (leader)")
        self.assertEqual(clean_up_word_list(bracket), ['sharing', 'ambitious',
            'and', 'leader'])
        sqbracket = clean_up_text(u"Sharing[ambitious] and [leader]")
        self.assertEqual(clean_up_word_list(sqbracket), ['sharing',
            'ambitious', 'and', 'leader'])
        abracket = clean_up_text(u"Sharing<ambitious> and <leader>")
        self.assertEqual(clean_up_word_list(abracket), ['sharing',
            'ambitious', 'and', 'leader'])
        space = clean_up_text(u"Sharing ambitious ")
        self.assertEqual(clean_up_word_list(space), ['sharing', 'ambitious'])
        amp = clean_up_text(u"Sharing&ambitious, empathy&kindness,")
        self.assertEqual(clean_up_word_list(amp),
            ['sharing', 'ambitious', 'empathy', 'kindness'])
        asterisk = clean_up_text(u"Sharing&ambitious*, empathy*kindness,")
        self.assertEqual(clean_up_word_list(asterisk),
            ['sharing', 'ambitious', 'empathy', 'kindness'])
        atandquestion = clean_up_text(u"Lead \"Developer\" Who is Connect@HBS? We ")
        self.assertEqual(clean_up_word_list(atandquestion),
            ['lead', 'developer', 'who', 'is', 'connect', 'hbs', 'we'])
        exclaim = clean_up_text(u"Lead Developer v good!")
        self.assertEqual(clean_up_word_list(exclaim),
            ['lead', 'developer', 'v', 'good'])
        curls = clean_up_text(u"“Lead” ‘Developer’ v good!")
        self.assertEqual(clean_up_word_list(curls),
            ['lead', 'developer', 'v', 'good'])

    def test_extract_coded_words(self):
        j1 = Text(u"Ambition:competition-decisiveness, empathy&kindness")
        self.assertEqual(j1.masculine_coded_words,
            "ambition,competition,decisiveness")
        self.assertEqual(j1.masculine_word_count, 3)
        self.assertEqual(j1.feminine_coded_words, "empathy,kindness")
        self.assertEqual(j1.feminine_word_count, 2)
        j2 = Text(u"empathy&kindness")
        self.assertEqual(j2.masculine_coded_words, "")
        self.assertEqual(j2.masculine_word_count, 0)
        self.assertEqual(j2.feminine_coded_words, "empathy,kindness")
        self.assertEqual(j2.feminine_word_count, 2)
        j3 = Text(u"empathy irrelevant words kindness")
        self.assertEqual(j3.masculine_coded_words, "")
        self.assertEqual(j3.masculine_word_count, 0)
        self.assertEqual(j3.feminine_coded_words, "empathy,kindness")
        self.assertEqual(j3.feminine_word_count, 2)

    def test_extract_coded_sentences(self):
        j1 = Text(u"here is an Alpha Male oh yeah")
        self.assertEqual(j1.masculine_coded_words, "alpha male")
        self.assertEqual(j1.masculine_word_count, 1)
        self.assertEqual(j1.feminine_coded_words, "")
        self.assertEqual(j1.feminine_word_count, 0)
        j1 = Text(u"la prise-en-Charge de l'equipe")
        self.assertEqual(j1.feminine_coded_words, "prise en charge")
        self.assertEqual(j1.feminine_word_count, 1)
        self.assertEqual(j1.masculine_coded_words, "")
        self.assertEqual(j1.masculine_word_count, 0)

    def test_assess_coding_neutral(self):
        j1 = Text("irrelevant words")
        self.assertFalse(j1.masculine_word_count)
        self.assertFalse(j1.feminine_word_count)
        self.assertEqual(j1.coding, "neutral")
        j2 = Text("sharing versus aggression")
        self.assertEqual(j2.masculine_word_count, j2.feminine_word_count)
        self.assertEqual(j2.coding, "neutral")

    def test_assess_coding_masculine(self):
        j1 = Text(u"Ambition:competition-decisiveness, empathy&kindness")
        self.assertEqual(j1.masculine_word_count, 3)
        self.assertEqual(j1.feminine_word_count, 2)
        self.assertEqual(j1.coding, "masculine-coded")
        j2 = Text(u"Ambition:competition-decisiveness, other words")
        self.assertEqual(j2.masculine_word_count, 3)
        self.assertEqual(j2.feminine_word_count, 0)
        self.assertEqual(j2.coding, "masculine-coded")
        j3 = Text(u"Ambition:competition-decisiveness&leadership, other words")
        self.assertEqual(j3.masculine_word_count, 4)
        self.assertEqual(j3.feminine_word_count, 0)
        self.assertEqual(j3.coding, "strongly masculine-coded")
        # NB: repeated "decisiveness" in j4
        j4 = Text(u"Ambition:competition-decisiveness&leadership,"
            " decisiveness, stubborness, sharing and empathy")
        self.assertEqual(j4.masculine_word_count, 6)
        self.assertEqual(j4.feminine_word_count, 2)
        self.assertEqual(j4.coding, "strongly masculine-coded")

    def test_assess_coding_feminine(self):
        j1 = Text(u"Ambition:competition, empathy&kindness, co-operation")
        self.assertEqual(j1.masculine_word_count, 2)
        self.assertEqual(j1.feminine_word_count, 3)
        self.assertEqual(j1.coding, "feminine-coded")
        j2 = Text(u"empathy&kindness, co-operation and some other words")
        self.assertEqual(j2.masculine_word_count, 0)
        self.assertEqual(j2.feminine_word_count, 3)
        self.assertEqual(j2.coding, "feminine-coded")
        j3 = Text(u"empathy&kindness, co-operation, trust and other words")
        self.assertEqual(j3.masculine_word_count, 0)
        self.assertEqual(j3.feminine_word_count, 4)
        self.assertEqual(j3.coding, "strongly feminine-coded")
        j4 = Text(u"Ambition:competition, empathy&kindness and"
            " responsibility, co-operation, honesty, trust and other words")
        self.assertEqual(j4.masculine_word_count, 2)
        self.assertEqual(j4.feminine_word_count, 6)
        self.assertEqual(j4.coding, "strongly feminine-coded")

    def test_analyse(self):
        j1 = Text(u"Ambition:competition-decisiveness&leadership,"
            " decisiveness, stubborness, sharing and empathy")
        self.assertEqual(j1.ad_text, u"Ambition:competition-decisiveness"
            "&leadership, decisiveness, stubborness, sharing and empathy")
        self.assertTrue(j1.coding == "strongly masculine-coded")
        self.assertEqual(j1.masculine_word_count, 6)
        self.assertEqual(j1.masculine_coded_words, "ambition,competition,"
                "decisiveness,leadership,decisiveness,stubborness")
        self.assertEqual(j1.feminine_word_count, 2)
        self.assertEqual(j1.feminine_coded_words,"sharing,empathy")

    def test_de_hyphen_non_coded_words(self):
        self.assertEqual(['competition', 'decisiveness'], de_hyphen_non_coded_words('competition-decisiveness'))

    def test_clean_up_text(self):
        self.assertEqual('blabla-blabla', clean_up_text('blabla—blabla'))
        self.assertEqual('blabla-blabla', clean_up_text('blabla–blabla'))
        self.assertEqual('unabhängig', clean_up_text('unabhängig'))

    def test_job_ad_saved(self):
        j1 = JobAd(Text(u"analytical, empathy, sharing"), "fritz", "fritz AG", "fritz@example.com")

        self.assertEqual(1, JobAd.query.count())
        dbjobad = JobAd.query.first();

        self.assertEqual("analytical, empathy, sharing", dbjobad.ad_text)
        self.assertEqual(1, dbjobad.masculine_word_count)
        self.assertEqual(2, dbjobad.feminine_word_count)
        self.assertEqual("empathy,sharing", dbjobad.feminine_coded_words)
        self.assertEqual("analytical", dbjobad.masculine_coded_words)
        self.assertEqual("fritz", dbjobad.name)
        self.assertEqual("fritz AG", dbjobad.company)
        self.assertEqual("fritz@example.com", dbjobad.email)
        self.assertIsNotNone(dbjobad.hash)
        self.assertIsNotNone(dbjobad.date)

    def test_list_words(self):
        text = Text(u"leader leader leader, ambition, ambition, competition")
        j1 = JobAd(text, "", "", "")

        masc_words, fem_words = j1.list_words()
        self.assertEqual(masc_words, ['leader (3 times)', 'ambition (2 times)', 'competition'])

    def test_results_view(self):
        j1 = JobAd(Text(u"analytical, empathy, sharing"), "fritz", "fritz AG", "fritz@example.com")

        data = self.client.get('/results/' + j1.hash)
        self.assert200(data)
        self.assert_template_used('results.html')
        self.assert_context("feminine_coded_words", ['empathy', 'sharing'])
        self.assert_context("masculine_coded_words", ['analytical'])

    @patch('app.views.send_email')
    def test_email_sent(self, mock_send_email):
        data = dict(
            texttotest = "analytical",
            name = "fritz",
            company = "fritz AG",
            email = "fritz@example.com"
        )
        resp = self.client.post('/', data=data)
        mock_send_email.assert_called_once_with(app.config['EMAIL_TO_NOTIFY'], dict(
            text = "analytical",
            name = "fritz",
            company = "fritz AG",
            email = "fritz@example.com",
            hash = JobAd.query.first().hash
        ))
        self.assertEqual(resp.status_code, 302)


if __name__ == '__main__':
    unittest.main()
