#!/usr/bin/env python3
 
###################################################################
# mobilize - transfer music to your portable player
# (c) Copyright - 2015 Geoff Clements
#
# Transfers music to your portable player converting flacs to 
# ogg or mp3 on the way and excluding unwanted music.
#
# Requirements:
# - Python (version 3.3 or above)
# - sox
# - python3-ply
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# version 2 as published by the Free Software Foundation.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA
# 02110-1301, USA.
###################################################################

import sys
import os
import shutil
import argparse
import subprocess as subp
import imghdr
import tempfile
import multiprocessing as mp
import unicodedata as uncd
 
AUDIOTYPES = ('flac', 'vorbis', 'mp3')
IMAGETYPES = ('jpeg', 'png')
 
def coroutine(f):
    def _coroutine(*args, **kwargs):
        cr = f(*args, **kwargs)
        next(cr)
        return cr
    return _coroutine
 
def pretty(media):
    retstr = ''
    for tag in ('artist', 'album', 'title'):
        try:
            try:
                retstr += media.tags[tag] + '/'
            except KeyError:
                try:
                    retstr += media.tags[tag.upper()] + '/'
                except KeyError:
                    retstr += os.path.basename(media.spath)
                    break
        except AttributeError:
            return os.path.basename(media.spath)
    return retstr.rstrip('/')
 
class ActionBase(object):
    def __init__(self, media):
        self.media = media
        
    def mkdir(self):
        target_dir = os.path.dirname(self.media.dpath)
        if not os.path.isdir(target_dir):
            os.makedirs(target_dir, exist_ok=True)
         
class ActionConvert(ActionBase):
    def __call__(self):
        if userargs.verbose: print('Converting {} to {}'.format(pretty(self.media), userargs.preferred))
        if not userargs.dry_run:
            self.mkdir()
            procstr = ['sox', '-V0', self.media.spath]
            if self.media.bits > 16:
                procstr.extend(('--bits', '16'))
            if self.media.rate > 44100:
                procstr.extend(('--rate', '44100'))
            if userargs.preferred == 'ogg':
                quality = '{:.3}'.format(userargs.quality)
            else:
                quality = '-{:d}.2'.format(int(round(userargs.quality)))
            procstr.extend(('--compression', '{}'.format(quality)))
            procstr.append((os.path.splitext(self.media.dpath)[0] + '.' + userargs.preferred))
            subp.call(procstr)
 
class ActionCopy(ActionBase):
    def __call__(self):
        if self.media.stype in IMAGETYPES:
            if os.path.isdir(os.path.dirname(self.media.dpath)):
                self.print_action()
                shutil.copy(self.media.spath, self.media.dpath)
        else:
            self.print_action()
            if not userargs.dry_run:
                self.mkdir()
                shutil.copy(self.media.spath, self.media.dpath)
                
    def print_action(self):
        if userargs.verbose: print('Copying {}'.format(pretty(self.media)))
 
class Action(object):
    def __new__(cls, media):
        if media.stype == 'flac':
            return ActionConvert(media)
        else:
            return ActionCopy(media)
         
@coroutine
def do_action():
    try:
        while True:
            action = (yield)
            pool.apply_async(action)
            #action()
    except GeneratorExit:
        pass
 
@coroutine
def set_action(target):
    try:
        while True:
            media = (yield)
            action = Action(media)
            target.send(action)
    except GeneratorExit:
        target.close()
 
@coroutine
def user_filter(target):
    try:
        while True:
            media = (yield)
            if filterlist and media.stype in AUDIOTYPES:
                if not filterlist.compare(media.tags):
                    target.send(media)
                elif userargs.verbose:
                    print('Rejecting {}'.format(pretty(media)))
            else:
                target.send(media)
                
    except GeneratorExit:
        target.close()
 
class Media(object):
    def __init__(self, spath, dpath):
        self.spath = spath
        self.dpath = dpath
        self.stype = getfiletype(spath)
        if self.stype in AUDIOTYPES:
            tags = subp.check_output(['soxi', '-a', spath], 
                                    stderr=subp.DEVNULL, 
                                    universal_newlines=True).split('\n')
            splittags = [self.splitter(tag.split('=', 1)) for tag in tags if tag]
            self.tags = {k.lower():v for (k,v) in splittags}
            if 'date' in self.tags.keys():
                self.tags['year'] = self.tags['date']
            elif 'year' in self.tags.keys():
                self.tags['date'] = self.tags['year']
            self.rate = int(subp.check_output(['soxi', '-r', spath], stderr=subp.DEVNULL, 
                                          universal_newlines=True))
            self.bits = int(subp.check_output(['soxi', '-b', spath], stderr=subp.DEVNULL, 
                                          universal_newlines=True))
             
    def inlist(self, tagsetlist):
        isinlist = False
        for tagset in tagsetlist:
            if tagset <= self.tags:
                isinlist = True
                break
        return isinlist
 
    def splitter(self, tag):
        if len(tag) == 2:
            return tag
        else:
            return (tag[0], '')
                 
