#!/usr/bin/env python3
 
###################################################################
# mobilize - transfer music to your portable player
# (c) Copyright - 2014 Geoff Clements
#
# Transfers music to your portable player converting flacs to 
# ogg or mp3 on the way and excluding unwanted music.
#
# Requirements:
# - Python (version 3.3 or above)
# - sox
# - ogg tools
# - lame
# - flac
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
# 
import sys
import os
import shutil
import argparse
import subprocess as subp
import imghdr
# import xml.etree.ElementTree as et
import tempfile
# import multiprocessing as mp
import unicodedata as uncd
# 
AUDIOTYPES = ('flac', 'vorbis', 'mp3')
IMAGETYPES = ('jpeg', 'png')
# 
# def coroutine(f):
#     def _coroutine(*args, **kwargs):
#         cr = f(*args, **kwargs)
#         cr.__next__()
#         return cr
#     return _coroutine
# 
# def pretty(media):
#     retstr = ''
#     for tag in ('Artist', 'Album', 'Title'):
#         try:
#             try:
#                 retstr += media.origtags[tag] + '/'
#             except KeyError:
#                 try:
#                     retstr += media.origtags[tag.upper()] + '/'
#                 except KeyError:
#                     retstr += os.path.basename(media.spath)
#                     break
#         except AttributeError:
#             return os.path.basename(media.spath)
#     return retstr.rstrip('/')
# 
# class ActionBase(object):
#     def __init__(self, media):
#         self.media = media
#         
# class ActionOgg(ActionBase):
#     def __call__(self):
#         if userargs.verbose: print('Converting {} to ogg'.format(pretty(self.media)))
#         if not userargs.dry_run:
#             procstr = ['oggenc', '--quiet']
#             procstr.extend(('-q', '{0:.3f}'.format(userargs.quality)))
#             procstr.extend(('-o', os.path.splitext(self.media.dpath)[0] + '.ogg'))
#             procstr.append(self.media.spath)
#             subp.call(procstr)
# 
# class ActionMp3(ActionBase):
#     def __call__(self):
#         if userargs.verbose: print('Converting {} to mp3'.format(pretty(self.media)))
#         if not userargs.dry_run:
#             procstr = ['lame', '--quiet', '--add-id3v2']
#             procstr.extend(('-V', '{0:d}'.format(userargs.quality)))
#             for tag in self.media.origtags.items():
#                 if tag[0].upper() == 'TITLE':
#                     procstr.extend(('--tt', tag[1]))
#                 elif tag[0].upper() == 'ARTIST':
#                     procstr.extend(('--ta', tag[1]))
#                 elif tag[0].upper() == 'ALBUM':
#                     procstr.extend(('--tl', tag[1]))
#                 elif tag[0].upper() == 'YEAR':
#                     procstr.extend(('--ty', tag[1]))
#                 elif tag[0].upper() == 'DATE':
#                     procstr.extend(('--ty', tag[1]))
#                 elif tag[0].upper() == 'COMMENT':
#                     procstr.extend(('--tc', tag[1]))
#                 elif tag[0].upper() == 'TRACKNUMBER':
#                     procstr.extend(('--tn', tag[1]))
#                 elif tag[0].upper() == 'GENRE':
#                     procstr.extend(('--tg', tag[1]))
#             procstr.append('-')
#             procstr.append(os.path.splitext(self.media.dpath)[0] + '.mp3')
#             decproc = subp.Popen(['flac', '-c', '-d', self.media.spath], 
#                                                     stdout=subp.PIPE, stderr=subp.DEVNULL)
#             encproc = subp.Popen(procstr, stdin=decproc.stdout, stderr=subp.DEVNULL)
#             decproc.stdout.close()
#             encproc.wait()
# 
# class ActionCopy(ActionBase):
#     def __call__(self):
#         if userargs.verbose: print('Copying {}'.format(pretty(self.media)))
#         if not userargs.dry_run:
#             shutil.copy(self.media.spath, self.media.dpath)
# 
# class Action(object):
#     def __new__(cls, media):
#         if media.stype == 'flac':
#             if userargs.preferred == 'ogg':
#                 return ActionOgg(media)
#             elif userargs.preferred == 'mp3':
#                 return ActionMp3(media)
#         else:
#             return ActionCopy(media)
#         
# @coroutine
# def do_action():
#     try:
#         while True:
#             action = (yield)
#             pool.apply_async(action)
#     except GeneratorExit:
#         pass
# 
# @coroutine
# def set_action(target):
#     try:
#         while True:
#             media = (yield)
#             action = Action(media)
#             target.send(action)
#     except GeneratorExit:
#         target.close()
# 
# @coroutine
# def user_filter(target):
#     global userargs
#     userargs.exclist = []
#     userargs.inclist = []
#     
#     def process_ex(root, tagslist=None, applist=None):
#         if tagslist is None:
#             tagslist = []
#         if applist is None:
#             applist = userargs.exclist
#             
#         if root.tag == 'exclude':
#             for child in root.getchildren():
#                 process_ex(child, tagslist[:], userargs.exclist)
#         elif root.tag == 'include':
#             for child in root.getchildren():
#                 process_ex(child, tagslist[:], userargs.inclist)
#         else:
#             if root.getchildren():
#                 try:
#                     tagslist.append((root.tag, root.attrib['name']))
#                 except:
#                     print('Exclude error in tag {}'.format(root.tag))
# 
#                 for child in root.getchildren():
#                     process_ex(child, tagslist[:], applist)
#             else:
#                 tagslist.append((root.tag, root.text))
#                 applist.append(TagSet(tagslist))
#     
#     if userargs.exclude:
#         try:
#             excroot = et.parse(userargs.exclude).getroot()
#         except Exception as e:
#             print('Error in {}: {}'.format(userargs.exclude.name, e))
#         else:
#             process_ex(excroot)
#         
#     try:
#         while True:
#             media = (yield)
#             isfilter = False
#             if media.stype in AUDIOTYPES:
#                 if media.inlist(userargs.exclist):
#                     if not media.inlist(userargs.inclist):
#                         isfilter = True
#             elif media.stype not in IMAGETYPES:
#                 isfilter = True
#             if not isfilter:
#                 target.send(media)
#             else:
#                 if userargs.verbose: print('Excluding {}'.format(pretty(media)))
#     except GeneratorExit:
#         target.close()
# 
class TagSet(set):
    def __init__(self, taglist):
        newtags = []
        for tag in taglist:
            tagn = tag[0].upper()
            tagv = tag[1].upper()
            newtags.append((tagn, tagv))
            if tagn == 'YEAR':
                newtags.append(('DATE', tagv))
            elif tagn == 'DATE':
                newtags.append(('YEAR', tagv))
        super().__init__(newtags)
             
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
            self.tags = TagSet(splittags)
            self.origtags = {k:v for (k,v) in splittags}
             
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
                 
