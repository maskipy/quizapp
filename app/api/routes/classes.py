"""
Class routes: a teacher's groups of students, joined with a short code.

Visibility rules (same philosophy as decks):
- not your class (neither its teacher nor a member) -> 404, so ids can't be probed;
- your class, but not your permission (a student calling a teacher action) -> 403.
"""

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from app.api.deps import CurrentUser, TeacherUser, get_owned_deck
from app.db.session import SessionDep
from app.models.classroom import (
    ClassDeck,
    ClassMembership,
    Classroom,
    ClassroomCreate,
    ClassroomPublic,
    JoinRequest,
    MemberPage,
    MemberPublic,
    SharedDeckPage,
    SharedDeckPublic,
    normalize_join_code,
)
from app.models.deck import Card, Deck
from app.models.user import User

router = APIRouter(prefix="/classes", tags=["classes"])


def _public(classroom: Classroom, member_count: int, viewer_id: int) -> ClassroomPublic:
    is_owner = classroom.teacher_id == viewer_id
    return ClassroomPublic(
        id=classroom.id,
        name=classroom.name,
        teacher_id=classroom.teacher_id,
        created_at=classroom.created_at,
        is_owner=is_owner,
        join_code=classroom.join_code if is_owner else None,
        member_count=member_count,
    )


async def _member_count(session: AsyncSession, class_id: int) -> int:
    query = select(func.count()).select_from(ClassMembership)
    return (await session.exec(query.where(ClassMembership.class_id == class_id))).one()


async def _get_visible_class(class_id: int, viewer_id: int, session: AsyncSession) -> Classroom:
    classroom = await session.get(Classroom, class_id)
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    if classroom.teacher_id != viewer_id:
        membership = await session.get(ClassMembership, (class_id, viewer_id))
        if membership is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Class not found")
    return classroom


async def _get_owned_class(class_id: int, viewer_id: int, session: AsyncSession) -> Classroom:
    classroom = await _get_visible_class(class_id, viewer_id, session)
    if classroom.teacher_id != viewer_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Only the class teacher can do that"
        )
    return classroom


@router.post("", response_model=ClassroomPublic, status_code=status.HTTP_201_CREATED)
async def create_class(
    class_in: ClassroomCreate, teacher: TeacherUser, session: SessionDep
) -> ClassroomPublic:
    classroom = Classroom(name=class_in.name, teacher_id=teacher.id)
    session.add(classroom)
    await session.commit()
    await session.refresh(classroom)
    return _public(classroom, 0, teacher.id)


@router.get("", response_model=list[ClassroomPublic])
async def list_my_classes(current_user: CurrentUser, session: SessionDep) -> list[ClassroomPublic]:
    """Classes you teach plus classes you joined, newest first. One query, and the member
    count is a correlated subquery, so it is computed only for the rows returned. (A
    grouped subquery would count every membership in the database on each request: at
    100,000 memberships that measured 10x slower.) Not paginated: a person is in a
    handful of classes."""
    member_count = (
        select(func.count())
        .select_from(ClassMembership)
        .where(ClassMembership.class_id == Classroom.id)
        .correlate(Classroom)
        .scalar_subquery()
    )
    joined = select(ClassMembership.class_id).where(ClassMembership.user_id == current_user.id)
    rows = (
        await session.exec(
            select(Classroom, member_count)
            .where(or_(Classroom.teacher_id == current_user.id, Classroom.id.in_(joined)))
            .order_by(Classroom.created_at.desc(), Classroom.id.desc())
        )
    ).all()
    return [_public(classroom, count, current_user.id) for classroom, count in rows]


@router.post("/join", response_model=ClassroomPublic)
async def join_class(
    body: JoinRequest, current_user: CurrentUser, session: SessionDep
) -> ClassroomPublic:
    user_id = current_user.id  # read now: a rollback below expires every loaded object
    code = normalize_join_code(body.join_code)
    classroom = (await session.exec(select(Classroom).where(Classroom.join_code == code))).first()
    if classroom is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid join code")
    if classroom.teacher_id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="You are the teacher of this class"
        )

    class_id = classroom.id
    if await session.get(ClassMembership, (class_id, user_id)) is None:
        session.add(ClassMembership(class_id=class_id, user_id=user_id))
        try:
            await session.commit()
        except IntegrityError:
            # A double tap: another request enrolled this student a moment ago. The end
            # state is the one we wanted, so this is a success, not an error.
            await session.rollback()
    classroom = await session.get(Classroom, class_id)  # reload: may have been expired
    return _public(classroom, await _member_count(session, class_id), user_id)


