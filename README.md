ENTags
======

Evernote tag utilities (alpha version).  Library and command line utility.

These rough tools do not come with any warranty or assurances of data integrity!
Know what you are getting doing, think twice, use carefully!

Requirements:
* Python (you may need to install readline)
* Spell checker requires aspell
* EN API library from http://dev.evernote.com/documentation/cloud/
* I have run on OSX and Linux.  It is very likely you can use on Windows with some tweaking.

Configuration:
1. copy ENTags_example.cfg to ENTags.cfg
2. Enter your credentials
3. It is highly recommended you work against the sandbox environment first to
understand how ENTags can help (and hurt!)
4. Edit the run_cnote and run_tests scripts to point to your EN library installation
5. Optiopnal run ./run_tests -- this will create and delete new tags as it runs
6. run ./run_cnote -- this strats the ENTags shell environment


Notes:
* This is a tag manager, you cannot create or delete notes with this utility
* When you delete a tag, it is moved under then _trash_cnote_ tag. You can delete it
in the standard web or desktop client if you like
* spellCheck provide suggestions for tags not in the dictionary, you have to change the tag
names manually with renameTag
* Shell has history, just use the up and down arrows
* You can write the output of any command to a file by appending "> filename" to the command
* 2 and 3 letter commands are shortcuts for regular commands "rt = renameTag"
* Where applicable, commands can accept regular expressions. For example, to list 
tags starting with "Dog" use "^Dog", to list tags containing dog use "dog" (not including quotes)
* Use double quotes (only) for tags containing spaces e.g. "tag name"
* If you change anything through another interface while using cnote, use the sync command
to update cnote to the current state
* noteCounts without argument list takes a long time if you have many tags
* deleteTagCounts will remove ALL tags with note count less than argument, use this power wisely.

Examples
========

To get help:

```bash
ENTags> ./run_cnote 
Evernote Command Line structure manager. Version 1
en> help

Documented commands (type help <topic>):
========================================
createTag        dt             listTags   mt          renameTag   sync        
ct               dtc            ln         nc          rt          up          
deleteTag        exit           lt         noteCounts  sc          updateParent
deleteTagsCount  listNotebooks  mergeTags  quit        spellCheck

Miscellaneous help topics:
==========================
quotes  file

Undocumented commands:
======================
help

en>
```

For any specific command, use:

```bash
en> help deleteTagsCount
deleteTagsCount (dtc) - deletes tags with note count less than the argument
en> 
```

listNotebooks:

```bash
en> ln

(results: 12)
  General Notebook
  Strategy Games & Decisions
  Computers & Mathematics
  Gnip
  Project Resources
  Recipes & Cooking
  Books
  Data & Visualization
  Business
  Astronomy
  @ToRead
  Physics Chemistry & Biology
```

listTags (no arguments lists all of your tags):

```bash
en> lt loc

(results: 6)
block printing
clock
local
location
location_aware_displays
locative art

en> lt ^loc

(results: 4)
local
location
location_aware_displays
locative art
```

updateParent:

```bash
en> up "locative art" art

Tag: locative art successfully updated with parent: art

en> up "James Fallows" people

Tag: James Fallows successfully updated with parent: people


```

create and delete tags:

```bash
en> ct "delete me"

Creating tag: delete me 

en> dt "delete me"

delete me: Deleted

```

Count notes tagged with a specific tag (empty tag list processes all tags--WARNING, 
this may take long time!):

```bash
en> nc networks

networks ......................   44

en> nc networks people

networks ......................   44
people ........................    1

```

Merge tags (update all notes with tag "doggies" to have tag "dogs", delete "doggies", both tags must exist.)

```bash
en> mt teleconferencing "video conferencing"

Updating teleconferencing --> video conferencing in 3 notes...
  updated: "Glowpoint - Telepresence | Video Conferencing | Managed Video Services"
  updated: "Avistar Provides Virtualized Desktop Videoconferencing and Multiparty ... - Techzone360"
  updated: "HD Telepresence, Video Conferencing Solutions - Vu TelePresence"

```

Delete tags with fewer than n notes (n required; empty tag list processes all tags,
will not delete tags with children):

```bash
en> dtc 2 yeti

Deleting tags with fewer than 2 notes (this may take time)...
yeti deleted (1 notes)

```


LICENSE
=======
This work is licensed under the Creative Commons Attribution 3.0 Unported License. To view a copy 
of this license, visit http://creativecommons.org/licenses/by/3.0/.
