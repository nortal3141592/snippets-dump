# How am i gonna create a note?
so i'm gonna ask the user for three things - 
1. heading -> string
2. body -> string
3. tags -> list of strings

now regarding the tags - 
i'll check which input_tags are already in my database for the current user using this piece of code-

```python 3.12.13
input_tags = [t.lower() for t in note_data.tags]

result = await db.execute(
    select(models.Tag).where(
        models.Tag.user_id == current_user.id,
        models.Tag.tagname.in_(input_tags)
    )
)

existing_tags = result.scalars().all() -> this is a list of Tag objects
```

so for these existing_tags -> i don't need to add them in my 'Tag' table

then i'll also need to add in the missing tags in my database table of 'Tag' using this piece of code - 

```python 3.12.13
existing_tag_names = {tag.tagname for tag in existing_tags}
missing_tag_names = list(set(input_tags) - existing_tag_names)

missing_tags = []
for tag_name in missing_tag_names:
    new_tag = models.Tag(
        tagname = tag_name,
        user_id = current_user.id,
        author = current_user
    )

    missing_tags.append(new_tag)
    db.add(new_tag)

await db.flush()
```

after i've updated my 'tags' table with these missing tags i can then go and create my notes and then add all of these tags to my notes using this piece of code - 

```python
all_tags = missing_tags + list(existing_tags) # this is a list of Tag objects

new_note = models.Note(
    heading = note_data.heading,
    body = note_data.body,
    user_id = current_user.id,
    author = current_user,
)

new_note.tags = all_tags

db.add(new_note)

await db.commit()
await db.refresh(new_note)
```

and this new_note.tags = all_tags will  also update all the tags in the all_tags that they are associated with the new_note
