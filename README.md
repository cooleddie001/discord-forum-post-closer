This bot, when people with the "Manage Posts" permission on discord run the /resolve command, will also close the post, apply the DONE tag, and rename the post to "[DONE {name}} {original title}"
Comes with an inactivity timer, "/resolve_timer {time}" which will auto resolve the post after time has passed if there is no other activity.
"/set_tag {tag}", which is required to run the other commands and will put {tag} next to every post you resolve.

Made for the pixmap.fun discord server but was scrapped for a more sophisicated solution, but may be resumed in the future if this is needed.
This can be used for any discord server that uses public forum posts as a form of reports.

Simple requirements to run:
- A "DONE" tag on the forum
- A "token.txt" file in the same directory with the raw discord bot token
- A "tags.json" file, also in the same directory
- discord-py installed.

I don't plan on updating this unless someone is actually using this, if you are and want something added just dm me on discord(@cooleddie001) and i can get that added for you.