def doparser():
    parser = argparse.ArgumentParser(prog='mobilize', description="Send audio files to a mobile device")
    parser.epilog = """Copy audio files from one tree to another. 
    When copying, files can be excluded based on their audio tags. 
    Also flac files are auto-converted to either ogg or mp3.
    """
    parser.add_argument('-p', '--preferred', choices=('ogg', 'mp3'), default='ogg',
                                        help='Preferred encoding for flac files, default is ogg')
    parser.add_argument('-q', '--quality', type=float, default=6.0,
                                        help='Quality setting for encoder, default = 6.0')
    parser.add_argument('-x', '--exclude', type=argparse.FileType('r'),
                                        metavar='<exclude file>', help='Path to file holding exclusion rules')
    parser.add_argument('-d', '--dry-run', action='store_true',
                                        help='Don\'t change anything, implies the --verbose setting')
    parser.add_argument('-v', '--verbose', action='store_true',
                                        help='Show what is being done')
    parser.add_argument('-o', '--output', required=True,
                                            metavar='<output directory>', help='Destination root directory')
    parser.add_argument('--version', action='version', version='%(prog)s 1.0')
    parser.add_argument('src', nargs='+', help='Source root directory')

    args = parser.parse_args()

    if args.preferred == 'ogg':
        qualrange = (-1.0, 10.0)
    else:
        qualrange = (0, 9)
        args.quality = int(round(args.quality))
    if args.quality < qualrange[0]: args.quality = qualrange[0]    
    if args.quality > qualrange[1]: args.quality = qualrange[1]    

    args.verbose = args.verbose or args.dry_run
    return args
    
def dochecks():
    if not shutil.which('sox'):
        print('Cannot find sox')
        sys.exit(1)
        
    try:
        subp.check_output(('sox', '--help-format', userargs.preferred), 
                          stderr=subp.DEVNULL, 
                          universal_newlines=True)
    except subp.CalledProcessError as subperr:
        if 'Writes:' not in subperr.output:
            print('Sox cannot handle {}'.format(userargs.preferred))
            sys.exit(1)
 
def getfiletype(fname):
    try:
        ftype = subp.check_output(('soxi', '-t', fname), 
                stderr=subp.DEVNULL, 
                universal_newlines=True).rstrip('\n')
    except subp.CalledProcessError:
        try:
            ftype = imghdr.what(fname)
        except:
            ftype = None
     
    if ftype:
        return ftype.lower()
    else:
        return None
 
def mobilize():
    
    def norm(s):
        return ''.join([c for c in uncd.normalize('NFKC', s) if c.isalpha() or c.isdigit() or c==' ']).rstrip()
    
    if not os.path.exists(userargs.output):
        print('Destination {} does not exist'.format(userargs.output))
        sys.exit(1)
    else:
        if not os.path.isdir(userargs.output):
            print('Destination {} is not a directory'.format(userargs.output))
            sys.exit(1)
     
    for srcpath in userargs.src:
        if userargs.dry_run:
            dsttmp = tempfile.TemporaryDirectory(prefix='mobilize_')
            dst_dir_path = os.path.join(dsttmp.name, os.path.basename(srcpath.rstrip('/')))
        else:
            dst_dir_path = userargs.output
                
        if os.path.isdir(srcpath):
            for src_dir_path, _, src_file_names in os.walk(srcpath):
                image_files = []
                for src_file_name in src_file_names:
                    dst_path_ext = src_dir_path.replace(srcpath, '')
                    dst_path_exts = dst_path_ext.split(os.sep)
                    dst_path_ext = os.path.join(*([norm(p) for p in dst_path_exts]))
                    dst_file_path = os.path.join(dst_dir_path, dst_path_ext, src_file_name)
                    src_media = Media(os.path.join(src_dir_path, src_file_name), dst_file_path)
                    if src_media.stype in AUDIOTYPES:
                        pipeline.send(src_media)
                    elif src_media.stype in IMAGETYPES: 
                        image_files.append(src_media)
                for src_image in image_files:
                    pipeline.send(src_image)
             
if __name__ == '__main__':
    userargs = doparser()
    dochecks()
