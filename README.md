# ZipPop

*Pop out files off the end of a zip, truncating as we go*

### What, why

Say you want to download a 400gb zip file that contains around 450gb of data inside, so, you go to the store and get a 512gb stick to download it to. So, that is great, but now what? You need at least that amount of space to unzip the file, and driving back to the store, waiting on a delivery, or trying to find yet another utility that might do this are all more friction than reading about the zip file format.

So, what this script does, crudely, is extracts the *last* file in the zip file, then lops off the zip to just before that file, and then writes new indexes on the end to make the zip file work again. This is *way slower* as we're (currently) constantly rewriting the index so that you constantly have a valid zip file most of the time. 

### This code is awful

Yup! I think most of it isn't needed and is probably already written better in the standard library or someone else's projects, so, ideally, ditching a lot of this is the future direction.

### Doesn't something already do this

Not the current versions of the Linux command line utilities as far as I can tell. You can certainly delete arbitrary files but this requires at least the size of the entire zip to perform as it essentially does a complete copy. 

I do believe several utilities perhaps do this, Windows programs I'm sure, and it was very difficult to Google with the specifics of this slower, piecemeal operation being hard for search engines to allow you to specify. 

### Some more detail of the clockwork before I mess with it

Sure, here is the structure of a dummy zip file with three 1k files filled with zeros and compressed into one file.

```
   0 Local File Header
  69 one_kay_one (compressed)
  80 Local File Header
 149 one_kay_two (compressed)
 160 Local File Header
 231 one_kay_three (compressed)
 242 CDFH - one_kay_one
 323 CDFH - one_kay_two
 404 CDFH - one_kay_three
 487 EOCD
 509 (end)
```

This script does the following:
- Map all of the above out and start building out an in memory object structure of these pieces in an ad hoc way for observation and stats
- Extract the last file (using the built-in zipfile library)
- Truncate the file to the end of the next to the last file
- Rewrite all the directory stuff at the end (change addresses, entry counts)

The result is:

```
   0 Local File Header
  69 one_kay_one (compressed)
  80 Local File Header
 149 one_kay_two (compressed)
 160 CDFH - one_kay_one
 241 CDFH - one_kay_two
 322 EOCD
 344 (end)
```

This example is included in the tests/ directory.

### Neat, is it compatible

I used it on what I had around and a few others that I downloaded. I'm not following the spec and I am also relying on some assumptions of what I saw in the zip files on hand. I think I got 64-bit compatibility working. This was only tested on exfat, a ramdrive, and ext4, and I don't know if that matters. 

### Only the last file at a time is slow

I think doing something like this would allow you to shift files forward in turn, it would be a bit more to keep track of, but doing this now was not important for what I needed from this, and there could certainly be a buffering scheme for files under a few megabytes that would still be at less risk of a corrupted zip if interrupted but much quicker. 

### No way, not going to touch this

Yeah, no, please be warned, this program deletes data and can make a mess in a way that can't be cleaned up. Do not use it anywhere near anything you want to keep. Be careful, and be sure this is what you want to do.


