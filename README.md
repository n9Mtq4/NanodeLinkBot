# NanodeLinkBot

#### About
This bot will track the subreddits r/nanotrade and r/nanocurrency
and search for nano addresses or nano block hashes. It will then
reply to the post or comment with the corresponding link to nanode.
This is to help mobile users and people who just don't want to open
up another tab to nanode to search an address or find a block. It
will not comment if you include any block explorer link along with
your address or block hash. It is also open source.

#### Installing and Running
1. Install python3 and [praw](https://praw.readthedocs.io/en/latest/getting_started/installation.html).
2. Install the package `moreutils` for your distro.
3. Create a [praw.ini](https://praw.readthedocs.io/en/latest/getting_started/configuration/prawini.html#defining-additional-sites) file, with the botname `nanodelinkbot`.
4. Create a file called `replied_posts.txt`.
5. Change `ALLOW_POSTS` in `nanodelinkbot.py:20` to `True` to allow actually posting to reddit.
6. Excecute script `runs.sh` to monitor submissions or `runc.sh` for comments.

