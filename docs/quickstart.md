# Projects

We call projects all things we want to synchronize:
- notes
- music
- my code source of my gym android application
- contacts in vcf files
- etc...

To add project1, run :

```bash
> echogit projects add project1
```

if it contains large files, like movies, then you may want to use git lfs (large file system)

```bash
> echogit projects add project1 -o lfs
```

You can sync this project:

```bash
> echogit projects sync project1
```

# Manage peers

To list all peers

```bash
> echogit peers list
```

to add a new peer "mylaptop", you have to add file ~/.config/echogit/peers/mylaptop.conf
You then have to add list of projects to synchronize:

for example, if you want to synchronize all projects belonging to toto, and only project1 of titi user, you should have:

```bash
> cat ~/.config/echogit/peers/mylaptop.conf
> toto
> titi:/project1
```

To remove a peer, just remove the file.


# echogit usage

If you have projects, and peers, to synchronize you can run

```bash
> echogit sync
```

and to see status and error/conflict (if any)

```bash
> echogit status
```

in both case you can sync/status only for specific user or/and project
