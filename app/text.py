#!flask/bin/python
# -*- coding: utf-8 -*-

import re
import operator
import functools

from app import app
from app.wordlists import *

def de_hyphen_non_coded_words(word):
    if word.find("-"):
        for coded_word in hyphenated_coded_words:
            if word.startswith(coded_word):
                return [word]
        return word.split("-")
    return [word]

def clean_up_text(messy_text):
    text = re.sub("[\\s]", " ", messy_text, 0, 0)
    text = re.sub(u"[\.\t\,“”‘’<>\*\?\!\"\[\]\@\':;\(\)\./&]", " ", text, 0, 0)
    text = re.sub(u"[—–]", "-", text, 0, 0)
    return text.lower()

def clean_up_word_list(text):
    word_list = filter(lambda x: x, text.split(" "))
    return functools.reduce(operator.concat, map(de_hyphen_non_coded_words, word_list))

class Text:

    def __init__(self, ad_text):
        self.ad_text = ad_text
        self.__masculine_coded_words_array = []
        self.__feminine_coded_words_array = []
        self.analyse()

    def analyse(self):
        clean_text = clean_up_text(self.ad_text)
        word_list = clean_up_word_list(clean_text)
        self.extract_coded_words(word_list)
        self.extract_coded_sentences(re.sub(u"[-]", " ", clean_text, 0, 0))
        self.masculine_coded_words = (",").join(self.__masculine_coded_words_array)
        self.feminine_coded_words = (",").join(self.__feminine_coded_words_array)
        self.masculine_word_count = len(self.__masculine_coded_words_array)
        self.feminine_word_count = len(self.__feminine_coded_words_array)
        self.assess_coding()

    def clean_text(self):
        return self.ad_text

    def extract_coded_words(self, advert_word_list):
        words = self.find_coded_words(advert_word_list, masculine_coded_words)
        self.__masculine_coded_words_array += words
        words = self.find_coded_words(advert_word_list, feminine_coded_words)
        self.__feminine_coded_words_array += words

    def extract_coded_sentences(self, clean_text):
        words = self.find_sentences(clean_text, masculine_sentences)
        self.__masculine_coded_words_array += words
        words = self.find_sentences(clean_text, feminine_sentences)
        self.__feminine_coded_words_array += words

    def find_sentences(self, clean_text, sentences):
        sentences = [word for word in sentences
            if word in clean_text]
        return sentences

    def find_coded_words(self, advert_word_list, gendered_word_list):
        gender_coded_words = [word for word in advert_word_list
            for coded_word in gendered_word_list
            if word.startswith(coded_word)]
        return gender_coded_words

    def assess_coding(self):
        coding_score = self.feminine_word_count - self.masculine_word_count
        if coding_score == 0:
            self.coding = "neutral"
        elif coding_score > 3:
            self.coding = "strongly feminine-coded"
        elif coding_score > 0:
            self.coding = "feminine-coded"
        elif coding_score < -3:
            self.coding = "strongly masculine-coded"
        else:
            self.coding = "masculine-coded"
