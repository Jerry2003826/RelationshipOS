from relationship_os.application.runtime.friend_chat_social_queries import (
    DEFAULT_SOCIAL_QUERY_NOISE_TOKENS,
    build_friend_chat_social_queries,
)


def test_build_friend_chat_social_queries_strips_noise_tokens() -> None:
    queries = build_friend_chat_social_queries(
        "\u4f60\u662f\u4e0d\u662f\u77e5\u9053\u4e00\u70b9\u6708\u997c\u7684\u4e8b\uff1f\u8981\u8bf4\u5c31\u5c11\u8bf4\u4e00\u70b9\u3002",
        noise_tokens=DEFAULT_SOCIAL_QUERY_NOISE_TOKENS,
    )

    assert queries == ["\u6708\u997c"]