# def mediacopy(spath, dpath):
#     global pipeline
#     pipeline.send(Media(spath, dpath))
# 
# def mobilize():
#     if not os.path.exists(userargs.output):
#         print('Destination {} does not exist'.format(userargs.output))
#         sys.exit(1)
#     else:
#         if not os.path.isdir(userargs.output):
#             print('Destination {} is not a directory'.format(userargs.output))
#             sys.exit(1)
#     
#     for srcpath in userargs.src:
#         if os.path.isdir(srcpath):
#             dname = os.path.basename(srcpath.rstrip('/'))
#             dname = ''.join([c for c in uncd.normalize('NFKC', dname) if c.isalpha() or c.isdigit() or c==' ']).rstrip()
#             dstpath = os.path.join(userargs.output, dname)
#             if os.path.isdir(dstpath):
#                 if not userargs.dry_run:
#                     shutil.rmtree(dstpath)
#             if userargs.dry_run:
#                 dsttmp = tempfile.TemporaryDirectory(prefix='mobilize_')
#                 dstpath = os.path.join(dsttmp.name, os.path.basename(srcpath.rstrip('/')))
# 
#             shutil.copytree(srcpath, dstpath, 
#                                             ignore=shutil.ignore_patterns('.*'), 
#                                             copy_function=mediacopy)
# 
# def prune():
#     for srcpath in userargs.src:
#         top = os.path.join(userargs.output, os.path.basename(srcpath.rstrip('/')))
#         if os.path.isdir(top):
#             for root, dirs, files in os.walk(top, topdown=False):
#                 isaudio = False
#                 for fname in files:# #!/usr/bin/env python3
# 
#                     ftype = getfiletype(os.path.join(root, fname))
#                     if ftype in AUDIOTYPES:
#                         isaudio = True
#                         break
#                 if not (isaudio or dirs):
#                     shutil.rmtree(root, ignore_errors=True)
#             if not os.listdir(top):
#                 shutil.rmtree(root, ignore_errors=True)
# 
# if __name__ == '__main__':
#     doparser()
#     dochecks()
#     pipeline = user_filter(set_action(do_action()))
#     print('Mobilizing your music...')
#     pool = mp.Pool(mp.cpu_count() * 2)
#     mobilize()
#     pool.close()
#     pool.join()
#     pipeline.close()
#     if not userargs.dry_run: prune()
#     print('Your music has been mobilized!')

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
    parser.add_argument('--version', action='version', version='%(prog)s 0.11')
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
                for src_file_name in src_file_names:
                    dst_path_ext = src_dir_path.replace(srcpath, '')
                    dst_path_exts = dst_path_ext.split(os.sep)
                    dst_path_ext = os.path.join(*([norm(p) for p in dst_path_exts]))
                    dst_file_path = os.path.join(dst_dir_path, dst_path_ext, src_file_name)
                    src_media = Media(os.path.join(src_dir_path, src_file_name), dst_file_path)
                    if src_media.stype in AUDIOTYPES:
                        pass
                    elif src_media.stype in IMAGETYPES: 
                        pass
             
if __name__ == '__main__':
    userargs = doparser()
    dochecks()
    mobilize()
    