@router.get("/{class_id}", response_model=ClassroomPublic)
async def get_class(
    class_id: int, current_user: CurrentUser, session: SessionDep
) -> ClassroomPublic:
    classroom = await _get_visible_class(class_id, current_user.id, session)
    return _public(classroom, await _member_count(session, class_id), current_user.id)


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_class(class_id: int, current_user: CurrentUser, session: SessionDep) -> None:
    classroom = await _get_owned_class(class_id, current_user.id, session)
    await session.delete(classroom)  # the database cascades to the membership rows
    await session.commit()


@router.post("/{class_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def leave_class(class_id: int, current_user: CurrentUser, session: SessionDep) -> None:
    classroom = await _get_visible_class(class_id, current_user.id, session)
    if classroom.teacher_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The teacher can't leave their own class; delete it instead",
        )
    membership = await session.get(ClassMembership, (class_id, current_user.id))
    await session.delete(membership)
    await session.commit()


@router.get("/{class_id}/members", response_model=MemberPage)
async def list_members(
    class_id: int,
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(100, ge=1, le=200),
    offset: int = Query(0, ge=0),
) -> MemberPage:
    await _get_owned_class(class_id, current_user.id, session)
    total = await _member_count(session, class_id)
    rows = (
        await session.exec(
            select(User, ClassMembership.joined_at)
            .join(ClassMembership, ClassMembership.user_id == User.id)
            .where(ClassMembership.class_id == class_id)
            .order_by(ClassMembership.joined_at, User.id)
            .offset(offset)
            .limit(limit)
        )
    ).all()
    items = [
        MemberPublic(id=user.id, email=user.email, full_name=user.full_name, joined_at=joined_at)
        for user, joined_at in rows
    ]
    return MemberPage(items=items, total=total, limit=limit, offset=offset)


@router.delete("/{class_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_member(
    class_id: int, user_id: int, current_user: CurrentUser, session: SessionDep
) -> None:
    await _get_owned_class(class_id, current_user.id, session)
    membership = await session.get(ClassMembership, (class_id, user_id))
    if membership is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Member not found")
    await session.delete(membership)
    await session.commit()


@router.get("/{class_id}/decks", response_model=SharedDeckPage)
async def list_shared_decks(
    class_id: int,
    current_user: CurrentUser,
    session: SessionDep,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
) -> SharedDeckPage:
    """Decks shared with this class. Visible to its teacher and its members."""
    await _get_visible_class(class_id, current_user.id, session)
    total = (
        await session.exec(
            select(func.count()).select_from(ClassDeck).where(ClassDeck.class_id == class_id)
        )
    ).one()
    card_count = (
        select(func.count())
        .select_from(Card)
        .where(Card.deck_id == Deck.id)
        .correlate(Deck)
        .scalar_subquery()
    )
    rows = (
        await session.exec(
            select(Deck, ClassDeck.shared_at, card_count)
            .join(ClassDeck, ClassDeck.deck_id == Deck.id)
            .where(ClassDeck.class_id == class_id)
            .order_by(ClassDeck.shared_at.desc(), Deck.id.desc())
            .offset(offset)
            .limit(limit)
        )
    ).all()
    items = [
        SharedDeckPublic(
            id=deck.id,
            title=deck.title,
            description=deck.description,
            owner_id=deck.owner_id,
            created_at=deck.created_at,
            shared_at=shared_at,
            card_count=count,
        )
        for deck, shared_at, count in rows
    ]
    return SharedDeckPage(items=items, total=total, limit=limit, offset=offset)


@router.put("/{class_id}/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def share_deck(
    class_id: int, deck_id: int, current_user: CurrentUser, session: SessionDep
) -> None:
    """Share one of YOUR decks with one of YOUR classes. Idempotent: sharing twice is fine."""
    await _get_owned_class(class_id, current_user.id, session)
    await get_owned_deck(deck_id, current_user, session)
    if await session.get(ClassDeck, (class_id, deck_id)) is None:
        session.add(ClassDeck(class_id=class_id, deck_id=deck_id))
        try:
            await session.commit()
        except IntegrityError:
            # Two taps at once: the other request already shared it. Same end state.
            await session.rollback()


@router.delete("/{class_id}/decks/{deck_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_deck(
    class_id: int, deck_id: int, current_user: CurrentUser, session: SessionDep
) -> None:
    await _get_owned_class(class_id, current_user.id, session)
    share = await session.get(ClassDeck, (class_id, deck_id))
    if share is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Deck is not shared with this class"
        )
    await session.delete(share)
    await session.commit()
