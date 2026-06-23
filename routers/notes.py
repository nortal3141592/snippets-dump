# NOTES.PY

from typing import Annotated

from fastapi import APIRouter, HTTPException, status, Depends, Request

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload
from database import get_db
from auth import CurrentUser
import models
from models import note_tag

from schemas import NoteCreate, NoteResponse, NoteUpdate, TagCreate, TagResponse

from limiter import limiter

router = APIRouter()

@router.post("", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("30/minute")
async def create_note(request: Request, note_data: NoteCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    input_tags = [t.lower() for t in note_data.tags]

    result = await db.execute(
        select(models.Tag).where(
            models.Tag.user_id == current_user.id,
            models.Tag.tagname.in_(input_tags)
        )
    )

    existing_tags = result.scalars().all()

    existing_tag_names = {tag.tagname for tag in existing_tags}
    missing_tag_names = list(set(input_tags) - existing_tag_names)

    missing_tags = []

    for tag_name in missing_tag_names:
        new_tag = models.Tag(
            tagname = tag_name,
            user_id = current_user.id,
        )

        missing_tags.append(new_tag)
        db.add(new_tag)
    
    await db.flush()

    all_tags = missing_tags + list(existing_tags)

    new_note = models.Note(
        heading = note_data.heading,
        body = note_data.body,
        user_id = current_user.id,
    )

    new_note.tags = all_tags

    db.add(new_note)

    await db.commit()
    await db.refresh(new_note, attribute_names=["tags"])

    return new_note

@router.get("",response_model=list[NoteResponse])
@limiter.limit("120/minute")
async def get_all_notes(request: Request, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)], tag: str | None = None):
    if tag:
        result = await db.execute(
            select(models.Note).
            options(selectinload(models.Note.tags)).
            where(models.Note.user_id == current_user.id, models.Note.tags.any(models.Tag.tagname == tag.lower()))
        )
    else:
        result = await db.execute(
            select(models.Note).
            options(selectinload(models.Note.tags), selectinload(models.Note.author)).
            where(models.Note.user_id == current_user.id)
        )

    notes = result.scalars().all()

    return notes

@router.get("/{note_id}", response_model=NoteResponse)
async def get_note(note_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Note).
        options(selectinload(models.Note.tags), selectinload(models.Note.author)).
        where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )

    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Note not found or Invalid user access")

    return note



@router.patch("/{note_id}", response_model=NoteResponse)
async def update_note(note_id: int, note_data: NoteUpdate, current_user : CurrentUser, db:Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Note).
        options(selectinload(models.Note.tags), selectinload(models.Note.author)).
        where(models.Note.id == note_id, models.Note.user_id == current_user.id)
    )

    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    
    update_data = note_data.model_dump(exclude_unset=True)

    for field, data in update_data.items():
        setattr(note, field, data)
    
    await db.commit()
    await db.refresh(note, attribute_names=["author", "tags"])

    return note


@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
@limiter.limit("20/minute")
async def delete_note(request: Request, note_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):    
    result = await db.execute(
        select(models.Note).
        options(selectinload(models.Note.tags), selectinload(models.Note.author)).
        where(models.Note.user_id == current_user.id, models.Note.id == note_id)
    )

    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Note not found or invalid access to note")
    
    tags_to_check = list(note.tags)

    await db.delete(note)
    await db.flush()

    for tag in tags_to_check:
        result = await db.execute(
            select(func.count()).select_from(note_tag).where(note_tag.c.tag_id == tag.id)
        )

        count = result.scalar()

        if count == 0:
            await db.delete(tag)
    
    await db.commit()


@router.post("/{note_id}/tags", response_model = NoteResponse)
@limiter.limit("60/minute")
async def add_tag(request: Request, note_id:int, tag_data: TagCreate, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Note).
        options(selectinload(models.Note.tags), selectinload(models.Note.author)).
        where(models.Note.user_id == current_user.id, models.Note.id == note_id)
    )

    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Note not found or Invalid access to note")
    
    tag_name = tag_data.tagname.lower()

    result = await db.execute(
        select(models.Tag).
        where(models.Tag.user_id == current_user.id, models.Tag.tagname == tag_name)
    )

    tag = result.scalars().first()

    if not tag:
        tag = models.Tag(tagname=tag_name, user_id=current_user.id)
        db.add(tag)
        await db.flush()
    
    if tag in note.tags:
        raise HTTPException(status_code=400, detail="Tag already on note")

    note.tags.append(tag)

    await db.commit()

    await db.refresh(note, attribute_names=["tags"])

    return note

@router.delete("/{note_id}/tags/{tag_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_tag_from_note(note_id: int, tag_id: int, current_user: CurrentUser, db: Annotated[AsyncSession, Depends(get_db)]):
    result = await db.execute(
        select(models.Note).
        options(selectinload(models.Note.tags), selectinload(models.Note.author)).
        where(models.Note.user_id == current_user.id, models.Note.id == note_id)
    )

    note = result.scalars().first()

    if not note:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="note not found or invalid note access")
    
    result = await db.execute(
        select(models.Tag).
        where(models.Tag.user_id == current_user.id, models.Tag.id == tag_id)
    )

    tag = result.scalars().first()

    if not tag:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Tag not found or Invalid tag access")
    
    if tag not in note.tags:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag is not attached to this note")

    note.tags.remove(tag)

    await db.flush()

    result = await db.execute(
        select(func.count()).select_from(note_tag).where(note_tag.c.tag_id == tag.id)
    )

    count = result.scalar_one()

    if count == 0:
        await db.delete(tag)

    await db.commit()



