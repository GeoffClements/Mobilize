# Mobilize
You have all your music on your PC or a NAS device and you want to put it on a mobile device, ok no problem just copy the directory tree. BUT ... you have a mixture of flacs, oggs and mp3s, you'd like to convert the flacs to either oggs or mp3 to save space and, just to make things even harder, you don't want all the music; your significant other's U2 collection is definitely out and as for Coldplay, well ...

That's where mobilze comes to help, with one command you can do the above, just download mobilize.py from [GitHub](https://github.com/GeoffClements/Mobilize Mobilize at GitHub). 

Mobilize has some dependences:
  * Python 3.3 or above
  * [Sox](http://sox.sourceforge.net/) for reading music tags and converting file types. Sox will have dependencies of its own such as lame, vorbis and flac.
  * python3-ply
  
To run mobilize and see the options type `mobilze -h`, you should see this:
```
usage: mobilize [-h] [-p {ogg,mp3}] [-q QUALITY] [-x <exclude file>] [-d] [-v]
          -o <output directory> [--version]
          src [src ...]
          
Send audio files to a mobile device
positional arguments:src Source root directory
optional arguments: -h, --help show this help message and exit
                    -p {ogg,mp3}, --preferred {ogg,mp3}
                       Preferred encoding for flac files, default is ogg
                    -q QUALITY, --quality QUALITY
                       Quality setting for encoder, default = 6.0
                     -x <exclude file>, --exclude <exclude file>
                       Path to file holding exclusion rules
                     -d, --dry-run
                       Don't change anything, implies the --verbose setting
                     -v, --verbose
                       Show what is being done
                     -o <output directory>, --output <output directory>
                       Destination root directory
                     --version
                       show program's version number and exit
                       
Copy audio files from one tree to another. When copying, files can be excluded
based on their audio tags. Also flac files are auto-converted to either ogg or
mp3.
```

Hopefully this is all self-explanatory but the following will explain some of the more mysterious aspects.

## src and output directories
Mobilize is all about copying directory trees, not individual files hence both src and output designations should be pre-existing directories. The intention is that the output directory is on a mobile device but it can be anywhere on your accessible file systems. More than one src directory can be specified and file globbing can be used. All directories specified as a src *will have their contents copied under* the output directory.

## Quality setting
The quality setting is passed directly to the encoder whether it be oggenc or lame. The default value of 6.0 is ideal for oggenc but not so good for lame where a lower number may be better. A floating point number is used for oggenc but if lame is used then this number is rounded to the nearest integer.

## Exclude Files
The exclude file allows you to exclude some music and comparisons are made with the tags in the music files. The format of the file is simple text and a basic file will look like this:

```
exclude (
)
```

This will exclude nothing but forms the basis of the exclude file. Now lets exclude all U2 music:
```
exclude (
	artist is "U2"
)
```

This matches the artist tag with that found in the music file and does not copy the file. Now some more music we don't want, in this case I don't want Bob Dylan but he appears as the artist in Bob Dylan albums and also on "Bob Dylan and the Band". In this case I can use the word "has" instead of "is" to ask mobilize to search for a string contained in the tag: 
```
exclude (
	artist is "U2"
	artist has "Bob Dylan"
)
```

Finally here's an excerpt from my own file to show you some of the options:
```
exclude (
  artist has "Bob Dylan"
  artist is "Belle And Sebastian"
  artist is "Beth Orton"
  artist is "Dido"
  artist is "Dire Straits"
  artist is "Elbow"
  artist is "Lou Reed"
  artist has "Garfunkel"
  artist is "The Clash"
  artist is "U2"
  artist is "Al Stewart"
  artist is "Van Morrison"
  artist is "Elbow"
  genre has "Christmas"
  genre is "Easy Listening"
  album has "Pop Party"
  artist is "Uriah Heep"(
    year between "1977" and "1980"
  )
  artist is "Pink Floyd" (
    album is "Works"
    album is "The Early Pink Floyd Singles"
    album is "Masters of Rock"
    album is "Relics"
    album has "Ummagumma"
    album has "A Saucerful Of Secrets"
    album is "The Piper At The Gates Of Dawn"
  )
  artist is "Sweet" (
    album is "First Recordings 1968-1971"
    album is "The Best Of Sweet"
    album is "Poppa Joe"
  )
)
```

Both the tags themselves and the values of the tags are matched using a case insensitive rule. The following tags can be used to create match rules in the exclude file:

  * artist
  * album
  * year
  * date
  * genre
  * comment

Date and year are treated as the same tag.