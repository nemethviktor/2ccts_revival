A note or two on translations:

The way translations work is that legacy stuff (non-English from the old releases that is) has been ported into the automation.
Python should, in theory pick up all new strings that are created and should, in theory add them to the non-English languages. 
Translations should automatically be retained. The reason I keep saying should is because this hasn't been overly tested but considering that only a new build can override any files, there's nothing to lose! :D

Basically if you want to translate, grab one of the CSV files (they are UTF-coded, even the simple ones) and just update the text in there. Python will take care of the rest.

One thing is, please don't use "(" and ")" characters, use "[" and "]" - this is because the way suffixes (e.g. "25kV AC") are being added removes any parentheses from the existing texts, this a feature, not a bug. 

If you want to start a new language, duplicate an existing CSV file most likely. You should _not_ ever need to edit the lng files themselves, they will be overwritten automatically.