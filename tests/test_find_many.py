import pytest
from prisma import Client


@pytest.mark.asyncio
async def test_find_many(client: Client) -> None:
    """Filters and ordering work as suggested"""
    posts = [
        await client.post.create({'title': 'Test post 1', 'published': False}),
        await client.post.create({'title': 'Test post 2', 'published': False}),
    ]
    found = await client.post.find_many(where={'title': 'Test post 1'})
    assert len(found) == 1
    assert found[0].id == posts[0].id

    posts = await client.post.find_many(
        where={'OR': [{'title': 'Test post 1'}, {'title': 'Test post 2'}]}
    )
    assert len(posts) == 2

    posts = await client.post.find_many(where={'title': {'contains': 'Test post'}})
    assert len(posts) == 2

    posts = await client.post.find_many(where={'title': {'startswith': 'Test post'}})
    assert len(posts) == 2

    posts = await client.post.find_many(where={'title': {'not_in': ['Test post 1']}})
    assert len(posts) == 1
    assert posts[0].title == 'Test post 2'

    posts = await client.post.find_many(where={'title': {'equals': 'Test post 2'}})
    assert len(posts) == 1
    assert posts[0].title == 'Test post 2'

    posts = await client.post.find_many(where={'title': 'Test post 2'})
    assert len(posts) == 1
    assert posts[0].title == 'Test post 2'

    posts = await client.post.find_many(order={'title': 'desc'})
    assert len(posts) == 2
    assert posts[0].title == 'Test post 2'
    assert posts[1].title == 'Test post 1'

    posts = await client.post.find_many(order={'title': 'asc'})
    assert len(posts) == 2
    assert posts[0].title == 'Test post 1'
    assert posts[1].title == 'Test post 2'


@pytest.mark.asyncio
async def test_filtering_one_to_one_relation(client: Client) -> None:
    """Filtering by a 1-1 relational field and negating the filter"""
    async with client.batch_() as batcher:
        batcher.user.create(
            {'name': 'Robert', 'profile': {'create': {'bio': 'My very cool bio.'}}}
        )
        batcher.user.create(
            {
                'name': 'Tegan',
                'profile': {'create': {'bio': 'Hello world, this is my bio.'}},
            }
        )
        batcher.user.create({'name': 'Callum'})

    users = await client.user.find_many(
        where={'profile': {'is': {'bio': {'contains': 'cool'}}}}
    )
    assert len(users) == 1
    assert users[0].name == 'Robert'
    assert users[0].profile is None

    users = await client.user.find_many(
        where={'profile': {'is': {'bio': {'contains': 'bio'}}}}
    )
    assert len(users) == 2
    assert users[0].name == 'Robert'
    assert users[1].name == 'Tegan'

    users = await client.user.find_many(
        where={'profile': {'is_not': {'bio': {'contains': 'bio'}}}}
    )
    assert len(users) == 1
    assert users[0].name == 'Callum'


@pytest.mark.asyncio
async def test_filtering_one_to_many_relation(client: Client) -> None:
    """Filtering by a 1-M relational field and negating the filter"""
    async with client.batch_() as batcher:
        batcher.user.create(
            {
                'name': 'Robert',
                'posts': {
                    'create': [
                        {'title': 'My first post', 'published': True},
                        {'title': 'My second post', 'published': False},
                    ]
                },
            }
        )
        batcher.user.create(
            {
                'name': 'Tegan',
                'posts': {
                    'create': [
                        {'title': 'Hello, world!', 'published': True},
                        {'title': 'My test post', 'published': False},
                    ]
                },
            }
        )
        batcher.user.create({'name': 'Callum'})

    # I guess it makes sense that a record with no relations also matches this
    # TODO: this needs to be documented
    users = await client.user.find_many(
        where={'posts': {'every': {'title': {'contains': 'post'}}}},
    )
    assert len(users) == 2
    assert users[0].name == 'Robert'
    assert users[1].name == 'Callum'

    users = await client.user.find_many(
        where={'posts': {'some': {'title': {'contains': 'Post'}}}}
    )
    assert len(users) == 2
    assert users[0].name == 'Robert'
    assert users[1].name == 'Tegan'

    users = await client.user.find_many(
        where={'posts': {'none': {'title': {'contains': 'Post'}}}}
    )
    assert len(users) == 1
    assert users[0].name == 'Callum'

    users = await client.user.find_many(where={'posts': {'some': {'title': 'foo'}}})
    assert len(users) == 0
