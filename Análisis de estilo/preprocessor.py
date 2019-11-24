# -*- coding: utf-8 -*-
"""
Created on Sun Nov 17 18:27:33 2019

@author: Carlos
"""

from __future__ import print_function
from email_reply_parser import EmailReplyParser
import base64
import os
import csv
import spacy

TAGS_BREAKS_LINE = {'/p', '/div', 'br', 'br/'}
BREAK_LINE = {'\n', '\r'}

class Preprocessor:
    
    def __init__(self, raw_msgs, msgs, cv_raw, cv_msgs):
        """
        Class constructor.
        
        Parameters
        ----------
        raw_msgs: list
            List of extracted messages.
        msgs: list
            List of preprocessed messages which were obtained from raw_msgs.
        cv_raw: multiprocessing.Condition
            Conditional variable for accessing raw_msgs.
        cv_msgs: multiprocessing.Condition
            Conditional variable for accessing to msgs.

        Returns
        -------
        Constructed Preprocessor class.

        """
        self.raw = raw_msgs
        self.preprocessed = msgs
        self.cv_raw = cv_raw
        self.cv_msgs = cv_msgs
        self.__nlp = spacy.load("es_core_news_sm") 
        
    def __is_break_line_tag(self, html, pos):
        """
        Checks if the html tag causes a break line.
        
        Parameters
        ----------
        html: str
            HTML code.
        pos: int
            Position of the tag that we want to check.
            
        Returns
        -------
        bool: True if the tag causes a break line and false if it does not.
        
        """
        tag = ""
        while (html[pos] != ' ' and html):
            tag += html[pos]
            pos += 1
        return tag in TAGS_BREAKS_LINE 
        
    def __remove_soft_breaks(self, plain, html):
        """
        Removes soft break lines of the message body by comparing its
        representation as a plain text and as html
        
        Parameters
        ----------
        plain: str
            Message body as plain text.
        html: str
            Message body represented as html.
            
        Returns
        -------
        str: Message body as plain text without soft break lines.
        """
        cleaned_text = ""
        ind = html.find('>') + 1
        
        for c in plain:
            while (c != html[ind] and not c in BREAK_LINE):
                if html[ind] == '<':
                    ind = html.find('>', ind) + 1
                else:
                    ind += 1
                    
            while (c in BREAK_LINE and html[ind] == '<' and 
                   not self.__is_break_line_tag(html, ind + 1)):
                ind = html.find('>', ind) + 1
                    
            if (not c in BREAK_LINE):
                ind += 1
                cleaned_text += c
            elif (html[ind] == '<' and self.__is_break_line_tag(html, ind + 1)):
                cleaned_text += c
                ind = html.find('>', ind) + 1
        
    def __clean_decoded_text(self, text):
        """
        Removes soft break lines of the message body.

        Parameters
        ----------
        text: str
            Message body

        Returns
        -------
        str: Message body without soft break lines.
        """
        new_text = ""
        i = 0
        n = len(text)
        while i < n:
            if (text[i] == '\r' and (i + 1 < n) and text[i + 1] == '\n'):
                i += 2
                while((i + 1 < n) and text[i] == '\r' and text[i + 1] == '\n'):
                    new_text = new_text + text[i] + text[i + 1]
                    i += 2
            else:
                new_text += text[i]
                i += 1
    
        return new_text
        
    def star_preprocessing(self, user):
        if not os.path.exists(user + '/Extraction'):
            os.mkdir(user + '/Extraction')
        
        csv_columns = ['id', 'threadId', 'to', 'cc', 'bcc', 'from',
                       'depth', 'date', 'subject', 'bodyBase64Plain', 
                       'bodyBase64Html', 'plainEncoding', 'charLength']
        if not os.path.exists(user + '/Extraction/extracted.csv'):
            csvfile = open(user + '/Extraction/extracted.csv', 'w')
            writer = csv.DictWriter(csvfile, fieldnames = csv_columns)
            writer.writeheader()
        else:
            csvfile = open(user + '/Extraction/extracted.csv', 'a')
            writer = csv.DictWriter(csvfile, fieldnames = csv_columns)
        
        self.cv_raw.acquire()
        while (len(self.raw) == 0):
            self.cv_raw.wait()
        msg_raw = self.raw.pop()
        self.cv_raw.release()
        
        if 'bodyPlain' in msg_raw:
            msg_prep = {}
            if msg_raw['depth'] > 0:
                msg_prep['bodyPlain'] = EmailReplyParser.parse_reply(
                        msg_raw.pop('bodyPlain'))
                if 'bodyHtml' in msg_raw:
                    msg_prep['bodyPlain'] = self.__remove_soft_breaks(
                        msg_prep['bodyPlain'], msg_raw.pop('bodyHtml'))
            elif 'bodyHtml' in msg_raw:
                msg_prep['bodyPlain'] = self.__remove_soft_breaks(
                        msg_raw.pop('bodyPlain'), msg_raw.pop('bodyHtml'))
            elif ('plainEncoding' in msg_raw and 
                  msg_raw['plainEncoding'] == 'quoted-printable'):
                msg_prep['bodyPlain'] = self.__clean_decoded_text(
                        msg_raw.pop('bodyPlain'))
            else:
                msg_prep['bodyPlain'] = msg_raw.pop('bodyPlain')
            
            writer.writerow(msg_raw)
            msg_prep['bodyBase64Plain'] = base64.urlsafe_b64encode(
                msg_prep['bodyPlain'].encode()).decode()