#===============================================================================
# Parsing of the exclude file starts here
# PLY requires us to do this at module level so it's in-line here
#===============================================================================
    if userargs.exclude:
        tokens = ('EXCLUDE', 'LPAREN', 'RPAREN', 'AUDIOTAG', 'IS', 
                  'HAS', 'STRING', 'BETWEEN', 'AND')
        
        t_EXCLUDE  = r'exclude'
        t_LPAREN   = r'\('
        t_RPAREN   = r'\)'
        t_AUDIOTAG = r'(album)|(artist)|(date)|(year)|(genre)|(comments?)'
        t_IS       = r'is'
        t_HAS      = r'has'
        t_BETWEEN  = r'between'
        t_AND      = r'and'
        
        def t_STRING(t):
            r'\"([^\\\n]|(\\.))*?\"'
            t.value = t.value.strip('"')
            return t
        
        t_ignore = ' \t'
        
        # Define a rule so we can track line numbers
        def t_newline(t):
            r'\n+'
            t.lexer.lineno += len(t.value)
        
        # Error handling rule
        def t_error(t):
            print("Illegal character '%s'" % t.value[0])
            t.lexer.skip(1)
        
        import ply.lex as lex
        lexer = lex.lex(debug=False)
        
        class TagCompare(object):
            def __init__(self, audiotag, op, value):
                self.audiotag = audiotag
                self.op = op
                self.value = value
                
            def compare(self, audiodata):
                try:
                    if self.op == 'is':
                        return self.value.lower() == audiodata[self.audiotag].lower()
                    elif self.op == 'has':
                        return self.value.lower() in audiodata[self.audiotag].lower()
                    elif self.op == 'between':
                        assert self.audiotag == 'year'
                        try:
                            values = [int(v) for v in self.value]
                            values.sort()
                            adate = int(audiodata['date'])
                        except ValueError:
                            return False
                        return values[0] <= adate <= values[1]
                except:
                    return False
            
        class TagCompareList(list):
            def __init__(self, initlist=(), op='OR', invert=False):
                super().__init__(initlist)
                self.op = op
                self.invert = invert
            
            def compare(self, audiodata):
                result = not self.op == 'OR'
                if result:
                    for item in self:
                        result = result and item.compare(audiodata)
                        if not result:
                            break
                else:
                    for item in self:
                        result = result or item.compare(audiodata)
                        if result:
                            break
                if self.invert:
                    result = not result
                return result
        
        '''
        exclude_list : EXCLUDE LPAREN expression_list RPAREN
        
        expression_list : expression_list expression
                        | expression
        
        expression : simple_expression
                   | compound_expression
        
        compound_expression : simple_expression LPAREN expression_list RPAREN
        
        simple_expression : AUDIOTAG IS STRING
                          | AUDIOTAG HAS STRING
                          | AUDIOTAG BETWEEN STRING AND STRING
        '''
        
        
        def p_exclude_list(p):
            'exclude_list : EXCLUDE LPAREN expression_list RPAREN'
            p[0] = TagCompareList(p[3])
        
        def p_expression_list(p):
            '''expression_list : expression_list expression
                               | expression'''
            expression_list = TagCompareList()
            if len(p) == 3:
                expression_list.extend((p[1], p[2]))
            else:
                expression_list.append(p[1])
            p[0] = expression_list
        
        def p_expression(p):
            '''expression : simple_expression
                          | compound_expression'''
            p[0] = p[1]
        
        def p_compound_expression(p):
            'compound_expression : expression LPAREN expression_list RPAREN'
            sub_list = TagCompareList(p[3])
            p[0] = TagCompareList((p[1], sub_list), op='AND')
        
        def p_simple_expression(p):
            '''simple_expression : AUDIOTAG IS STRING
                                 | AUDIOTAG HAS STRING
                                 | AUDIOTAG BETWEEN STRING AND STRING'''
            
            value = (p[3], p[5]) if len(p) == 6 else p[3]
            p[0] = TagCompare(p[1], p[2], value)
        
        # Error rule for syntax errors
        def p_error(p):
            print("Syntax error in input!")
        
        import ply.yacc as yacc
        parser = yacc.yacc(debug=False, write_tables=False)
        filterlist = parser.parse(userargs.exclude.read())
    else:
        filterlist = None
#===============================================================================
# End of exclude file parsing
#===============================================================================
    pipeline = user_filter(set_action(do_action()))
    print('Mobilizing your music...')
    pool = mp.Pool(mp.cpu_count() + 1)
    mobilize()
    pool.close()
    pool.join()
    pipeline.close()
    print('Your music has been mobilized!')
    